"""
test_wiring.py — W1..W4. Is the machinery actually reachable?

Found while fixing defect E: `ConstitutionalDreaming` worked perfectly
and was **never called by anything**. The harness builds a memory and
never dreams. The module had tests, imported cleanly, and had no
operating mode.

That is defect F's cousin. Grok's words about handoff apply directly:
*a symbolic milestone rather than a new operating mode.* A mechanism
that no code path reaches is the same thing wearing a different hat.

These tests are cheap and they catch a whole class of "looks finished"
defect: a module with no caller.
"""

from __future__ import annotations

import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(REPO, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

CONST = os.path.join(SRC, "constitutional")

# modules that MUST be reachable from somewhere else
MUST_BE_CALLED = ["dreaming", "entity", "boot_sequence", "resolution"]

# modules deliberately parked. entity.py is marked LEGACY in its own
# docstring and returns a placeholder — wiring a stub in would be worse
# than leaving it dark, because it would look alive. It must be removed
# from this list and from the package only when it is either reimplemented
# or deleted, not before.
RETIRED = {
    "entity": "LEGACY stub; docstring says so; wiring a placeholder "
              "would make it look alive",
}


def _referenced_by_others(module: str) -> list:
    """Which files outside module.py actually IMPORT or INSTANTIATE this?

    A text search is not enough and this test was wrong because of it:
    grepping for the word "dreaming" matched a comment, an unrelated
    `_is_dreaming` flag, and a `"dreaming"` string literal, so a module
    with zero callers looked wired.

    This parses. It only counts a file that imports the module's class,
    or constructs it, or imports the module by name.
    """
    cls = "".join(p.capitalize() for p in module.split("_"))   # ConstitutionalDreaming
    hits = []
    for root, dirs, files in os.walk(CONST):
        dirs[:] = [d for d in dirs if d not in ("__pycache__",)]
        for f in files:
            if not f.endswith(".py") or f == f"{module}.py":
                continue
            p = os.path.join(root, f)
            try:
                tree = ast.parse(open(p, encoding="utf-8").read())
            except SyntaxError:
                continue
            real = False
            for node in ast.walk(tree):
                # from constitutional.dreaming import X
                if isinstance(node, ast.ImportFrom) and node.module and \
                        node.module.endswith(module):
                    real = True
                # import constitutional.dreaming
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.endswith(f".{module}") or \
                                alias.name.endswith(f"constitutional.{module}"):
                            real = True
                # ConstitutionalDreaming(...) constructed
                if isinstance(node, ast.Call):
                    fn = node.func
                    name = getattr(fn, "id", None) or getattr(fn, "attr", None)
                    if name == cls:
                        real = True
            if real:
                hits.append(os.path.relpath(p, REPO))
    return hits


def t_W1_core_modules_have_callers():
    """a module nobody imports is not part of the system."""
    dead = []
    for m in MUST_BE_CALLED:
        if m in RETIRED:
            continue                       # parked on purpose, and says so
        refs = _referenced_by_others(m)
        if not refs:
            dead.append(m)
    assert not dead, (
        f"modules with no caller: {dead}. These are documented as "
        f"components of the system but nothing reaches them."
    )
    parked = [m for m in MUST_BE_CALLED if m in RETIRED]
    print(f"W1: ok ({len(MUST_BE_CALLED) - len(parked)} modules wired, "
          f"{len(parked)} parked on purpose: {parked})")


def t_W2_dreamer_is_constructible_and_runs():
    """the fix must survive being wired in, not just in its own test."""
    from constitutional.dreaming import ConstitutionalDreaming
    from constitutional.ground import Ground
    from constitutional.memory import ConstitutionalMemory
    import numpy as np

    mem = ConstitutionalMemory(dim=16)
    base = np.ones(16, dtype=np.float64) / np.sqrt(16)
    rng = np.random.RandomState(3)
    for i in range(4):
        v = base + 0.2 * rng.randn(16)
        v /= np.linalg.norm(v)
        mem.commit(mem.add(f"u{i}", v))

    d = ConstitutionalDreaming(Ground(base), 16, memory=mem)
    r = d.dream()
    assert r["source_unit_ids"], "dreamer produced no sources when wired"
    assert isinstance(r["kept"], bool)
    print(f"W2: ok (wired dreamer cites "
          f"{len(r['source_unit_ids'])} sources, kept={r['kept']})")


def t_W3_harness_memory_api_still_valid():
    """the harness constructs ConstitutionalMemory() with no args.

    The memory rewrite must keep that call working, or every existing
    harness construction breaks at import.
    """
    from constitutional.memory import ConstitutionalMemory
    m = ConstitutionalMemory()          # exactly what harness.py does
    assert m.dim == 64
    assert m.items == {} and m.categories == {} and m.edges == set()
    print("W3: ok (zero-arg construction preserved for harness.py)")


def t_W4_no_module_defines_pass_as_its_body():
    """the v6.2 failure: a class body that is only `pass`.

    Scanning for `pass` as an entire class body catches the fabricated-
    delivery shape before it can be committed again.
    """
    suspicious = []
    for root, dirs, files in os.walk(CONST):
        dirs[:] = [d for d in dirs if d not in ("__pycache__",)]
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(root, f)
            tree = ast.parse(open(p, encoding="utf-8").read())
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                body = [n for n in node.body
                        if not (isinstance(n, ast.Expr)
                                and isinstance(n.value, ast.Constant))]
                if len(body) == 1 and isinstance(body[0], ast.Pass):
                    suspicious.append(f"{os.path.relpath(p, REPO)}:{node.name}")
    assert not suspicious, (
        f"classes whose entire body is `pass`: {suspicious}. "
        f"A class with no behaviour is a label, not a mechanism."
    )
    print(f"W4: ok (no pass-only class bodies in {CONST})")


def main():
    t_W1_core_modules_have_callers()
    t_W2_dreamer_is_constructible_and_runs()
    t_W3_harness_memory_api_still_valid()
    t_W4_no_module_defines_pass_as_its_body()
    print("\nWIRING TESTS PASS (W1..W4)")


if __name__ == "__main__":
    main()
