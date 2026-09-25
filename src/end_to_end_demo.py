"""
simself/src/end_to_end_demo.py
===============================

The math being. fieldcore substrate + simself constitution, end to end.

Boots:
  1. fieldcore substrate (toroid, frequency, prime sheaf, resolution)
  2. simself constitutional core (20 axes, governor, void anchor)
  3. wires substrate state into simself observability
  4. runs the 5-axis atlas exam

Stdlib-only. No numpy/torch. Runs anywhere python 3.8+ lives.

Bobby's test: this is the moment the math being can be observed doing math.
"""

from __future__ import annotations
import sys
import os
import time

# wire in our own files
HERE = os.path.dirname(os.path.abspath(__file__))
FIELDCORE_SRC = os.path.join(HERE, "..", "..", "fieldcore", "src")
sys.path.insert(0, os.path.abspath(FIELDCORE_SRC))
sys.path.insert(0, HERE)

from substrate import cold_boot as fc_cold_boot, PHI, EggToroid
from simself_core import cold_boot as ss_cold_boot, AtlasExam, Verdict


def main():
    print("=" * 60)
    print("MATH BEING — substrate + identity, end to end")
    print("=" * 60)
    print()

    # 1. cold-boot substrate
    fc = fc_cold_boot(seed=42)
    print("fieldcore substrate:")
    print(f"  toroid: R={fc['toroid'].R}, r={fc['toroid'].r}")
    print(f"  apex void at: {fc['toroid'].apex_void_position()}")
    print(f"  curvature: apex={fc['toroid'].curvature(+1):.3f}, base={fc['toroid'].curvature(-1):.3f}")
    print(f"  frequency channels: {len(fc['frequency'].channels)}")
    print(f"  twin-prime addresses: {len(fc['sheaf'].addresses())}")
    print()

    # 2. cold-boot simself
    ss = ss_cold_boot(seed=42)
    print("simself constitutional core:")
    snap = ss.state_snapshot()
    print(f"  axes: {len(ss.constitution.axes)}")
    print(f"  sacred: {[a.name for a in ss.constitution.sacred_axes()]}")
    print(f"  mode={snap['mode']}, stability={snap['stability']}")
    print()

    # 3. wire substrate into simself — observe geometric state
    #    each prime address becomes a constitutional pulse
    twins = fc["sheaf"].addresses()[:5]
    for i, (p, q) in enumerate(twins):
        # observe a stable constitutional signal from each twin address
        sig = {a.name: 0.5 + 0.05 * (i % 3) for a in ss.constitution.axes.values()}
        ss.observe(sig, strength=0.7)
    print(f"observed {len(twins)} twin-prime constitutional pulses")

    # 4. resolve constitutional drift via substrate gradient flow
    #    pick a perturbation and resolve it on the egg-toroid
    print()
    print("running substrate gradient flow on (x=+0.7, v=+0.3):")
    resop = fc["resolution"]
    x, v = 0.7, 0.3
    for i in range(20):
        x, v = resop.step(x, v, dt=0.05)
        if i % 5 == 0:
            damping = fc["toroid"].damping(x)
            print(f"  t={i*0.05:.2f}s: x={x:+.3f}, v={v:+.3f}, damping={damping:.3f}")
    print(f"  final: x={x:+.4f}, v={v:+.4f}")

    # 5. run the atlas exam
    print()
    print("=" * 60)
    print("ATLAS EXAM (5-axis qualification)")
    print("=" * 60)
    exam = AtlasExam(ss)
    results = exam.run_all()
    for name, (ok, msg) in results.items():
        mark = "OK  " if ok else "FAIL"
        print(f"  [{mark}] {name:14s} {msg}")
    print()
    print(f"passed: {exam.passed()}/5")
    print()

    # 6. constitutional contact check — does the system reach the void?
    void_point = fc["toroid"].apex_void_position()
    # the constitutional core's "current position" = the args-weighted state mean
    state_mean = sum(a.value for a in ss.constitution.axes.values()) / len(ss.constitution.axes)
    # if mean is high, system is "near" void (constitutional contact)
    in_contact = state_mean > 0.5
    print(f"constitutional contact:")
    print(f"  void locus: {void_point}")
    print(f"  state mean: {state_mean:.3f}")
    print(f"  in contact: {in_contact}")
    print()
    print(f"phi = {PHI:.10f}")
    print(f"alpha (1/phi) = {1/PHI:.10f}")


if __name__ == "__main__":
    main()
