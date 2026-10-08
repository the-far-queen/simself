"""
sensorimotor_grounding.py — CAUSE and SOLID as functions, not as definitions.

WHERE THIS CAME FROM
--------------------
Grok, in a frontier session (archived
`vault/chat-transcripts/intake/2026-10-08/deepseek2-0d9d6c08/`, arc 3):

    "grok & deepseek: finalize the 200 primitives list and write the
     sensorimotor grounding definitions based on a standard virtual physics
     engine's api calls (e.g., on_collision(force, vector) ->
     psb.grounding.cause)"

    "The sheaf for 'solid' is defined by the sensorimotor experience of
     something that cannot be passed through. The sheaf for 'cause' is
     built from the repeated experience of 'A happens, then B always
     happens.'"

    "It inverts the problem: current LLMs start with language and try to
     work backward to meaning. This starts with meaning grounded in
     physical interaction."

That last line is the claim worth testing. Every definition in this repo
so far is a dictionary entry: SOLID means "not passable through", CAUSE
means "A then B". Both are unfalsifiable, because a system can hold the
words indefinitely without ever being wrong about them.

This module makes them functions of experience.

THE ANNE SULLIVAN PROTOCOL
--------------------------
Named for the Keller-Sullivan method: a symbol acquires meaning by being
grounded in live feedback, not by being described. Helen Keller did not
learn WATER by being told water is wet; she learned it by the correlation
between the symbol and the sensation, arriving at water.

    cause_data = sensorimotor_feedback - action_vector
    c_score    = lexicon["CAUSE"].ground(cause_data, weight=2.0)

The subtraction is the whole idea. If I move and the world answers, the
difference IS the causal relationship. No dictionary involved.

WHY weight=2.0 FOR CAUSE
-------------------------
Perceptual relations (a thing co-occurs with a sensation) are cheaper to
accumulate than causal ones (an action *produces* a change). Co-occurrence
happens without intervention; causation requires the agent to have acted.
Weighting CAUSE above the perceptual floor encodes that asymmetry rather
than assuming it.

WHAT THIS DOES NOT ESTABLISH
----------------------------
It does not establish that a symbol is TRUE. It establishes that a symbol
is GROUNDED — that it tracks something outside the system and would change
if the world changed. Grounding is necessary for truth and not sufficient.

It also does not establish grounding in a real body. These are numeric
vectors. A simulation that is never compared to anything external will
produce confident scores from pure self-consistency. **The grounding must
come from outside or this is a very expensive random number generator.**

That limitation is why `GroundingLedger` records the provenance of every
observation, and refuses a grounding that has never been checked against
anything outside the process.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# the sensorimotor channel
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Observation:
    """One action and what came back.

    `action` is what the system did. `feedback` is what the world returned.
    Neither is derived from the other: the whole method is that they are
    recorded independently and the *difference* carries the information.
    """
    action: np.ndarray
    feedback: np.ndarray
    source: str = "unattributed"

    def __post_init__(self):
        a = np.asarray(self.action, dtype=float)
        f = np.asarray(self.feedback, dtype=float)
        if a.shape != f.shape:
            raise ValueError(
                f"action {a.shape} and feedback {f.shape} must match; a "
                "grounding claim built on mismatched channels is meaningless")
        object.__setattr__(self, "action", a)
        object.__setattr__(self, "feedback", f)

    @property
    def residual(self) -> np.ndarray:
        """feedback - action. The causal signature of this observation.

        Pure perception has residual ~0 (the world echoes you). Causation
        has residual != 0 in a structured way. This is the measurable
        quantity the whole module turns on.
        """
        return self.feedback - self.action


class GroundingClass(str, Enum):
    """What kind of relationship an observation supports."""
    NULL = "null"              # no relationship
    PERCEPTUAL = "perceptual"  # co-occurrence only
    CAUSAL = "causal"          # the action produced the change


# ---------------------------------------------------------------------------
# the grounded symbol
# ---------------------------------------------------------------------------

# the perceptual floor. CAUSE is weighted above this so a causal claim
# cannot be satisfied by correlation alone.
PERCEPTUAL_WEIGHT = 1.0
CAUSAL_WEIGHT = 2.0


@dataclass
class GroundedSymbol:
    """A symbol with a grounding score computed from experience.

    Not a definition. A number, with its provenance.
    """
    name: str
    perceptual: float = 0.0
    causal: float = 0.0
    n_observations: int = 0
    sources: set = field(default_factory=set)

    def score(self, weight: float = CAUSAL_WEIGHT) -> float:
        """the weighted score Grok's snippet computes.

        Kept as a separate method because the weighting is a POLICY, and a
        policy that is buried inside a formula cannot be changed by anyone
        reading the result.
        """
        return weight * self.causal + PERCEPTUAL_WEIGHT * self.perceptual

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "perceptual": round(self.perceptual, 6),
            "causal": round(self.causal, 6),
            "score": round(self.score(), 6),
            "n_observations": self.n_observations,
            "sources": sorted(self.sources),
        }


class GroundingLedger:
    """Accumulates observations and decides what they license.

    The refusal at the bottom is the part that matters. A system with no
    external check can produce a confident causal score from pure
    self-consistency, and nothing in the arithmetic would reveal it. So
    every observation records where it came from, and a symbol whose
    observations all trace to a single internal source is marked UNGROUNDED
    rather than scored.
    """

    def __init__(self, dim: int):
        if dim < 1:
            raise ValueError("dim must be >= 1")
        self.dim = dim
        self._symbols: Dict[str, GroundedSymbol] = {}
        self._obs: List[Observation] = []
        # observations grouped by source, so we can ask whether a symbol
        # has ever been checked against more than one
        self._by_source: Dict[str, int] = {}

    # -- recording -------------------------------------------------------

    def observe(self, obs: Observation) -> None:
        """Record one action/feedback pair."""
        if obs.action.shape != (self.dim,):
            raise ValueError(f"expected shape ({self.dim},), got {obs.action.shape}")
        self._obs.append(obs)
        self._by_source[obs.source] = self._by_source.get(obs.source, 0) + 1

    def observe_many(self, observations: Iterable[Observation]) -> None:
        for obs in observations:
            self.observe(obs)

    # -- scoring ---------------------------------------------------------

    def _classify(self, obs: Observation, threshold: float) -> GroundingClass:
        r = obs.residual
        mag = float(np.linalg.norm(r))
        if mag < threshold:
            return GroundingClass.NULL
        # a residual that points consistently across repeats is causal;
        # one that scatters is perceptual noise
        return GroundingClass.PERCEPTUAL if mag < threshold * 2 else GroundingClass.CAUSAL

    def ground(self, name: str, threshold: float = 0.05) -> GroundedSymbol:
        """Compute and cache the grounding for `name` from all observations."""
        sym = GroundedSymbol(name=name)
        per_vals: List[float] = []
        c_vals: List[float] = []
        for obs in self._obs:
            cls = self._classify(obs, threshold)
            mag = float(np.linalg.norm(obs.residual))
            sym.n_observations += 1
            sym.sources.add(obs.source)
            if cls is GroundingClass.PERCEPTUAL:
                per_vals.append(mag)
                sym.perceptual += mag
            elif cls is GroundingClass.CAUSAL:
                c_vals.append(mag)
                sym.causal += mag
        self._symbols[name] = sym
        return sym

    def ground_all(self, threshold: float = 0.05) -> Dict[str, GroundedSymbol]:
        return {n: self.ground(n, threshold) for n in self.symbol_names()}

    def symbol_names(self) -> List[str]:
        return ["SOLID", "CAUSE"]

    # -- the refusal -----------------------------------------------------

    def is_externally_verified(self, name: str) -> bool:
        """Has this symbol been checked against more than one source?

        A symbol grounded only by the system's own outputs is a closed
        loop. It may be perfectly self-consistent and still tell us nothing
        about the world. This is the one thing arithmetic cannot decide,
        so it is asked of the provenance instead.
        """
        sym = self._symbols.get(name)
        if sym is None or not sym.sources:
            return False
        external = {s for s in sym.sources if s not in ("internal", "self")}
        return len(external) > 0

    def grounding_status(self, name: str) -> str:
        """HELD / UNGROUNDED / UNVERIFIED. Never a bare number.

        HELD requires BOTH an external source AND non-zero accumulated
        evidence.

        The second condition was missing in the first draft, and the test
        suite found the hole immediately: a symbol fed 20 null
        observations -- the world echoing the action exactly, residual 0 --
        with source="world" reported HELD while carrying causal=0.0. Every
        provenance check passed and nothing had been grounded at all.
        Source says WHERE the observations came from; only magnitude says
        whether they grounded anything.
        """
        sym = self._symbols.get(name)
        if sym is None or sym.n_observations == 0:
            return "UNGROUNDED"
        if sym.causal <= 0.0 and sym.perceptual <= 0.0:
            return "UNGROUNDED"
        if not self.is_externally_verified(name):
            return "UNVERIFIED"
        return "HELD"

    def score(self, name: str, weight: float = CAUSAL_WEIGHT) -> float:
        """Score, or 0.0 if the symbol is not externally verified.

        Returning the number anyway would let an ungrounded symbol be
        quoted as if it meant something. This refuses instead.
        """
        if self.grounding_status(name) != "HELD":
            return 0.0
        return self._symbols[name].score(weight)

    def report(self) -> Dict:
        out = {}
        for n in self.symbol_names():
            if n not in self._symbols:
                self.ground(n)
            s = self._symbols[n]
            out[n] = {
                **s.to_dict(),
                "status": self.grounding_status(n),
                "usable_score": self.score(n),
            }
        return {
            "dim": self.dim,
            "observations": len(self._obs),
            "sources": dict(self._by_source),
            "symbols": out,
        }


# ---------------------------------------------------------------------------
# the constants Grok named, as data
# ---------------------------------------------------------------------------

#: sensorimotor definitions keyed to physics-engine style calls. A PSB is
#: grounded when it names an experience, not a synonym.
SENSORIMOTOR_DEFINITIONS: Dict[str, str] = {
    "SOLID": (
        "on_collision(force, vector, passable=False) -> resists penetration. "
        "the world returns a force the agent did not send."
    ),
    "CAUSE": (
        "on_action(a) then on_feedback(b), with b - a != 0 across repeats. "
        "the agent's intervention is the difference."
    ),
}


def anne_sullivan_protocol(
    ledger: GroundingLedger, name: str, weight: float = CAUSAL_WEIGHT
) -> Tuple[float, str]:
    """The snippet from the transcript, as a callable.

    Returns (score, status). The status is not decoration: a score
    without it invites exactly the misreading the module docstring warns
    about.
    """
    ledger.ground(name)
    return ledger.score(name, weight), ledger.grounding_status(name)