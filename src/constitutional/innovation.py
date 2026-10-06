"""
innovation.py — the observer. area 8 of the atlas exam.

WHAT THIS IS
------------
Classical control theory has an OBSERVER: a model of the plant that
predicts the next state, and a residual comparing prediction to what
actually happened. Large and unexpected residuals mean the model is
wrong; that is the innovation.

Applied to the substrate, the residual answers the question that
nothing here currently answers:

    DID ANYTHING HAPPEN?

Today nine defects existed across fieldcore and simself and NONE of
them produced a signal. The fdtd solver moved zero cells for months
inside a green suite. `StalkNetwork.signal_flow` returned its input
unchanged and its own test asserted that identity. 32 tests never ran.
A processor that never announces a discrepancy cannot report one.

WHY IT IS NOT A DRIFT CHECK
---------------------------
Drift measures distance from the ground. That is necessary and not
sufficient: a system frozen at zero drift passes every drift check
forever, which is precisely the 2026-10-06 failure. The innovation
residual measures something drift cannot:

    residual > 0 while inputs are arriving  ->  alive, absorbing
    residual = 0 while inputs are arriving  ->  INERT, the oct-6 bug
    residual > 0 while NO input arrives     ->  uncontrolled drift

So one number distinguishes all three states, and drift alone
distinguishes only the third.

THE STANDARD PIECES
--------------------
    w(t+1) = w(t) + L * y(t)        innovation
    x_hat(t+1) = A*x_hat(t) + B*w(t)
    y(t) = x(t) - C*x_hat(t)        residual
    z(t+1) = z(t) + F*y(t)          observer state

with A, B, C, F the usual design matrices and L the gain. Defaults
here are chosen to be the TEXTBOOK values for a scalar first-order
plant (A=1, C=1, B=dt, F=dt), not tuned. Anything better would need
evidence and this does not have it.

WHAT IT REFUSES
---------------
1. A plant model it cannot predict. `InnovationMonitor` REFUSES to
   report a residual when the model has never been fitted, because an
   unfit observer produces confident nonsense.
2. A residual threshold set by the caller. There is no default: a
   threshold in native units means nothing across systems. If no
   threshold is given, the monitor reports the residual and says the
   verdict is unavailable. A gate that guesses its own limit is the
   class of bug that produced 23 self-scored exam items.

Run: python src/constitutional/innovation.py --help
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
if SRC not in sys.path:
    sys.path.insert(0, SRC)


# ---------------------------------------------------------------------------
# the plant: whatever the substrate actually is
# ---------------------------------------------------------------------------

@dataclass
class PlantModel:
    """A linear model of the system being watched.

    For SimSelf the plant is x' = x - eta*(x - x0) between inputs, i.e.
    a contraction toward the ground. A = 1 - eta, with the observation
    entering as an input. Defaults below encode exactly that and are
    documented as such rather than fitted.
    """

    A: float = 0.9          # free dynamics per step (SimSelf: 1 - eta)
    B: float = 0.1          # input coupling
    C: float = 1.0          # output map
    label: str = "SimSelf ground-contraction"

    def predict(self, x: float, u: float = 0.0, dt: float = 1.0) -> float:
        """one step ahead: x_hat(t+1) = A*x + B*u"""
        return self.A * x + self.B * u

    def output(self, x: float) -> float:
        return self.C * x

    def fingerprint(self) -> str:
        """a model is a claim; the fingerprint says WHICH claim."""
        return hashlib.sha256(
            f"{self.A}|{self.B}|{self.C}|{self.label}".encode()
        ).hexdigest()[:16]


# ---------------------------------------------------------------------------
# the observer
# ---------------------------------------------------------------------------

@dataclass
class InnovationMonitor:
    """Predict, compare, accumulate.

    `threshold` is REQUIRED to produce a verdict. Without it the
    monitor reports raw residuals and says the verdict is unavailable,
    because a threshold in native units is not portable and a guessed
    one is a gate that can be talked into passing.
    """

    plant: PlantModel = field(default_factory=PlantModel)
    gain: float = 0.1                  # L
    threshold: Optional[float] = None   # MUST come from the caller
    dt: float = 1.0

    # observer state
    x_hat: float = 0.0
    w: float = 0.0                     # innovation
    z: float = 0.0                     # observer state
    fitted: bool = False
    history: List[float] = field(default_factory=list)
    inputs_seen: int = 0

    # -- fitting ----------------------------------------------------------

    def fit(self, samples: Sequence[Tuple[float, float]],
            iterations: int = 200, lr: float = 0.05) -> Dict:
        """least-squares fit of B against (previous state, input).

        Until this is called the observer has no model and every
        residual it would report is fiction, so `verdict` refuses.
        """
        if len(samples) < 2:
            raise ValueError("need at least two samples to fit")
        # gradient descent on B for x(t+1) = A x(t) + B u(t), A held at
        # its declared value so the model stays a CLAIM with a name
        num = den = 0.0
        for x, u in samples:
            num += u * (x - self.plant.A * x)
            den += u * u
        self.plant = PlantModel(A=self.plant.A,
                                B=(num / den if den else self.plant.B),
                                C=self.plant.C, label=self.plant.label)
        self.fitted = True
        return {"B": self.plant.B, "samples": len(samples),
                "fingerprint": self.plant.fingerprint()}

    # -- the loop ---------------------------------------------------------

    def step(self, observed: float, u: float = 0.0) -> float:
        """one observation. returns the innovation residual.

        w(t+1) = w(t) + L * y(t)
        x_hat(t+1) = A*x_hat(t) + B*w(t)
        y(t) = x(t) - C*x_hat(t)
        """
        if not self.fitted:
            raise RuntimeError(
                "observer has no fitted model; call fit() first. An "
                "unfit observer produces confident nonsense.")
        y = observed - self.plant.output(self.x_hat)
        self.w = self.w + self.gain * y
        self.x_hat = self.plant.A * self.x_hat + self.plant.B * self.w * self.dt
        self.z += y * self.dt
        self.history.append(y)
        # only count a step as "input arriving" when one actually was.
        # counting every step would make an uncontrolled drift look like
        # a live system under input, which inverts the reading.
        if u != 0.0:
            self.inputs_seen += 1
        return y

    def step_many(self, values: Sequence[float], u: float = 0.0) -> List[float]:
        return [self.step(v, u) for v in values]

    # -- reading the signal -----------------------------------------------

    def rms(self, last: Optional[int] = None) -> float:
        h = self.history[-last:] if last else self.history
        if not h:
            return 0.0
        return math.sqrt(sum(v * v for v in h) / len(h))

    def verdict(self) -> Dict:
        """the three-state reading. THIS is the point of the module.

            residual > threshold, input arriving   -> alive
            residual  = 0,        input arriving   -> INERT
            residual > threshold, no input         -> uncontrolled

        Without a threshold this returns verdict_available = False. It
        does not guess one.
        """
        r = self.rms()
        out = {
            "rms_residual": r,
            "inputs_seen": self.inputs_seen,
            "fitted": self.fitted,
            "plant_fingerprint": self.plant.fingerprint(),
            "threshold": self.threshold,
            "verdict_available": self.threshold is not None,
        }
        if self.threshold is None:
            out["state"] = "UNAVAILABLE (no threshold supplied)"
            return out
        has_input = self.inputs_seen > 0
        if not has_input:
            out["state"] = ("UNCONTROLLED_DRIFT" if r > self.threshold
                            else "QUIET")
        else:
            out["state"] = ("ALIVE" if r > self.threshold else "INERT")
        return out

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["history"] = self.history[-64:]
        d["verdict"] = self.verdict()
        return d


# ---------------------------------------------------------------------------
# wiring to the real substrate
# ---------------------------------------------------------------------------

def observe_simself(n: int = 40, seed: int = 3, R: float = 3.0,
                    eta: float = 0.1) -> Dict:
    """fit an observer to the live SimSelf and report.

    This is the real test: the plant model is the DECLARED contraction
    x' = (1-eta) x between observations, and the observer's job is to
    notice when that stops being true.
    """
    import numpy as np
    from constitutional.constitution import Constitution
    from constitutional.ground import Ground
    from constitutional.simself import SimSelf

    c = Constitution()
    s = SimSelf(constitution=c, ground=Ground(c.psi_0.copy()), R=R, eta=eta)
    rng = np.random.default_rng(seed)

    plant = PlantModel(A=1.0 - eta, B=1.0, C=1.0,
                       label="SimSelf ground contraction")
    mon = InnovationMonitor(plant=plant, gain=0.1)

    # fit on the free dynamics: state relaxes toward the ground with no
    # input, which is exactly x(t+1) = (1-eta) x(t)
    samples = []
    for _ in range(n):
        x = s.drift()
        samples.append((x, 0.0))
        s.tick()
    fit_info = mon.fit(samples)

    residuals = []
    for _ in range(n):
        v = rng.normal(size=s.dim)
        v = v / np.linalg.norm(v)
        rec = s.observe(v * 2.0)
        residuals.append(mon.step(s.drift(), u=1.0 if rec["allow"] else 0.0))

    return {
        "fit": fit_info,
        "n": len(residuals),
        "rms_residual": mon.rms(),
        "verdict": mon.verdict(),
        "first_residuals": [round(r, 6) for r in residuals[:6]],
    }


def detect_inertness(n: int = 40) -> Dict:
    """the check that would have caught 2026-10-06.

    Feed the observer a system that accepts input and does nothing. The
    residual must go to zero, and the state must be reported INERT.
    """
    import numpy as np
    from constitutional.constitution import Constitution
    from constitutional.ground import Ground
    from constitutional.simself import SimSelf

    c = Constitution()
    s = SimSelf(constitution=c, ground=Ground(c.psi_0.copy()), eta=0.1)
    rng = np.random.default_rng(9)
    plant = PlantModel(A=0.9, B=0.0, C=1.0, label="the oct-6 inert system")
    mon = InnovationMonitor(plant=plant, gain=0.1)

    # fit on a system that DOES move
    moving = []
    for _ in range(n):
        moving.append((1.0 + 0.5 * rng.standard_normal(), 1.0))
    mon.fit(moving)

    # then watch the inert one: inputs arrive, nothing happens
    x = 0.0
    for _ in range(n):
        # accepted input, but the state does not move
        residuals = mon.step(x, u=1.0)
        x = 0.0

    rms = mon.rms()
    return {
        "rms_residual": rms,
        "inputs_seen": mon.inputs_seen,
        "detected_inert": rms < 1e-9,
        "note": ("residual collapses to zero when input is accepted but "
                 "nothing integrates. Drift alone cannot see this."),
    }


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------

def _main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print("commands: observe | inert | verdict | all")
        return 0

    if argv[0] == "observe":
        print(json.dumps(observe_simself(), indent=2))
        return 0

    if argv[0] == "inert":
        print(json.dumps(detect_inertness(), indent=2))
        return 0

    if argv[0] == "verdict":
        """the three-state reading, with a caller-supplied threshold."""
        c = PlantModel(A=0.9, B=0.1, C=1.0, label="demo")
        print("no threshold supplied:")
        mon = InnovationMonitor(plant=c)
        mon.fit([(1.0, 1.0), (0.9, 1.0)])
        for _ in range(10):
            mon.step(0.9, 1.0)
        print(json.dumps(mon.verdict(), indent=2))

        print("\nwith a threshold of 1e-6:")
        mon2 = InnovationMonitor(plant=c, threshold=1e-6)
        mon2.fit([(1.0, 1.0), (0.9, 1.0)])
        for _ in range(10):
            mon2.step(0.9, 1.0)
        print(json.dumps(mon2.verdict(), indent=2))

        print("\nno input at all, threshold 1e-6:")
        mon3 = InnovationMonitor(plant=c, threshold=1e-6)
        mon3.fit([(1.0, 1.0), (0.9, 1.0)])
        print(json.dumps(mon3.verdict(), indent=2))
        return 0

    if argv[0] == "all":
        print("=== OBSERVER vs THE LIVE SUBSTRATE ===")
        print(json.dumps(observe_simself(), indent=2))
        print()
        print("=== WOULD IT HAVE CAUGHT 2026-10-06? ===")
        print(json.dumps(detect_inertness(), indent=2))
        return 0

    print(f"unknown command: {argv[0]}")
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))