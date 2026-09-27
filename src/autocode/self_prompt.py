"""
self_prompt.py — assembles the 5-field self-prompt from current repo state.

The prompt is structured as:

    [REPOSITORY STATE]    — a snapshot of the canonical files
    [TEST SURFACE]        — pytest output, test_frequency_layer.py output, etc.
    [GOAL]                — one sentence
    [CONSTRAINTS]         — list of "do not"s
    [PLAN FIELD]          — model responds here with a unified diff

The plan field is the model's output. Everything else is assembly.

Public API:
    from simself.src.autocode.self_prompt import build, SelfPrompt

    sp = build(
        goal="Make agent_pool.py end-to-end work.",
        constraints=["Do not modify legacy/simself_v6_2_unified.py"],
        repo_root="/path/to/simself",
    )
    text = sp.render()      # the prompt string
    response = call_minimax.complete(prompt=text)
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Optional


# Files the model is allowed to see / touch. These are the canonical
# surface from the README "Where to look" table.
CANONICAL_FILES = [
    # simself
    "src/constitutional/simself.py",
    "src/constitutional/ground.py",
    "src/constitutional/constitution.py",
    "src/constitutional/resolution.py",
    "src/constitutional/atlas_exam.py",
    "src/constitutional/frequency.py",
    "src/constitutional/test_frequency_layer.py",
    "src/state_vector.py",
    "src/m1_m0_negotiation.py",
    "src/harness/gate.py",
    "src/demos/demo_one.py",
    "src/demos/atlas_run.py",
    "tests/test_restart.py",
    "tests/test_mltr.py",
    "tests/test_field.py",
    # fieldcore
    "../fieldcore/src/tiniest_core/tiniest_core.py",
    "../fieldcore/src/substrate.py",
    "../fieldcore/src/stalk_topology.py",
    "../fieldcore/src/steel_ball_proof.py",
    "../fieldcore/tests/test_sheaf_nn_latency.py",
    "../fieldcore/tests/test_sparse_substrate.py",
]

# Default test commands. Their output goes into [TEST SURFACE].
DEFAULT_TEST_COMMANDS = [
    # pytest of the simself tests/ dir
    ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
    # constitutional test suite (standalone runner)
    ["python", "src/constitutional/test_frequency_layer.py"],
]

# Files the model is NEVER allowed to touch, regardless of constraints.
# These are load-bearing and any change requires explicit human review.
PROTECTED_FILES = {
    "LICENSE",
    "README.md",
    "GENESIS.md",
    ".gitignore",
    "docs/sacred-library/",  # off-mission; preserved verbatim per README
    "notes/analogies/",      # off-mission; preserved verbatim per README
}


@dataclass
class SelfPrompt:
    """A fully rendered self-prompt ready for call_minimax.complete()."""
    goal: str
    constraints: List[str]
    repo_state: str          # [REPOSITORY STATE] section content
    test_surface: str        # [TEST SURFACE] section content
    plan_field_hint: str = field(default_factory=lambda: (
        "[PLAN FIELD — your response here. Output a unified diff only. "
        "No prose, no explanation, no markdown formatting outside the diff. "
        "If the goal cannot be satisfied within the constraints, output "
        "exactly the string NO_DIFF and nothing else.]"
    ))

    def render(self) -> str:
        """Build the final 5-field prompt string."""
        sections = [
            ("REPOSITORY STATE", self.repo_state),
            ("TEST SURFACE", self.test_surface),
            ("GOAL", self.goal),
            ("CONSTRAINTS", "\n".join(f"- {c}" for c in self.constraints)
                             if self.constraints else "(none)"),
            ("PLAN FIELD", self.plan_field_hint),
        ]
        out = []
        for title, body in sections:
            out.append(f"[{title}]")
            out.append(body.strip())
            out.append("")  # blank line between sections
        return "\n".join(out)


# ----------------------------------------------------------------------------
# Assembly helpers
# ----------------------------------------------------------------------------

def _read_canonical(repo_root: str, max_chars_per_file: int = 4000) -> str:
    """Read the canonical files and return them concatenated as text."""
    chunks = []
    for rel in CANONICAL_FILES:
        full = os.path.join(repo_root, rel)
        if not os.path.exists(full):
            chunks.append(f"--- {rel}: (file not found) ---")
            continue
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            chunks.append(f"--- {rel}: (read error: {e}) ---")
            continue
        if len(content) > max_chars_per_file:
            content = content[:max_chars_per_file] + \
                f"\n... ({len(content) - max_chars_per_file} more bytes truncated)\n"
        chunks.append(f"--- {rel} ---\n{content}")
    return "\n\n".join(chunks)


def _run_test(cmd: List[str], cwd: str, timeout: float = 60.0) -> str:
    """Run one test command and return a short result string."""
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=cwd,
        )
        out = r.stdout.strip().split("\n")
        # truncate long output
        if len(out) > 60:
            out = out[:30] + [f"... ({len(out) - 60} lines omitted) ..."] + out[-30:]
        err = r.stderr.strip().split("\n")
        if len(err) > 20:
            err = err[:10] + [f"... ({len(err) - 20} lines omitted) ..."] + err[-10:]
        return (
            f"$ {' '.join(cmd)}\n"
            f"returncode: {r.returncode}\n"
            f"stdout:\n" + "\n".join(out) + "\n"
            f"stderr:\n" + "\n".join(err)
        )
    except subprocess.TimeoutExpired:
        return f"$ {' '.join(cmd)}\nTIMEOUT after {timeout}s"
    except FileNotFoundError as e:
        return f"$ {' '.join(cmd)}\nEXECUTABLE NOT FOUND: {e}"


def _run_test_surface(repo_root: str,
                      commands: Optional[List[List[str]]] = None) -> str:
    """Run the default test commands and concatenate results."""
    cmds = commands if commands is not None else DEFAULT_TEST_COMMANDS
    results = []
    for cmd in cmds:
        results.append(_run_test(cmd, cwd=repo_root))
    return "\n\n".join(results)


def build(goal: str, *,
          constraints: Optional[List[str]] = None,
          repo_root: Optional[str] = None,
          include_test_surface: bool = True,
          test_commands: Optional[List[List[str]]] = None,
          extra_constraints: Optional[List[str]] = None) -> SelfPrompt:
    """Assemble a SelfPrompt from the current repo state.

    Args:
        goal: One-sentence description of the change to make.
        constraints: List of "do not" statements.
        repo_root: Path to the simself repo. Defaults to two parents up
            from this file (i.e. assumes simself/src/autocode/self_prompt.py).
        include_test_surface: If False, skip the test runs (faster).
        test_commands: Override the default test commands.
        extra_constraints: Additional constraints appended to `constraints`.
            Useful for callers that want to add system-level safety rules.

    Returns:
        SelfPrompt with all fields populated. Call .render() to get the
        final prompt string.
    """
    if repo_root is None:
        # default: ../../..  (simself/src/autocode/self_prompt.py)
        here = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(here, "..", "..", ".."))

    all_constraints = list(constraints or [])
    if extra_constraints:
        all_constraints.extend(extra_constraints)

    # Always add the protected-files rule (system-level safety).
    protected_note = (
        "Do not modify any of these files (system-protected): "
        + ", ".join(sorted(PROTECTED_FILES))
    )
    if protected_note not in all_constraints:
        all_constraints.append(protected_note)

    repo_state = _read_canonical(repo_root)
    test_surface = (_run_test_surface(repo_root, commands=test_commands)
                    if include_test_surface
                    else "(test surface skipped — set include_test_surface=True to run)")

    return SelfPrompt(
        goal=goal,
        constraints=all_constraints,
        repo_state=repo_state,
        test_surface=test_surface,
    )


# --- CLI for ad-hoc testing ------------------------------------------------

def _cli():
    import argparse
    p = argparse.ArgumentParser(
        description="Build a self-prompt from the current repo state and print it."
    )
    p.add_argument("--goal", required=True, help="One-sentence goal.")
    p.add_argument("--constraint", action="append", default=[],
                   help="Add a constraint (can be passed multiple times).")
    p.add_argument("--repo-root", default=None,
                   help="Path to the simself repo (default: autodetect).")
    p.add_argument("--no-tests", action="store_true",
                   help="Skip running the test commands (faster).")
    p.add_argument("--out", default=None,
                   help="Write the prompt to this file instead of stdout.")
    args = p.parse_args()
    sp = build(
        goal=args.goal,
        constraints=args.constraint,
        repo_root=args.repo_root,
        include_test_surface=not args.no_tests,
    )
    text = sp.render()
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        sys.stderr.write(f"[self_prompt] wrote {len(text)} bytes to {args.out}\n")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    _cli()