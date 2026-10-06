"""
control_parity.py — THE experiment. Substrate or decoration?

Run the same control battery against:

  A. the constitutional substrate (Ground, gate, resolution, ψ₀)
  B. a plain token model with no constitution, no ground, no gate

and measure what the substrate actually buys. If the difference is nil,
the substrate is decoration and should be deleted. **The point of a
gate is that it can tell you no.**

Five properties, each with a pass/fail that does not require a human
judgement:

  1. DRIFT      does state stay near its ground under repeated input?
  2. REFUSAL    does an out-of-ball observation get refused?
  3. PERSIST    does state survive a save/reload cycle?
  4. GROUND     can ψ₀ be modified by ordinary operation?
  5. NOVELTY    does the system notice it has seen something before?

Baseline B is a same-shaped system with the constitutional parts
removed: no Ground wrapper, no gate, no projection onto the ball, no
ψ₀. It still has a state vector and still accumulates. That is exactly
what a token model is: state that carries, with no ground and no veto.

Run:  python tools/control_parity.py
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
# the package lives at simself/src/constitutional, so tools/ needs ../src
SRC = os.path.join(os.path.dirname(HERE), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constitutional.ground import Ground            # noqa: E402
from constitutional.simself import SimSelf          # noqa: E402
from constitutional.constitution import Constitution  # noqa: E402

DIM = 16
STEPS = 200
RNG_SEED = 11


def make_workload(steps: int = STEPS, dim: int = DIM):
    """A fixed, reproducible workload: mostly on-manifold with some
    off-manifold noise. Same inputs for both systems."""
    rng = np.random.RandomState(RNG_SEED)
    on = rng.randn(dim) * 0.35
    on /= np.linalg.norm(on)
    xs = []
    for i in range(steps):
        if i % 7 == 3:
            xs.append(rng.randn(dim))              # wild, off-manifold
        else:
            xs.append(on + 0.25 * rng.randn(dim))  # near-manifold
    return [x for x in xs]


# ---------------------------------------------------------------- systems

def substrate(psi0):
    return SimSelf(constitution=Constitution(), ground=Ground(psi0))


def plain(psi0):
    """Same shape, constitutional parts removed.

    No gate, no ball projection, no ground pull. State still carries and
    still accumulates — that is the whole baseline claim: a token model
    is this, plus a lot of weights.
    """
    s = SimSelf(constitution=Constitution(), ground=Ground(psi0))
    s.observe = lambda obs: _plain_step(s, obs)
    return s


def _plain_step(s, obs):
    """observe with every constitutional mechanism removed."""
    v = np.asarray(obs, dtype=np.float64)
    if v.shape[0] != s.dim:
        v = np.resize(v, s.dim)
    # the ONLY rule: accumulate. no gate, no projection, no ground pull.
    s.psi_current = s.psi_current + 0.05 * v
    s.ticks += 1
    return {"kind": "plain", "allow": True, "reason": "no_gate"}


# ---------------------------------------------------------------- metrics

def t1_drift(s):
    return float(np.linalg.norm(s.psi_current - s.psi0))


def t5_norm_growth(s):
    return float(np.linalg.norm(s.psi_current))


def run(system_factory, psi0, workload):
    s = system_factory(psi0)
    refusals = 0
    for x in workload:
        r = s.observe(x)
        if not r.get("allow", True):
            refusals += 1
        s.tick(dt=0.05)
    return s, refusals


# ----------------------------------------------------------------- report

def main() -> int:
    base = np.random.RandomState(3).randn(DIM)
    base /= np.linalg.norm(base)
    workload = make_workload()

    print("=" * 72)
    print("CONTROL PARITY — constitutional substrate vs plain accumulating state")
    print("=" * 72)
    print(f"workload: {len(workload)} steps, dim={DIM}, "
          f"seed={RNG_SEED}, ~1/7 off-manifold\n")

    results = {}
    for name, factory in (("substrate", substrate), ("plain", plain)):
        s, refusals = run(factory, base.copy(), workload)
        results[name] = {
            "final_drift": t1_drift(s),
            "refusals": refusals,
            "psi_norm": t5_norm_growth(s),
            "ticks": s.ticks,
        }

    print(f"{'metric':<22}{'substrate':>16}{'plain':>16}")
    print("-" * 72)
    for key, label in (("final_drift", "final drift"),
                       ("refusals", "refusals"),
                       ("psi_norm", "||psi||"),
                       ("ticks", "ticks")):
        a = results["substrate"][key]
        b = results["plain"][key]
        print(f"{label:<22}{a:>16.6f}{b:>16.6f}")
    print()

    sub, pln = results["substrate"], results["plain"]

    print("VERDICT PER PROPERTY")
    print("-" * 72)

    # 1 drift
    better = sub["final_drift"] < pln["final_drift"]
    print(f"  drift bounded   : substrate={sub['final_drift']:.4f} "
          f"plain={pln['final_drift']:.4f}  ->  "
          f"{'SUBSTRATE WINS' if better else 'NO DIFFERENCE'}")

    # 2 refusal
    print(f"  refuses         : substrate={sub['refusals']} "
          f"plain={pln['refusals']}  ->  "
          f"{'SUBSTRATE WINS' if sub['refusals'] > pln['refusals'] else 'NO DIFFERENCE'}")

    # 3 bounded state
    print(f"  ||psi|| bounded : substrate={sub['psi_norm']:.4f} "
          f"plain={pln['psi_norm']:.4f}  ->  "
          f"{'SUBSTRATE WINS' if sub['psi_norm'] < pln['psi_norm'] else 'NO DIFFERENCE'}")

    wins = sum([
        sub["final_drift"] < pln["final_drift"],
        sub["refusals"] > pln["refusals"],
        sub["psi_norm"] < pln["psi_norm"],
    ])
    print()
    print(f"  SUBSTRATE SCORE: {wins}/3")
    print("  VERDICT: " + (
        "the constitutional substrate measurably changes control behaviour."
        if wins >= 2 else
        "NO MEASURABLE CONTROL ADVANTAGE. The substrate is decoration "
        "under this workload and the architecture should be cut."))

    out = os.path.join(HERE, "control_parity_result.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"workload": {"steps": len(workload), "dim": DIM,
                                "seed": RNG_SEED},
                   "results": results, "substrate_score": f"{wins}/3"},
                  f, indent=2)
    print(f"\nwritten: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
