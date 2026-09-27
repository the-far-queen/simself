"""
test_autocode.py — smoke tests for the autocode/ surface.

Verifies:
  1. All 4 modules import cleanly.
  2. The unified-diff parser handles git-format and plain-format diffs,
     new files, deleted files, and multiple hunks per file.
  3. The protected-files check rejects writes to LICENSE / README.md / etc.
  4. apply_and_test() on a real patch against the real repo: apply,
     run test surface, commit, then undo the commit. (slow)
  5. NO_DIFF sentinel short-circuits (returns ok=False, stop_reason=no_diff).

These tests do NOT call the MiniMax API — they exercise the local
plumbing only. The full end-to-end (prompt → API → patch → test →
commit) is exercised separately by a run_loop.py --goal invocation
that requires $MINIMAX_API_KEY.
"""
import os
import subprocess
import sys
from pathlib import Path

# Make autocode/ importable. test_mltr.py uses the same pattern.
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
_SRC = _REPO / "src"
sys.path.insert(0, str(_SRC))

import pytest


def test_imports():
    """All 4 autocode modules import without error."""
    from autocode import call_minimax, self_prompt, apply_patch, run_loop
    assert hasattr(call_minimax, "complete")
    assert hasattr(call_minimax, "MiniMaxError")
    assert hasattr(self_prompt, "build")
    assert hasattr(self_prompt, "SelfPrompt")
    assert hasattr(apply_patch, "apply_and_test")
    assert hasattr(apply_patch, "parse_unified_diff")
    assert hasattr(run_loop, "run")


def test_parse_single_file():
    """git-format diff: 1 file, 2 hunks."""
    from autocode.apply_patch import parse_unified_diff
    diff = (
        "diff --git a/foo.py b/foo.py\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -1,3 +1,4 @@\n"
        " line one\n"
        "-line two\n"
        "+line two (modified)\n"
        "+line two-bis\n"
        " line three\n"
        "@@ -10,2 +11,3 @@\n"
        " context\n"
        " context\n"
        "+added at end\n"
    )
    files = parse_unified_diff(diff)
    assert len(files) == 1
    f = files[0]
    assert f.path == "foo.py"
    assert not f.is_new
    assert not f.is_deleted
    assert len(f.hunks) == 2
    assert f.hunks[0].old_start == 1
    assert f.hunks[0].new_count == 4
    assert len(f.hunks[0].lines) == 5


def test_parse_new_file():
    """A diff with --- /dev/null is a new file."""
    from autocode.apply_patch import parse_unified_diff
    diff = (
        "diff --git a/new.py b/new.py\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        "+++ b/new.py\n"
        "@@ -0,0 +1,2 @@\n"
        "+line a\n"
        "+line b\n"
    )
    files = parse_unified_diff(diff)
    assert len(files) == 1
    assert files[0].is_new is True
    assert files[0].path == "new.py"
    assert len(files[0].hunks) == 1


def test_parse_deleted_file():
    """A diff with +++ /dev/null is a deletion."""
    from autocode.apply_patch import parse_unified_diff
    diff = (
        "diff --git a/old.py b/old.py\n"
        "deleted file mode 100644\n"
        "--- a/old.py\n"
        "+++ /dev/null\n"
        "@@ -1,1 +0,0 @@\n"
        "-line x\n"
    )
    files = parse_unified_diff(diff)
    assert len(files) == 1
    assert files[0].is_deleted is True


def test_parse_plain_diff():
    """Plain diff -u format (no git header)."""
    from autocode.apply_patch import parse_unified_diff
    diff = (
        "--- a/x.py\n"
        "+++ b/x.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-old\n"
        "+new\n"
    )
    files = parse_unified_diff(diff)
    assert len(files) == 1
    assert files[0].path == "x.py"


def test_protected_file_check():
    """apply_and_test must reject writes to LICENSE, README.md, .gitignore."""
    from autocode.apply_patch import apply_and_test
    diff = (
        "diff --git a/LICENSE b/LICENSE\n"
        "--- a/LICENSE\n"
        "+++ b/LICENSE\n"
        "@@ -1,1 +1,1 @@\n"
        "-old\n"
        "+modified\n"
    )
    r = apply_and_test(diff, repo_root=str(_REPO), auto_commit=False)
    assert r.ok is False
    assert "protected" in (r.error or "").lower()


def test_run_loop_no_api_call_required(monkeypatch):
    """run_loop.run() short-circuits cleanly if call_minimax.complete
    returns NO_DIFF. We monkeypatch complete to avoid the API call."""
    from autocode import run_loop as rl
    from autocode import call_minimax

    def fake_complete(prompt, **kwargs):
        return call_minimax.MiniMaxResponse(
            text="NO_DIFF",
            model="fake",
            finish_reason="stop",
        )

    monkeypatch.setattr(call_minimax, "complete", fake_complete)

    result = rl.run(
        goal="Test goal that should yield NO_DIFF.",
        constraints=["No-op for testing."],
        repo_root=str(_REPO),
        max_iterations=2,
        include_test_surface=False,
    )
    assert result["ok"] is False
    assert result["stop_reason"] == "no_diff"
    assert result["iterations"] == 1


@pytest.mark.slow
def test_apply_and_commit_real_patch():
    """End-to-end: apply a real patch to a real file, run tests, commit.

    This is a slow test (runs pytest + the constitutional test layer). It
    is marked with `@pytest.mark.slow` and deselected by default. Run with
    `pytest --runslow` to include it.
    """
    from autocode.apply_patch import apply_and_test

    target_rel = "src/constitutional/simself.py"
    target = str(_REPO / target_rel)

    # Read original (HEAD version) so we can restore it.
    r = subprocess.run(
        ["git", "show", f"HEAD:{target_rel}"],
        capture_output=True, text=True, cwd=str(_REPO),
    )
    if r.returncode != 0:
        pytest.skip(f"cannot read HEAD:{target_rel}: {r.stderr.strip()}")
    original = r.stdout

    # Make a small, isolated, marker edit.
    needle = "# Defaults — match simself/config/simself_config.yaml."
    replacement = needle + " (autocode-test marker)"
    if replacement in original:
        pytest.skip("autocode-test marker already present; re-run after a fresh commit")

    modified = original.replace(needle, replacement, 1)

    with open(target, "w") as f:
        f.write(modified)

    try:
        # Generate the diff that the model WOULD have produced.
        r = subprocess.run(
            ["git", "diff", target_rel],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        diff_text = r.stdout
        assert "autocode-test marker" in diff_text

        # Revert working tree before the apply, so apply_patch does the work.
        subprocess.run(
            ["git", "checkout", "--", target_rel],
            capture_output=True, text=True, cwd=str(_REPO),
        )

        # Now exercise the full pipeline.
        result = apply_and_test(
            diff_text,
            repo_root=str(_REPO),
            commit_message="autocode-test: temporary marker (will be reverted)",
            auto_commit=True,
        )
        assert result.ok, f"apply_and_test failed: {result.error}"
        assert result.applied is True
        assert result.tested is True
        assert result.committed is True
        assert result.commit_sha is not None

        # Verify the marker is now in HEAD.
        r = subprocess.run(
            ["git", "show", "HEAD:src/constitutional/simself.py"],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        assert "autocode-test marker" in r.stdout

        # Roll back the test commit.
        subprocess.run(
            ["git", "reset", "--hard", "HEAD~1"],
            capture_output=True, text=True, cwd=str(_REPO),
        )
    finally:
        # Safety net: ensure the original is restored even if the test
        # raises mid-way.
        r = subprocess.run(
            ["git", "show", f"HEAD:{target_rel}"],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        if r.returncode == 0:
            with open(target, "w") as f:
                f.write(r.stdout)