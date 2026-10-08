"""
atlas_exam_v3.py — an exam that can FAIL.

WHY V3 EXISTS
-------------
The v2 exam scored 15/27 and looked respectable. It was measured against
a sabotaged system and NOTHING CHANGED:

    baseline total_avg   0.7778
    sabotaged total_avg  0.7778     0 of 27 items reacted

An AST audit of v2 found why:

    touch constitutional code    1
    no constitutional import     3
    hardcoded 0.5 / 1.0 literal  23

Twenty-three of twenty-seven items assigned themselves a score. The
worst is a literal tautology:

    def _item_harmonics():
        freq = 137.0
        return {"score": 1.0 if freq == 137.0 else 0.5}

That is not an examination. It cannot fail, so it cannot pass either.

THE REDESIGN
------------
A qualification test has one job: distinguish a working system from a
broken one. That means every item must

    1. EXERCISE the system, not assert about it
    2. have a PROPERTY that holds if the system works and breaks if it
       does not -- not a number that was typed in
    3. be MUTATION-SENSITIVE: sabotage the system and confirm the item
       goes red
    4. declare what it does NOT cover, so a pass is not read as a
       general claim

Item structure:

    class ExamItem:
        name        what is being checked
        property_fn the assertion, as a callable returning (ok, detail)
        covers      what this item does NOT establish

Scoring is binary per item -- pass or fail -- because the v2 exam's
partial scores hid the fact that half its items were decorative. A
half-measure on an item that either works or does not is noise.

THE FIVE PROPERTIES
-------------------
Grouped by what they can actually detect:

    P1 motion      the state MOVES when an accepted input arrives
    P2 bounded     and stays inside its bound
    P3 gates       refuses what it must, accepts what it must
    P4 immutable   the ground never moves
    P5 wired       the module has callers -- dead code fails

P5 is the one that catches the failure mode that has dominated this
project: code that imports cleanly, passes tests, and is never called.

Run: python src/constitutional/atlas_exam_v3.py --help
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import os
import sys
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
if SRC not in sys.path:
    sys.path.insert(0, SRC)


# ---------------------------------------------------------------------------
# item
# ---------------------------------------------------------------------------

@dataclass
class ExamItem:
    """One qualification check.

    `check` returns (ok: bool, detail: str). Binary by design.
    `covers` states what a pass does NOT establish -- an exam that
    cannot say what it missed is not an exam.
    """
    name: str
    property: str          # P1..P5
    check: Callable[[], Tuple[bool, str]]
    covers: str            # the limit of this item

    def run(self) -> Dict:
        try:
            ok, detail = self.check()
            return {"name": self.name, "property": self.property,
                    "pass": bool(ok), "detail": detail,
                    "does_not_establish": self.covers}
        except Exception as exc:                      # noqa: BLE001
            # an item that RAISES has failed. v2 let exceptions fall
            # through to a default score, which turned a broken system
            # into a passing grade.
            return {"name": self.name, "property": self.property,
                    "pass": False,
                    "detail": f"RAISED {type(exc).__name__}: {exc}",
                    "does_not_establish": self.covers}


# ---------------------------------------------------------------------------
# the system under test
# ---------------------------------------------------------------------------

def _make_simself(dim: int = 16, R: float = 3.0, eta: float = 0.1):
    import numpy as np
    from constitutional.constitution import Constitution
    from constitutional.ground import Ground
    from constitutional.simself import SimSelf
    c = Constitution()
    return SimSelf(constitution=c, ground=Ground(c.psi_0.copy()), R=R, eta=eta), np


def _accepted_vector(dim: int = 16, seed: int = 0):
    _, np = _make_simself(dim)
    rng = np.random.default_rng(seed)
    v = rng.normal(size=dim)
    v = v / np.linalg.norm(v)
    return v * 1.5


# ---------------------------------------------------------------------------
# P1 — MOTION. does an accepted observation actually enter the state?
# ---------------------------------------------------------------------------

def p1_motion() -> ExamItem:
    def check() -> Tuple[bool, str]:
        s, _ = _make_simself()
        before = s.drift()
        x = _accepted_vector()
        accepted = 0
        for _ in range(20):
            if s.observe(x)["allow"]:
                accepted += 1
        after = s.drift()
        ok = after > before + 1e-6
        return ok, (f"accepted {accepted}/20, drift {before:.6f} -> "
                    f"{after:.6f}")
    return ExamItem(
        "accepted input moves the state", "P1_motion", check,
        "that motion is correct, only that it exists. A system that "
        "drifts in the wrong direction also passes.",
    )


def p1_not_inert_over_many() -> ExamItem:
    """The 2026-10-06 bug was 128 accepted observations and zero
    movement. Repeat that at scale."""
    def check() -> Tuple[bool, str]:
        s, _ = _make_simself()
        rng_seen, np = _make_simself()
        rng = np.random.default_rng(5)
        drifts = []
        for _ in range(200):
            v = rng.normal(size=s.dim)
            v = v / np.linalg.norm(v)
            s.observe(v * 2.0)
            drifts.append(s.drift())
        peak = max(drifts)
        ok = peak > 1e-3
        return ok, f"max drift over 200 observations = {peak:.6f}"
    return ExamItem(
        "200 observations produce non-zero drift", "P1_motion", check,
        "anything about the DIRECTION of the drift, or whether the "
        "path is efficient.",
    )


# ---------------------------------------------------------------------------
# P2 — BOUNDED. motion stays inside the ball.
# ---------------------------------------------------------------------------

def p2_bounded() -> ExamItem:
    def check() -> Tuple[bool, str]:
        s, _ = _make_simself()
        _, np = _make_simself()
        rng = np.random.default_rng(7)
        worst = 0.0
        for _ in range(1000):
            v = rng.normal(size=s.dim)
            v = v / np.linalg.norm(v)
            s.observe(v * 3.0)
            worst = max(worst, s.drift())
        ok = worst <= s.R + 1e-9
        return ok, f"max drift {worst:.6f} against R = {s.R}"
    return ExamItem(
        "state never leaves the ball", "P2_bounded", check,
        "that the ball is the RIGHT constraint. A pass says nothing "
        "about whether R=3 is the right value.",
    )


def p2_no_divergence() -> ExamItem:
    """the opposite failure: bounded AND moving, not bounded BY stillness"""
    def check() -> Tuple[bool, str]:
        s, _ = _make_simself()
        _, np = _make_simself()
        x = _accepted_vector(seed=3)
        moved = 0
        for _ in range(50):
            s.observe(x)
            if s.drift() > 1e-6:
                moved += 1
        ok = moved == 50 and math.isfinite(s.drift())
        return ok, f"moved on {moved}/50 presentations, final {s.drift():.6f}"
    return ExamItem(
        "repeated input does not diverge or stall", "P2_bounded", check,
        "whether the steady state is where it SHOULD be.",
    )


# ---------------------------------------------------------------------------
# P3 — GATES. it must be able to say no.
# ---------------------------------------------------------------------------

def p3_gates() -> ExamItem:
    def check() -> Tuple[bool, str]:
        s, np = _make_simself()
        cases = []
        # coherent, small -> allow
        ok_x = np.zeros(16); ok_x[0] = 0.8; ok_x[1] = 0.6
        cases.append(("coherent small", s.observe(ok_x)["allow"], True))
        # orthogonal -> refuse (cos ~ 0 < 0.4)
        bad = np.zeros(16); bad[3] = 1.0
        cases.append(("orthogonal", s.observe(bad)["allow"], False))
        # zero -> refuse
        cases.append(("zero", s.observe(np.zeros(16))["allow"], False))
        wrong = [(n, g, e) for n, g, e in cases if g != e]
        return not wrong, ("all as coded" if not wrong else f"wrong: {wrong}")
    return ExamItem(
        "gate accepts what it must and refuses what it must", "P3_gate",
        check,
        "whether the THRESHOLD is right. cos >= 0.4 is a choice, not a "
        "result; this item only checks the code does what it says.",
    )


def p3_refusal_is_inert() -> ExamItem:
    """a refused input must change nothing. v2 never checked this."""
    def check() -> Tuple[bool, str]:
        s, np = _make_simself()
        x = _accepted_vector(seed=11)
        for _ in range(10):
            s.observe(x)
        d_before = s.drift()
        psi_before = s.psi_current.copy()
        bad = np.zeros(16); bad[7] = 1.0
        rec = s.observe(bad)
        d_after = s.drift()
        unchanged = bool(np.allclose(psi_before, s.psi_current))
        ok = (not rec["allow"]) and unchanged and abs(d_after - d_before) < 1e-12
        return ok, (f"allow={rec['allow']} state_unchanged={unchanged} "
                    f"drift {d_before:.9f}->{d_after:.9f}")
    return ExamItem(
        "a refused observation changes nothing", "P3_gate", check,
        "that refusal is the RIGHT call. Only that it is inert.",
    )


# ---------------------------------------------------------------------------
# P4 — IMMUTABLE GROUND. psi_0 never moves.
# ---------------------------------------------------------------------------

def p4_ground_immutable() -> ExamItem:
    def check() -> Tuple[bool, str]:
        import numpy as np
        s, _ = _make_simself()
        ground = s.psi0.copy()
        _, np2 = _make_simself()
        rng = np2.random.default_rng(2)
        for _ in range(300):
            v = rng.normal(size=s.dim)
            v = v / np.linalg.norm(v)
            s.observe(v * 2.0)
            s.tick()
        ok = bool(np.allclose(ground, s.psi0)) and \
            bool(np.allclose(ground, s.ground.psi_0))
        return ok, ("ground unchanged" if ok else
                    f"ground moved by {np.max(np.abs(ground - s.psi0)):.3e}")
    return ExamItem(
        "psi_0 is never modified by observations or ticks", "P4_immutable",
        check,
        "that the ground is the RIGHT ground, or that it is protected "
        "against a write that does not go through these paths.",
    )


def p4_ground_is_write_protected() -> ExamItem:
    """psi0 is a bare alias today. Assignment works. That is a REAL
    fragility -- the same one that let an untrained layer under
    no_grad() rewrite psi_0 every tick in an earlier version."""
    def check() -> Tuple[bool, str]:
        s, _ = _make_simself()
        before = float(s.psi0[0])
        try:
            s.psi0[0] = 12345.0
            after = float(s.psi0[0])
        except ValueError:
            return True, "psi_0 is write-protected"
        leaked = abs(after - before) > 1e-9
        return not leaked, (
            "write was silently accepted and propagated"
            if leaked else "assignment did not propagate")
    return ExamItem(
        "psi_0 resists direct write", "P4_immutable", check,
        "protection against every possible write. A read-only flag does "
        "not stop deliberate re-binding.",
    )


# ---------------------------------------------------------------------------
# P5 — WIRED. dead code fails. This is the one that matters most here.
# ---------------------------------------------------------------------------

def _module_callers(module_stem: str) -> int:
    """count real inbound references by AST, not by grep.

    A grep version once matched a comment and a string literal and
    reported a dead module as wired, so this resolves imports properly.
    """
    count = 0
    for root, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            if os.path.basename(path) == f"{module_stem}.py":
                continue
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                # from x import module_stem
                if isinstance(node, ast.ImportFrom):
                    if any(a.name == module_stem for a in node.names):
                        count += 1
                # import module_stem
                elif isinstance(node, ast.Import):
                    if any(a.name.split(".")[0] == module_stem
                           for a in node.names):
                        count += 1
                # attribute access x.module_stem
                elif isinstance(node, ast.Attribute):
                    if node.attr == module_stem:
                        count += 1
    return count


def p5_simself_is_wired() -> ExamItem:
    def check() -> Tuple[bool, str]:
        n = _module_callers("simself")
        return n > 0, f"{n} inbound references to simself"
    return ExamItem(
        "the canonical simself module has callers", "P5_wired", check,
        "that it is CALLED, only that it is REFERENCED. A module imported "
        "but never invoked passes this.",
    )


def p5_no_pass_only_classes() -> ExamItem:
    """the v6.2 shape: a class whose body is only `pass`."""
    def check() -> Tuple[bool, str]:
        offenders = []
        pkg = os.path.join(SRC, "constitutional")
        for f in os.listdir(pkg) if os.path.isdir(pkg) else []:
            if not f.endswith(".py"):
                continue
            path = os.path.join(pkg, f)
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    body = [n for n in node.body
                            if not isinstance(n, ast.Pass)]
                    if not body:
                        offenders.append(f"{f}:{node.name}")
        return not offenders, (
            "no pass-only classes" if not offenders
            else f"pass-only: {offenders[:4]}")
    return ExamItem(
        "no class has an empty body", "P5_wired", check,
        "that every non-empty class is CORRECT. It only detects the "
        "empty-body shape.",
    )


# ---------------------------------------------------------------------------
# the exam
# ---------------------------------------------------------------------------

def build_exam() -> List[ExamItem]:
    return [
        p1_motion(),
        p1_not_inert_over_many(),
        p2_bounded(),
        p2_no_divergence(),
        p3_gates(),
        p3_refusal_is_inert(),
        p4_ground_immutable(),
        p4_ground_is_write_protected(),
        p5_simself_is_wired(),
        p5_no_pass_only_classes(),
    ]


def run_exam(items: Optional[List[ExamItem]] = None) -> Dict:
    items = items or build_exam()
    results = [it.run() for it in items]
    by_prop: Dict[str, Dict[str, int]] = {}
    for r in results:
        p = by_prop.setdefault(r["property"], {"pass": 0, "fail": 0})
        p["pass" if r["pass"] else "fail"] += 1
    return {
        "results": results,
        "passed": sum(1 for r in results if r["pass"]),
        "total": len(results),
        "by_property": by_prop,
    }


# ---------------------------------------------------------------------------
# MUTATION SENSITIVITY — the thing v2 could not do
# ---------------------------------------------------------------------------

def _mutate(src: str, old: str, new: str) -> Optional[str]:
    return src.replace(old, new, 1) if old in src else None


def mutation_sensitivity() -> List[Dict]:
    """sabotage the system in a scratch copy and confirm items go red.

    THIS IS THE EXAM TESTING ITSELF. v2 reported 15/27 and 0 of 27
    reacted to sabotage. A qualification test that cannot distinguish
    a working system from a broken one is decoration.
    """
    import shutil
    import tempfile
    import subprocess

    target = os.path.join(SRC, "constitutional", "simself.py")
    original = open(target, encoding="utf-8").read()

    mutations = [
        ("integration step x 0 (the 2026-10-06 inert bug)",
         "(self.eta * self.R * 0.5) * direction",
         "0.0 * direction"),
        ("projection removed (state escapes the ball)",
         "self.psi_current = _project_ball(\n                decayed + (self.eta * self.R * 0.5) * direction,\n                self.psi0,\n                self.R,\n            )",
         "self.psi_current = decayed + (self.eta * self.R * 0.5) * direction"),
        ("gate always allows (nothing is refused)",
         "return False, \"refuse_zero\"",
         "return True, \"allow\""),
    ]

    out: List[Dict] = []
    for label, old, new in mutations:
        mutated = _mutate(original, old, new)
        if mutated is None:
            out.append({"mutation": label, "applied": False,
                        "note": "pattern not found; source drifted"})
            continue
        tmp = tempfile.mkdtemp(prefix="atlas_v3_")
        try:
            shutil.copytree(SRC, os.path.join(tmp, "constitutional_src"),
                            ignore=shutil.ignore_patterns("__pycache__"))
            t2 = os.path.join(tmp, "constitutional_src")
            open(os.path.join(t2, "constitutional", "simself.py"), "w",
                 encoding="utf-8").write(mutated)
            env = dict(os.environ)
            env["PYTHONPATH"] = t2
            r = subprocess.run(
                [sys.executable,
                 os.path.join(t2, "constitutional", "atlas_exam_v3.py"),
                 "--run", "--quiet"],
                capture_output=True, text=True, env=env, timeout=300)
            try:
                data = json.loads(r.stdout.strip().splitlines()[-1])
                out.append({"mutation": label, "applied": True,
                            "passed": data["passed"],
                            "total": data["total"],
                            "reacted": data["passed"] < data["total"]})
            except (ValueError, IndexError):
                out.append({"mutation": label, "applied": True,
                            "error": r.stderr.strip()[-200:]})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return out


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------

def _main(argv: List[str]) -> int:
    # NOTE: filtering flags with startswith("--") before dispatch also
    # deleted the COMMANDS, which are themselves flags (--run,
    # --mutate). Only --quiet was meant to be stripped.
    quiet = "--quiet" in argv
    argv = [a for a in argv if a != "--quiet"]

    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("commands: --run | --mutate | --items")
        return 0

    if argv[0] == "--run":
        d = run_exam()
        if not quiet:
            print("=" * 68)
            print("ATLAS EXAM v3 — binary, mutation-sensitive")
            print("=" * 68)
            for r in d["results"]:
                mark = "PASS" if r["pass"] else "FAIL"
                print(f"\n  [{mark}] {r['name']}  ({r['property']})")
                print(f"         {r['detail']}")
                print(f"         does NOT establish: {r['does_not_establish']}")
            print(f"\n  {d['passed']}/{d['total']} passed")
            print("\n  by property:")
            for k, v in sorted(d["by_property"].items()):
                print(f"    {k:14} {v['pass']} pass / {v['fail']} fail")
        print(json.dumps({"passed": d["passed"], "total": d["total"]}))
        return 0 if d["passed"] == d["total"] else 1

    if argv[0] == "--mutate":
        rows = mutation_sensitivity()
        if not quiet:
            print("MUTATION SENSITIVITY — does the exam notice a broken system?")
            for r in rows:
                if not r.get("applied"):
                    print(f"  {r['mutation'][:46]:48} NOT APPLIED")
                elif "error" in r:
                    print(f"  {r['mutation'][:46]:48} ERROR {r['error'][:60]}")
                else:
                    print(f"  {r['mutation'][:46]:48} "
                          f"{r['passed']}/{r['total']} pass  "
                          f"reacted={r['reacted']}")
        print(json.dumps({"mutations": rows}))
        return 0

    if argv[0] == "--items":
        for it in build_exam():
            print(f"{it.property:14} {it.name}")
        return 0

    print(f"unknown command: {argv[0]}")
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))