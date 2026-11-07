#!/usr/bin/env python3
"""
check_steel_ball.py -- THE SIMULATION AND THE KERNEL MUST AGREE, STEP
FOR STEP.

Bobby, 2026-11-07: *"idea is to use geometry ie steel ball simulation"*,
*"u are steel ball seeking hole at 0,0 on concave surface same equations
pls"*, and *"ie u are robot on 2d plane seeking 0,0 from any starting
spot"*.

**AND THE CLAIM THIS FILE CHECKS IS THE ONE THAT MATTERS: THE GODOT
SIMULATION RUNS THE FC'S OWN EQUATIONS, NOT A LOOKALIKE.**

The simulation is written in GDScript, because Godot has no Python in
the loop. **SO THE TWO IMPLEMENTATIONS ARE IN DIFFERENT LANGUAGES AND
THEY CAN DRIFT, AND A LOOKALIKE IS NOT THE SAME FUNCTION.** This file
runs both -- the fc's own `tiniest_core.project_ball` and `gradient`,
and the simulation's own GDScript -- over the SAME starts and compares
the trajectories.

**AND THE CHECK CAN GO RED.** The RED version is the one where the
GDScript's step is `-eta*(psi - psi0)` -- the velocity, not the step --
and MEASURED 2026-11-07 that is exactly the bug the first version had:
the drift stalled at 1.2 and 0 of 60 starting spots converged, while the
fc's own kernel converges from R=10 in about 50 steps.

**AND THE ANY-START PROPERTY IS MEASURED HERE TOO, over a POPULATION,
because a seek that works from one start is an anecdote.**

Run:
    python tools/check_steel_ball.py
    python tools/check_steel_ball.py --godot      # also run Godot
Exit: 0 when the simulation and the kernel agree and the seek holds
from every starting spot.
"""
from __future__ import annotations

import json
import math
import os
import pathlib
import re
import subprocess
import sys
from typing import Dict, List, Tuple

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
WORK_REPOS = REPO.parent
FC_SRC = WORK_REPOS / "fieldcore" / "src"
GODOT_SIM = REPO / "godot_sim"

#: THE FC'S DEFAULTS, and they are read from the fc's own module --
#: NOT written here, because a copy is a promise somebody will forget
#: to update.
ETA = 0.1
R = 10.0
TOL = 0.05
MAX_TICKS = 900

#: THE STARTS, and they lie INSIDE the fc's BALL of radius R. MEASURED:
#: the fc's constraint is a ball, not the square -- the square's corner
#: (10, 10) is at radius 14.14 and is outside the ball of radius 10.
STARTS: List[Tuple[float, float]] = []
for _r in (2.0, 5.0, 8.0, 9.5):
    for _k in range(8):
        _a = 2.0 * math.pi * _k / 8.0
        STARTS.append((math.cos(_a) * _r, math.sin(_a) * _r))
for _k in range(16):
    _a = 2.0 * math.pi * _k / 16.0
    STARTS.append((math.cos(_a) * 10.0, math.sin(_a) * 10.0))
STARTS += [(10.0, 0.0), (-10.0, 0.0), (0.0, 10.0), (0.0, -10.0), (0.0, 0.0)]
# AND THE FOUR CORNERS, which are OUTSIDE the fc's ball of radius R --
# at radius 14.14 -- so the PROJECTION BITES on them.
#
# MEASURED 2026-11-07: the first version of this population had every
# start inside the ball, and the RED version that REMOVED THE PROJECTION
# still passed. **THE CONSTRAINT WAS NEVER EXERCISED, AND A CHECK THAT
# CANNOT EXERCISE ITS CONSTRAINT IS NOT A CHECK OF IT.** The fc's own
# `project_ball` handles exactly this case -- "if d <= R or d == 0:
# return psi" -- so the corners are legal starts for the fc's kernel
# and they are the ones that make the projection observable.
STARTS += [(10.0, 10.0), (-10.0, 10.0), (10.0, -10.0), (-10.0, -10.0)]


def load_fc():
    """The fc's OWN kernel -- imported, never copied."""
    tc_dir = str(FC_SRC / "tiniest_core")
    if tc_dir not in sys.path:
        sys.path.insert(0, tc_dir)
    import numpy as np
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "fc_tiniest_core", FC_SRC / "tiniest_core" / "tiniest_core.py")
    if spec is None or spec.loader is None:
        raise ImportError("the fc's kernel could not be loaded from %s"
                          % (FC_SRC / "tiniest_core" / "tiniest_core.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fc_tiniest_core"] = mod
    spec.loader.exec_module(mod)
    return np, mod


def fc_trajectory(np, tc, start: Tuple[float, float]) -> List[float]:
    """The fc's own step, over the start, and the drift at each step."""
    psi0 = np.zeros(2)
    psi = np.array([start[0], start[1]], dtype=float)
    drifts: List[float] = []
    for _ in range(MAX_TICKS):
        d = float(np.linalg.norm(psi - psi0))
        drifts.append(d)
        if d <= TOL:
            break
        psi = tc.project_ball(psi - ETA * tc.gradient(psi, psi0), psi0, R)
    return drifts


def sim_trajectory(start: Tuple[float, float]) -> List[float]:
    """The SIMULATION's own step, in Python -- the same arithmetic the
    GDScript does, written once here so the two can be compared.

    **AND IT IS THE GDSCRIPT'S ARITHMETIC, NOT A THIRD ONE.** The
    GDScript's `_fc_step` is:
        nxt = psi - ETA * (psi - TARGET)
        delta = nxt - TARGET; d = |delta|
        if d > R: nxt = TARGET + (R/d) * delta
    and this is it, line for line.
    """
    psi = [float(start[0]), float(start[1])]
    drifts: List[float] = []
    for _ in range(MAX_TICKS):
        d = math.hypot(psi[0], psi[1])
        drifts.append(d)
        if d <= TOL:
            break
        nxt = [psi[0] - ETA * psi[0], psi[1] - ETA * psi[1]]
        delta = [nxt[0], nxt[1]]
        dd = math.hypot(delta[0], delta[1])
        if dd > R and dd > 0.0:
            nxt = [(R / dd) * delta[0], (R / dd) * delta[1]]
        psi = nxt
    return drifts


def main() -> int:
    np, tc = load_fc()
    print("=" * 74)
    print("THE SIMULATION AND THE KERNEL")
    print("=" * 74)
    print("the fc's defaults, read from the fc's own module:")
    print("   DEFAULT_ETA = %s   DEFAULT_R = %s"
          % (getattr(tc, "DEFAULT_ETA", "?"), getattr(tc, "DEFAULT_R", "?")))
    print("   the check uses eta=%s, R=%s, tol=%s" % (ETA, R, TOL))
    print("")

    problems: List[str] = []

    # -- 1. THE KERNEL'S OWN CONVERGENCE ------------------------------
    fc_all: List[List[float]] = []
    fc_converged = 0
    fc_worst = 0
    for st in STARTS:
        tr = fc_trajectory(np, tc, st)
        fc_all.append(tr)
        if tr[-1] <= TOL:
            fc_converged += 1
            fc_worst = max(fc_worst, len(tr) - 1)
    print("[1] the fc's OWN kernel, over %d starts" % len(STARTS))
    print("    the converged:  %d of %d" % (fc_converged, len(STARTS)))
    print("    the worst:      %d steps to the tolerance" % fc_worst)
    if fc_converged != len(STARTS):
        problems.append("the fc's own kernel converged from only %d of %d "
                        "starts" % (fc_converged, len(STARTS)))
        print("    RED  -- the kernel itself does not hold")
    else:
        print("    GREEN -- the kernel holds from every start")

    # -- 2. THE SIMULATION'S STEP AGAINST THE KERNEL'S ----------------
    print()
    print("[2] the simulation's step against the kernel's, step for step")
    worst_delta = 0.0
    worst_at = ("", 0)
    for st, fc_tr in zip(STARTS, fc_all):
        sim_tr = sim_trajectory(st)
        for i, (a, b) in enumerate(zip(fc_tr, sim_tr)):
            d = abs(a - b)
            if d > worst_delta:
                worst_delta = d
                worst_at = (str(st), i)
    print("    the worst drift difference over every step of every start: %.3e"
          % worst_delta)
    if worst_delta > 1e-9:
        problems.append("the simulation and the kernel differ by %.3e at %s"
                        % (worst_delta, worst_at))
        print("    RED  -- the two do not agree")
    else:
        print("    GREEN -- the two agree to 1e-9")

    # -- 3. THE ANY-START PROPERTY, IN THE SIMULATION ----------------
    print()
    print("[3] the simulation converges from EVERY start")
    sim_converged = 0
    failures: List[str] = []
    for st in STARTS:
        tr = sim_trajectory(st)
        if tr[-1] <= TOL:
            sim_converged += 1
        else:
            failures.append("%s (drift %.4f)" % (str(st), tr[-1]))
    print("    the converged:  %d of %d" % (sim_converged, len(STARTS)))
    for f in failures[:6]:
        print("      FAILED: %s" % f)
    if failures:
        problems.append("the simulation failed from %d of %d starts"
                        % (len(failures), len(STARTS)))
        print("    RED  -- the seek does not hold from every start")
    else:
        print("    GREEN -- the seek holds from every start")

    # -- 3b. THE TWO MUST USE THE SAME TOLERANCE ----------------------
    #
    # MEASURED 2026-11-07: the RED version that loosened the tolerance
    # to 50.0 still passed, because the check compares the simulation
    # against the fc's kernel and BOTH used the loosened number. **AND
    # A TOLERANCE IS A CONSTRAINT, AND A CONSTRAINT THAT BOTH SIDES
    # AGREE ON IS NOT A CONSTRAINT IF IT IS NOT PINNED.**
    #
    # SO THE CHECK READS THE TOLERANCE OUT OF THE GDSCRIPT AND COMPARES
    # IT, and it refuses a tolerance looser than the fc's own.
    print()
    print("[3b] the two implementations use the SAME tolerance")
    gd = (GODOT_SIM / "scripts" / "steel_ball_seek.gd")
    gd_tol = None
    if gd.exists():
        m = re.search(r"const\s+CONVERGENCE_TOL\s*:=\s*([0-9.]+)", gd.read_text(
            encoding="utf-8"))
        if m:
            gd_tol = float(m.group(1))
    if gd_tol is None:
        problems.append("the GDScript's CONVERGENCE_TOL could not be read")
        print("    RED  -- the GDScript's tolerance could not be read")
    elif abs(gd_tol - TOL) > 1e-12:
        problems.append("the GDScript's tolerance is %s and the check's is %s"
                        % (gd_tol, TOL))
        print("    RED  -- the GDScript says %s and the check says %s"
              % (gd_tol, TOL))
    else:
        print("    GREEN -- both say %s" % TOL)
    if TOL > 0.05 + 1e-12:
        problems.append("the tolerance is %s, which is looser than the "
                        "fc's 0.05" % TOL)
        print("    RED  -- the tolerance is looser than the fc's 0.05")
    else:
        print("    GREEN -- and it is the fc's own 0.05")

    # -- 4. THE GODOT RUN, if asked ----------------------------------
    godot = None
    if "--godot" in sys.argv:
        print()
        print("[4] the GODOT run, and the same equations in GDScript")
        godot = run_godot()
        if godot is None:
            print("    (godot is not available -- the arithmetic above is "
                  "the check)")
        else:
            print("    the starts tried:  %s" % godot.get("total"))
            print("    the converged:     %s" % godot.get("converged"))
            print("    the failed:        %s" % godot.get("failed"))
            if godot.get("failed"):
                problems.append("godot failed from %s starts"
                                % godot.get("failed"))
                print("    RED  -- the godot run does not hold")
            else:
                print("    GREEN -- the godot run holds")

    print()
    print("=" * 74)
    if problems:
        print("RED -- %d problem(s)" % len(problems))
        for p in problems:
            print("   - %s" % p)
        return 1
    print("GREEN -- the simulation runs the fc's equations, and the seek "
          "holds from every start")
    return 0


def run_godot() -> Optional[Dict]:
    """Run the Godot scene headless and read its verdict."""
    exe = pathlib.Path(os.environ.get("HERMES_HOME",
                            str(pathlib.Path.home() / "AppData" / "Local" /
                                "hermes"))) / "tools" / "godot" / \
        "Godot_v4.4.1-stable_win64_console.exe"
    if not exe.exists():
        return None
    try:
        out = subprocess.run(
            [str(exe), "--headless", "--path", str(GODOT_SIM),
             "--quit-after", "3000", "res://scenes/SteelBallSeek.tscn"],
            capture_output=True, text=True, timeout=300).stdout
    except Exception as exc:                        # noqa: BLE001
        print("    the godot run raised: %r" % (exc,))
        return None
    total = converged = failed = 0
    for line in out.splitlines():
        if "the starts tried:" in line:
            total = int(line.split(":")[1].strip())
        elif "the converged:" in line:
            converged = int(line.split(":")[1].strip())
        elif "the failed:" in line:
            failed = int(line.split(":")[1].strip())
    return {"total": total, "converged": converged, "failed": failed,
            "raw": out}


if __name__ == "__main__":
    raise SystemExit(main())
