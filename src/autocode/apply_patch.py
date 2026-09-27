"""
apply_patch.py — parses unified diffs, applies atomically, runs tests.

The MiniMax response is expected to be a unified diff (output of `diff -u`
or `git diff`). This module:

  1. Parses the diff into a list of (file_path, hunks) tuples.
  2. Applies each file's hunks to the working tree, using `git apply`
     (atomic — if any hunk fails to apply, the whole patch is rejected).
  3. Runs the test surface (pytest + test_frequency_layer.py).
  4. If tests pass: commit. If tests fail: revert + report.

This is the safety surface of the autocode loop. The model can be told
to do anything; apply_patch.py decides what actually lands.

Public API:
    from simself.src.autocode.apply_patch import apply_and_test, parse_unified_diff

    files = parse_unified_diff(diff_text)        # list of dicts
    result = apply_and_test(diff_text, repo_root)  # PatchResult
    print(result.ok, result.committed_sha)
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class PatchFile:
    """One file in a unified diff."""
    path: str                 # relative to repo root
    is_new: bool              # /dev/null in old
    is_deleted: bool          # /dev/null in new
    old_mode: Optional[str] = None
    new_mode: Optional[str] = None
    hunks: List["PatchHunk"] = field(default_factory=list)


@dataclass
class PatchHunk:
    """One @@ -X,Y +A,B @@ block within a file."""
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[str] = field(default_factory=list)
    # lines are the +/-/' ' prefixed lines from the hunk body


@dataclass
class PatchResult:
    """The outcome of apply_and_test()."""
    ok: bool
    applied: bool = False      # True if diff was applied to the working tree
    tested: bool = False       # True if the test surface ran
    committed: bool = False    # True if a git commit was made
    commit_sha: Optional[str] = None
    commit_message: Optional[str] = None
    files_touched: List[str] = field(default_factory=list)
    test_output: str = ""
    error: Optional[str] = None
    reverted: bool = False     # True if the working tree was rolled back


# --- Unified diff parser ---------------------------------------------------

_HUNK_RE = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$"
)
_FILE_HEADER_RE = re.compile(r"^\+\+\+ (\S+)")
_OLD_FILE_RE = re.compile(r"^--- (\S+)")


def parse_unified_diff(text: str) -> List[PatchFile]:
    """Parse a unified diff into PatchFile entries.

    Supports:
      - plain `diff -u` output
      - `git diff` output (with `diff --git a/path b/path` headers)
      - new files (--- /dev/null) and deleted files (+++ /dev/null)
      - multiple files per patch
    """
    files: List[PatchFile] = []
    current: Optional[PatchFile] = None
    current_hunk: Optional[PatchHunk] = None

    def _close_file():
        """Finalize the current file: append trailing hunk and the file."""
        nonlocal current, current_hunk
        if current is not None:
            if current_hunk is not None:
                current.hunks.append(current_hunk)
                current_hunk = None
            # If the file has no path (malformed header), drop it.
            if current.path:
                files.append(current)
            current = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")

        # File header detection (git format).
        if line.startswith("diff --git "):
            _close_file()
            current = PatchFile(path="", is_new=False, is_deleted=False)
            m = re.match(r"^diff --git a/(.+?) b/(.+?)$", line)
            if m:
                current.path = m.group(2)
            continue

        if line.startswith("--- "):
            # If we already have a path from `diff --git`, this just
            # confirms the old side. Don't start a new PatchFile.
            if current is not None and current.path:
                m = _OLD_FILE_RE.match(line)
                if m:
                    old = m.group(1)
                    if old == "/dev/null":
                        current.is_new = True
                continue
            _close_file()
            current = PatchFile(path="", is_new=False, is_deleted=False)
            m = _OLD_FILE_RE.match(line)
            if m:
                old = m.group(1)
                if old == "/dev/null":
                    current.is_new = True
                else:
                    current.path = old[2:] if old.startswith("a/") else old
            continue

        if line.startswith("+++ "):
            m = _FILE_HEADER_RE.match(line)
            if m and current is not None:
                new = m.group(1)
                if new == "/dev/null":
                    current.is_deleted = True
                elif not current.path:
                    current.path = new[2:] if new.startswith("b/") else new
            continue

        if line.startswith("@@"):
            if current is None:
                continue
            if current_hunk is not None:
                current.hunks.append(current_hunk)
            m = _HUNK_RE.match(line)
            if not m:
                continue
            current_hunk = PatchHunk(
                old_start=int(m.group(1)),
                old_count=int(m.group(2) or 1),
                new_start=int(m.group(3)),
                new_count=int(m.group(4) or 1),
                lines=[],
            )
            continue

        if current_hunk is not None:
            if line.startswith((" ", "+", "-")):
                current_hunk.lines.append(line)
            elif line == "":
                current_hunk.lines.append(" ")

    _close_file()

    return files


# --- Apply via git apply ---------------------------------------------------

def _validate_protected(files: List[PatchFile],
                        protected: Optional[set] = None) -> Optional[str]:
    """Return an error message if any file is protected, else None."""
    prot = protected if protected is not None else {
        "LICENSE", "README.md", "GENESIS.md", ".gitignore",
    }
    for f in files:
        # exact match or prefix-match for directories ending with /
        for p in prot:
            if f.path == p or (p.endswith("/") and f.path.startswith(p)):
                return f"refused: file '{f.path}' is protected ({p})"
    return None


def apply_with_git(diff_text: str, repo_root: str) -> Tuple[bool, str]:
    """Apply the diff using `git apply --check` first, then `git apply`.

    Returns (ok, message). If ok is False, message is the error.
    """
    # Write diff to a temp file.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".patch", delete=False, encoding="utf-8"
    ) as f:
        f.write(diff_text)
        patch_path = f.name
    try:
        # Dry-run check first.
        r = subprocess.run(
            ["git", "apply", "--check", patch_path],
            capture_output=True, text=True, cwd=repo_root,
        )
        if r.returncode != 0:
            return False, f"git apply --check failed:\n{r.stderr.strip()}"
        # Real apply.
        r = subprocess.run(
            ["git", "apply", patch_path],
            capture_output=True, text=True, cwd=repo_root,
        )
        if r.returncode != 0:
            return False, f"git apply failed:\n{r.stderr.strip()}"
        return True, "applied"
    finally:
        try:
            os.unlink(patch_path)
        except OSError:
            pass


def revert_files(files: List[PatchFile], repo_root: str) -> bool:
    """Revert the listed files via `git checkout -- <path>...`.

    Only touches files that were tracked before the patch (i.e. not new
    files). New files are left to be cleaned up by `git clean -fd` (the
    loop calls this separately).
    """
    if not files:
        return True
    paths = [f.path for f in files if not f.is_new and not f.is_deleted]
    if not paths:
        return True
    r = subprocess.run(
        ["git", "checkout", "--"] + paths,
        capture_output=True, text=True, cwd=repo_root,
    )
    return r.returncode == 0


def clean_new_files(files: List[PatchFile], repo_root: str) -> bool:
    """Remove any new files introduced by the patch."""
    new_paths = [f.path for f in files if f.is_new]
    if not new_paths:
        return True
    r = subprocess.run(
        ["git", "clean", "-fd"] + new_paths,
        capture_output=True, text=True, cwd=repo_root,
    )
    return r.returncode == 0


# --- Test runner -------------------------------------------------------- --------------------------------------------------------

DEFAULT_TEST_COMMANDS = [
    ["python", "-m", "pytest", "tests/", "-q", "--tb=line"],
    ["python", "src/constitutional/test_frequency_layer.py"],
]


def run_test_surface(repo_root: str,
                     commands: Optional[List[List[str]]] = None,
                     timeout: float = 120.0) -> Tuple[bool, str]:
    """Run each test command. Return (all_passed, combined_output)."""
    cmds = commands if commands is not None else DEFAULT_TEST_COMMANDS
    all_ok = True
    out_parts = []
    for cmd in cmds:
        try:
            r = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout, cwd=repo_root,
            )
            ok = r.returncode == 0
            all_ok = all_ok and ok
            out_parts.append(
                f"$ {' '.join(cmd)}\n"
                f"returncode: {r.returncode}\n"
                f"stdout(last 20):\n" +
                "\n".join(r.stdout.strip().split("\n")[-20:]) +
                f"\nstderr(last 10):\n" +
                "\n".join(r.stderr.strip().split("\n")[-10:])
            )
        except subprocess.TimeoutExpired:
            all_ok = False
            out_parts.append(f"$ {' '.join(cmd)}\nTIMEOUT after {timeout}s")
    return all_ok, "\n\n".join(out_parts)


# --- Top-level: apply_and_test --------------------------------------------

def apply_and_test(
    diff_text: str,
    repo_root: str,
    *,
    commit_message: Optional[str] = None,
    test_commands: Optional[List[List[str]]] = None,
    protected: Optional[set] = None,
    auto_commit: bool = True,
) -> PatchResult:
    """Apply a diff, run the test surface, commit if tests pass.

    This is the safety surface. Order:
      1. Parse the diff.
      2. Reject if any file is protected.
      3. git apply --check (dry run).
      4. git apply (real run).
      5. Run test surface.
      6. If tests pass and auto_commit=True: git commit.
      7. If tests fail: roll back.

    Returns a PatchResult describing what happened.
    """
    files = parse_unified_diff(diff_text)
    if not files:
        return PatchResult(ok=False, error="no files in diff (empty or unparseable)")

    prot_err = _validate_protected(files, protected=protected)
    if prot_err is not None:
        return PatchResult(ok=False, error=prot_err, files_touched=[f.path for f in files])

    paths = [f.path for f in files]
    ok, msg = apply_with_git(diff_text, repo_root)
    if not ok:
        return PatchResult(ok=False, error=msg, files_touched=paths)
    applied = True

    tests_ok, test_output = run_test_surface(repo_root, commands=test_commands)
    tested = True

    if not tests_ok:
        # Roll back.
        reverted = revert_files(files, repo_root) and clean_new_files(files, repo_root)
        return PatchResult(
            ok=False,
            applied=applied,
            tested=tested,
            reverted=reverted,
            test_output=test_output,
            error="tests failed; patch reverted",
            files_touched=paths,
        )

    committed = False
    commit_sha = None
    if auto_commit:
        msg = commit_message or f"autocode: apply patch ({len(files)} file(s))"
        r = subprocess.run(
            ["git", "add", "-A"], capture_output=True, text=True, cwd=repo_root,
        )
        r = subprocess.run(
            ["git", "commit", "-m", msg],
            capture_output=True, text=True, cwd=repo_root,
        )
        if r.returncode == 0:
            committed = True
            sha_r = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, cwd=repo_root,
            )
            commit_sha = sha_r.stdout.strip()[:12]

    return PatchResult(
        ok=True,
        applied=applied,
        tested=tested,
        committed=committed,
        commit_sha=commit_sha,
        commit_message=commit_message if auto_commit else None,
        test_output=test_output,
        files_touched=paths,
    )


# --- CLI -------------------------------------------------------------------

def _cli():
    import argparse
    p = argparse.ArgumentParser(
        description="Apply a unified diff and run the test surface."
    )
    p.add_argument("patch", help="Path to a .patch/.diff file, or '-' for stdin.")
    p.add_argument("--repo-root", default=None,
                   help="Path to the repo (default: autodetect).")
    p.add_argument("--message", default=None,
                   help="Commit message (default: 'autocode: apply patch').")
    p.add_argument("--no-commit", action="store_true",
                   help="Apply + test, but don't commit (just inspect).")
    args = p.parse_args()

    text = (sys.stdin.read() if args.patch == "-"
            else open(args.patch, "r", encoding="utf-8").read())

    repo_root = args.repo_root or os.getcwd()
    r = apply_and_test(
        text,
        repo_root=repo_root,
        commit_message=args.message,
        auto_commit=not args.no_commit,
    )
    print(f"ok: {r.ok}")
    print(f"applied: {r.applied}")
    print(f"tested: {r.tested}")
    print(f"reverted: {r.reverted}")
    print(f"committed: {r.committed}  sha: {r.commit_sha}")
    print(f"files_touched: {r.files_touched}")
    if r.error:
        print(f"error: {r.error}")
    if r.test_output:
        print("--- test output ---")
        print(r.test_output)


if __name__ == "__main__":
    _cli()