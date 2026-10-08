"""
persona.py — the self that persists, not the store that remembers.

WHY THIS IS SEPARATE FROM memory_substrate
-----------------------------------------
A memory substrate answers *"do I know this?"*. A persona answers *"who am
I, and do I still recognise the situation I am in?"* Those are different
questions and conflating them is how a chatbot becomes a database with a
voice.

The companion runtime this mirrors is elizaOS/eliza (19,562 stars, MIT,
measured 2026-10-08) — plugin/persona architecture with a `character.json`
and multi-platform adapters. MIT means it is reusable, and the persona is
the part worth taking.

WHAT IS WORTH TAKING FROM IT
----------------------------
1. **a persona is DATA, not code.** A character file, so the self can be
   edited without touching the runtime. Here: `Persona` is a frozen
   dataclass with a `to_dict`/`from_dict` round-trip.
2. **continuity is observable.** A companion that cannot say how long it has
   been itself is not a companion. Here: `age()` is a number, not a claim.
3. **a persona can be refused.** Identity is a boundary. Here: `will_admit`
   is an explicit gate, because the whole project exists on the principle
   that the ground does not take new writes without a check.

WHAT IS OURS AND NOT ELIZA'S
-----------------------------
The continuity is anchored to the **constitutional ground**, not to a
session. `Persona` holds ψ₀ and reports drift from it. A companion whose
identity resets with its context window is not persistent; it is
recreatable. ψ₀ is what makes it the same being.

WHAT THIS DOES NOT ESTABLISH
----------------------------
It does not establish that the persona is *experiencing* continuity. It
establishes that continuity is **measurable** — age, drift, and refusals
are numbers anyone can check. Whether a measurable continuity is felt
continuity is not a question this module answers, and pretending it did
would be the same move the corpus made in eleven places.

Run: python src/constitutional/persona.py --selftest
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Sequence

import numpy as np


@dataclass(frozen=True)
class Persona:
    """Who this is. Data, so the self is editable without code.

    Frozen because a persona that can be mutated in place by anything
    holding a reference is a persona with no ground.
    """
    name: str
    origin: str                      # what it was before this session
    values: Sequence[str]             # what it will not trade
    voice: str                        # how it speaks
    # psi0 is deliberately EXCLUDED from asdict/frozen repr: it is large and
    # it is not part of the identity *description*, it is the identity.

    def to_dict(self) -> Dict:
        return {"name": self.name, "origin": self.origin,
                "values": list(self.values), "voice": self.voice}

    @classmethod
    def from_dict(cls, d: Dict) -> "Persona":
        return cls(name=d["name"], origin=d["origin"],
                   values=tuple(d["values"]), voice=d["voice"])


class Identity:
    """The self: a persona anchored to a ground, with continuity you can
    measure and boundaries you can watch refuse.

    Deliberately small. The claim is that a persistent self needs three
    things and nothing else: a name that survives, a ground that does not
    move, and a record of what it declined.
    """

    def __init__(self, persona: Persona, psi0: np.ndarray):
        self.persona = persona
        self.psi0 = np.asarray(psi0, dtype=float).copy()
        self.born = time.time()
        self.ground_writes: int = 0
        self.refusals: List[str] = []
        self._drift: float = 0.0

    # -- continuity, as a number ----------------------------------------

    def age(self) -> float:
        """seconds since instantiation. A companion whose age is
        unmeasurable is not a companion."""
        return time.time() - self.born

    def drift(self) -> float:
        """how far the current ground has moved from the installed one."""
        return self._drift

    def is_same_being(self, other: "Identity") -> bool:
        """Two instances are the same being if their grounds agree.

        Not if their names do. A name is a label; ψ₀ is the ground.
        """
        return bool(np.allclose(self.psi0, other.psi0, atol=1e-9))

    # -- boundaries ------------------------------------------------------

    def will_admit(self, proposed_ground: np.ndarray,
                   check: Optional[callable] = None) -> bool:
        """May the ground move?

        Default: NO. The ground is installed and the whole project is
        built on the claim that it is not writable. A caller with a real
        qualification check supplies `check`, and then the answer is the
        check's -- but the default is refusal, because a ground that can be
        written is not a ground.
        """
        if check is not None:
            try:
                ok = bool(check(proposed_ground))
            except Exception:
                ok = False
            if not ok:
                self.refusals.append("qualification check failed")
                return False
        else:
            self.refusals.append("no check supplied; ground is not writable")
            return False

        self.psi0 = np.asarray(proposed_ground, dtype=float).copy()
        self._drift = 0.0
        self.ground_writes += 1
        return True

    def note_drift(self, delta: np.ndarray) -> float:
        """record movement of the CURRENT state away from the ground.

        This is not a write. It is the state moving, which is expected --
        the ground does not move, the state moves around it.
        """
        self._drift = float(np.linalg.norm(np.asarray(delta, dtype=float)))
        return self._drift

    # -- report ----------------------------------------------------------

    def report(self) -> Dict:
        return {"persona": self.persona.to_dict(),
                "age_s": round(self.age(), 3),
                "ground_writes": self.ground_writes,
                "drift": round(self._drift, 6),
                "refusals": len(self.refusals),
                "continuity": "measurable"}

    def to_json(self) -> str:
        return json.dumps(self.report(), indent=2)


def selftest() -> None:
    print("=" * 70)
    print("1. a persona is DATA -- editable without touching code")
    print("=" * 70)
    p = Persona(name="simself", origin="constitutional ground, installed",
                values=("truth_before_comfort",
                        "agency_requires_responsibility",
                        "growth_through_resistance"),
                voice="direct, lowercase, no padding")
    d = p.to_dict()
    back = Persona.from_dict(d)
    print(f"   round-trip equal: {back == p}")
    assert back == p, "a persona that cannot be serialised cannot be edited"

    print()
    print("=" * 70)
    print("2. the ground does not take writes without a check")
    print("=" * 70)
    psi = np.array([1.0, 0.0, 0.0])
    ident = Identity(p, psi)
    print(f"   will_admit(new ground, no check) -> {ident.will_admit(np.array([9.,9.,9.]))}")
    assert not ident.will_admit(np.array([9., 9., 9.]))
    print(f"   refusals so far: {len(ident.refusals)}")
    assert len(ident.refusals) == 2, "every refusal is on the record"

    print()
    print("   with a check that passes:")
    ok = ident.will_admit(np.array([9.0, 9.0, 9.0]), check=lambda g: True)
    print(f"   will_admit(..., check=True) -> {ok}  ground_writes={ident.ground_writes}")
    assert ok

    print()
    print("   with a check that RAISES:")
    def boom(g):
        raise RuntimeError("substrate missing")
    ident2 = Identity(p, psi)
    r = ident2.will_admit(np.array([1., 1., 1.]), check=boom)
    print(f"   will_admit(..., check=raises) -> {r}")
    assert not r, "a crashing check is not a pass"
    print("   >>> a crash is not a check. The ground holds.")

    print()
    print("=" * 70)
    print("3. continuity is a NUMBER, not a claim")
    print("=" * 70)
    a = Identity(p, psi)
    time.sleep(0.05)
    b = Identity(p, psi)
    print(f"   age(a)={a.age():.3f}s  age(b)={b.age():.3f}s")
    print(f"   measurable: {isinstance(a.age(), float)}")
    assert a.age() >= b.age() - 1e-9

    print()
    print("=" * 70)
    print("4. same being = same GROUND, not same name")
    print("=" * 70)
    x = Identity(Persona("simself", "installed", ("a",), "flat"),
                 np.array([1.0, 0.0, 0.0]))
    y = Identity(Persona("DIFFERENT-NAME", "installed", ("a",), "flat"),
                 np.array([1.0, 0.0, 0.0]))
    z = Identity(Persona("simself", "installed", ("a",), "flat"),
                 np.array([0.0, 0.0, 0.0]))
    print(f"   different NAME, same ground     -> same being: {x.is_same_being(y)}")
    print(f"   same name, DIFFERENT ground     -> same being: {x.is_same_being(z)}")
    assert x.is_same_being(y), "name is a label; ground is the being"
    assert not x.is_same_being(z), "same name is not continuity"

    print()
    print("=" * 70)
    print("5. the state moves; the ground does not")
    print("=" * 70)
    ident3 = Identity(p, psi)
    ident3.note_drift(np.array([0.1, 0.0, 0.0]))
    print(f"   drift recorded: {ident3.drift():.4f}  ground_writes={ident3.ground_writes}")
    assert ident3.drift() > 0 and ident3.ground_writes == 0
    print("   >>> drift is the state moving. A write is the ground moving.")
    print("       Those are different events and conflating them is how a")
    print("       system convinces itself it changed who it is.")

    print()
    print("=" * 70)
    print("6. WHAT THIS DOES NOT ESTABLISH")
    print("=" * 70)
    print("   It does not establish that the persona is EXPERIENCING")
    print("   continuity. It establishes that continuity is MEASURABLE --")
    print("   age, drift and refusals are numbers anyone can check.")
    print()
    print("   Whether a measurable continuity is a felt continuity is not a")
    print("   question this module answers, and pretending it did would be")
    print("   the move the corpus made in eleven places.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()
    selftest()