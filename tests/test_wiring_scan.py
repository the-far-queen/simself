"""
test_wiring_scan.py -- reachability across ALL of src/, not a named list.

WHY THIS EXISTS ALONGSIDE test_wiring.py
----------------------------------------
`tests/test_wiring.py` already exists and already earned its keep: it
found `ConstitutionalDreaming` working perfectly and never called by
anything. It checks SIX named modules with an AST parse that only
follows imports, constructions, and imports-by-name.

It cannot see the failure mode measured 2026-10-09, because that mode
is at the TOP LEVEL of src/ rather than inside constitutional/:

    loop.MainLoop              130 lines, no test references it
    selfcore.py                 192 lines, 0 test files
    coding_operator_object.py   67 lines, 0 test files
    robotic_field_core.py      178 lines, 0 test files
    training_bridge.py         185 lines, 0 test files
    m1_m0_negotiation.py       34 lines, 0 test files
    modulator.py              251 lines, 0 test files
    actions.py                 84 lines, 0 test files

That is the learning loop, the operators and the training bridge -- the
parts that would make the system ADAPT rather than merely exist. The
project's own vocabulary for this is *unwired*, and it already names it.

So: this file does the whole-tree scan and PRINTS the state. It does not
fail on an unwired module, because these are declared components of a
system still under construction and failing the suite every time one is
added would train everyone to ignore it. Instead it emits a report, and
the report is the point: an inventory that is on the record cannot be
mistaken for progress.

RUN IT DIRECTLY for the inventory:

    python tests/test_wiring_scan.py

WHAT IT DOES NOT ESTABLISH
--------------------------
Having a caller is not the same as working, and it is certainly not the
same as being exercised at runtime. This asserts reachability only. A
wired module can still be broken -- which is why area 10 of the atlas
exam mutates the substrate rather than trusting it.

The load-bearing failure in this session's history was not an unwired
module; it was a WIRED one that did not work. `hodge_cycle` passed its
own docstring while diverging. `resilience` gated after shrinking the
attack. Reachability is necessary and nowhere near sufficient.
"""

from __future__ import annotations

import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(REPO, "src")

# entry points by design, not libraries
ENTRY_POINTS = {"end_to_end_demo"}

# wired this session from measured defects; all have dedicated tests
KNOWN_WIRED = {
    "sensorimotor_grounding", "nested_stalks",
    "sovereign_governor", "resilience",
}


def _py(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in ("__pycache__",)]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(d, f)


def _parse(path):
    try:
        return ast.parse(open(path, encoding="utf-8", errors="replace").read())
    except SyntaxError:
        return None


def _all_names(path):
    """every identifier AND string token in a file, minus the file itself"""
    tree = _parse(path)
    if tree is None:
        return set()
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            out.add(node.id)
        elif isinstance(node, ast.Attribute):
            out.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            for part in node.value.replace(".", " ").split():
                out.add(part)
    return out


def _imports(path):
    tree = _parse(path)
    if tree is None:
        return set()
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.name.split(".")[-1])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.add(node.module.split(".")[-1])
            for a in node.names:
                out.add(a.name)
    return out


def _test_constructions(paths):
    """class/function names actually CALLED in the tests.

    Not string search. The first version of this scan used
    `stem in test_text`, which matched the word "loop" inside unrelated
    docstrings and classified an unwired module as wired -- the exact
    mistake the history of tests/test_wiring.py records. Imports plus
    real constructions only.
    """
    out = set()
    for p in paths:
        tree = _parse(p)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = getattr(fn, "id", None) or getattr(fn, "attr", None)
                if name:
                    out.add(name.lower())
    return out


def scan():
    """returns (wired, unwired, skipped)"""
    files = list(_py(SRC))
    tdir = os.path.join(REPO, "tests")
    test_files = list(_py(tdir)) if os.path.isdir(tdir) else []
    test_imports = set()
    for p in test_files:
        test_imports |= _imports(p)
    test_built = _test_constructions(test_files)

    wired, unwired, skipped = [], [], []
    for path in files:
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem in ENTRY_POINTS:
            skipped.append(stem)
            continue

        callers = False
        for other in files:
            if other == path:
                continue
            if stem in _imports(other):
                callers = True
                break
        # a test counts as a caller only via a real import or a real
        # construction, never via a word appearing in a docstring
        cls_name = "".join(w.capitalize() for w in stem.split("_"))
        if not callers and (stem in test_imports or cls_name in test_built
                            or stem in KNOWN_WIRED):
            callers = True
        (wired if callers else unwired).append(stem)
    return wired, unwired, skipped


def main():
    wired, unwired, skipped = scan()
    print("=" * 68)
    print(f"REACHABILITY SCAN -- {len(wired) + len(unwired) + len(skipped)} modules in src/")
    print("=" * 68)
    print(f"\nWIRED ({len(wired)}):")
    for m in sorted(wired):
        print(f"   {m}")
    print(f"\nUNWIRED ({len(unwired)}) -- present, readable, never called:")
    for m in sorted(unwired):
        print(f"   {m}")
    if skipped:
        print(f"\nENTRY POINTS ({len(skipped)}): {', '.join(sorted(skipped))}")

    print()
    print("THE CONTROL-SYSTEM PARTS, specifically:")
    for m in ("loop", "selfcore", "coding_operator_object", "robotic_field_core",
              "training_bridge", "m1_m0_negotiation", "modulator", "actions"):
        state = "wired" if m in wired else ("UNWIRED" if m in unwired else "?")
        print(f"   {m:26s} {state}")
    print()
    print("  The learning loop, the four operators and the training bridge are")
    print("  the parts that make the system ADAPT rather than merely exist.")
    print("  Until they are wired, the adaptable parts are present and dark.")
    print()
    print("  This is an INVENTORY, not a verdict. Having a caller is not the")
    print("  same as working -- hodge_cycle was reachable and diverged.")
    print("  Reachability is necessary and nowhere near sufficient.")


# ---------------------------------------------------------------------------
# the part that runs under pytest
# ---------------------------------------------------------------------------

def test_scan_finds_the_control_system_modules():
    """Rule 7 for this file. If the scan silently found nothing, the
    inventory below would print an empty list and look like good news."""
    wired, unwired, skipped = scan()
    total = len(wired) + len(unwired) + len(skipped)
    assert total > 20, f"only {total} modules found; the scan is broken"
    # the scan must at least SEE the control-system modules, wired or not
    seen = set(wired) | set(unwired) | set(skipped)
    for m in ("loop", "actions", "modulator"):
        assert m in seen, f"scan missed {m}"


def test_no_unwired_module_looks_wired():
    """The scan must not count a module as wired because its own name
    appears in a test's docstring. This is the mistake the first version
    of tests/test_wiring.py made, and it made an unwired module look
    wired."""
    wired, unwired, _ = scan()
    # `loop` is genuinely unreferenced by any test today; if that changes
    # this assertion forces the list to be updated rather than silently
    # reclassified.
    assert "loop" in unwired or "loop" in wired, "scan lost the loop module"
    assert not (set(wired) & {"loop"}), \
        "loop has callers -- drop this assertion and update the inventory"


if __name__ == "__main__":
    main()