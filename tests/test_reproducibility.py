"""
test_reproducibility.py — nothing in this substrate may depend on PYTHONHASHSEED.

WHY THIS FILE EXISTS (2026-10-16, Hermes).

Four separate places used Python's builtin `hash()` on data that had to be
stable, and each one failed in a different, invisible way:

  constitutional/lexicon/ingest.py   embed_bag
      the lexicon's embedder. The same span embedded to axis 2 in one process
      and axis 4 in the next. Committed units did not survive a restart, and
      the M0 gate's allow/refuse verdict was not reproducible — identical
      input, different answer, chosen by process start order.

  constitutional/constitution.py      embed_text
      THE WORST OF THE FOUR. This builds psi_0. The ground itself was
      re-randomized on every start, so no position, drift, or measurement
      could survive a restart. An identity substrate that re-randomizes its
      own ground is not holding a position.

  constitutional/frozen_experiment.py  f1_run's distinctness check
      a demo whose own number was a per-run lottery.

  language_stalk_control.py           _reinforce_projection's trace key
      a delayed-reward trace that silently lost every entry between runs.

All four are now blake2b. This file is the instrument that says "and there
are no more", because the failure mode is invisible by construction: it
produces no exception, no warning, and plausible output — it just quietly
disagrees with itself.

THE METHOD. Run the check in a real SUBPROCESS, not in-process. In-process,
`hash()` is already resolved and everything agrees forever; the bug only
appears across interpreter starts. Two fresh interpreters must produce
identical output. Setting PYTHONHASHSEED in the test would defeat the
purpose — the point is that the code is correct WITHOUT anyone having to
remember to set an environment variable in every launcher.

WHAT THIS DOES NOT ESTABLISH

That every hash in the repo is deterministic — it checks the four that were
broken plus the general pattern below. A `hash()` that legitimately wants
process-local randomness (e.g. a cache key that never leaves the process) is
not a defect; the pattern check is deliberately narrow about what counts.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def _run_twice(code: str) -> tuple[str, str]:
    """Run identical code in two fresh interpreters, with hash randomization ON."""
    outs = []
    for _ in range(2):
        r = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=180,
        )
        assert r.returncode == 0, f"subprocess failed: {r.stderr[-500:]}"
        outs.append(r.stdout.strip())
    return outs[0], outs[1]


def test_embed_bag_is_stable_across_processes():
    a, b = _run_twice(
        "import sys; sys.path.insert(0, r'%s');"
        "from constitutional.lexicon.ingest import embed_bag;"
        "print([round(float(x), 9) for x in embed_bag('the ground self')])" % SRC
    )
    assert a == b and a, f"embed_bag unstable across processes:\n  {a}\n  {b}"


def test_embed_text_and_psi_0_are_stable_across_processes():
    """The one that mattered most: psi_0 is the ground."""
    a, b = _run_twice(
        "import sys; sys.path.insert(0, r'%s');"
        "import numpy as np;"
        "from constitutional.constitution import Constitution, embed_text;"
        "c = Constitution();"
        "print([round(float(x), 9) for x in c.psi_0],"
        " [round(float(x), 9) for x in embed_text('the ground self')])" % SRC
    )
    assert a == b and a, f"psi_0 unstable across processes:\n  {a}\n  {b}"


def test_a_constitution_built_twice_is_identical():
    """Same process is not enough — this catches per-process re-rolling."""
    code = (
        "import sys; sys.path.insert(0, r'%s');"
        "import numpy as np;"
        "from constitutional.constitution import Constitution;"
        "print(np.allclose(Constitution().psi_0, Constitution().psi_0))" % SRC
    )
    a, b = _run_twice(code)
    assert a == "True", f"two Constitution() calls disagree: {a} / {b}"


def test_gate_verdict_is_reproducible_across_processes():
    """The user-visible consequence: same span, same verdict, every run."""
    code = (
        "import sys; sys.path.insert(0, r'%s');"
        "from coding_operator_object import CodingOperatorObject;"
        "op = CodingOperatorObject();"
        "print([op.propose_span(s)['allow'] for s in"
        " ('form', 'gate', 'core', 'allow', 'truth', 'verdict', 'unit')])" % SRC
    )
    a, b = _run_twice(code)
    assert a == b and a, f"M0 verdict is not reproducible:\n  {a}\n  {b}"


# ---------------------------------------------------------------------------
# the pattern check: catch the class, not just the four instances
# ---------------------------------------------------------------------------

_ALLOWED_CALLS = {"hashlib", "blake2b", "md5", "sha1", "sha256", "sha512"}


def _uses_builtin_hash(tree: ast.AST) -> bool:
    """True if the tree calls bare `hash(...)`."""
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "hash"):
            return True
    return False


def test_no_module_under_src_calls_bare_hash():
    """No file in src/ may call builtin hash().

    This is the check that generalises. The four that were broken are fixed;
    this fails on the fifth one the day someone writes it, instead of on the
    day someone notices a number changed between runs.

    Excluded: test files (a test may legitimately use hash() to build a
    throwaway fixture) and files under any directory named tests/.
    """
    offenders = []
    for path in SRC.rglob("*.py"):
        if "test" in path.name or "tests" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        if _uses_builtin_hash(tree):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, (
        "builtin hash() found in substrate code — unstable across processes:\n  "
        + "\n  ".join(offenders)
    )