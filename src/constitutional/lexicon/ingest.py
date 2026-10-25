"""
ingest.py — geodesic lexicon write path.

Per Grok sharpen 2026-09-16 (applied by Hermes). Ported from
`fieldcore/docs/chat-transcripts/grok/05-part2-substrate-and-lexicon-with-ingest-code-2026-09-16.md`
(Desktop/Grok/md/05-...md).

This is the ONLY write path for language in the shell. The generator may propose
a span; ingest embeds, costs, and either stores a unit or returns a refusal. No
other function marks admitted or committed.

If tool ingest and language ingest use different checks (i.e. harness/gate.py and
this gate_m0 diverge), the policy has already split.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional, Tuple

import numpy as np


class Status(str, Enum):
    CANDIDATE = "candidate"
    ADMITTED = "admitted"
    COMMITTED = "committed"
    REFUSED = "refused"


class UnitType(str, Enum):
    ACT = "act"
    REFUSE = "refuse"
    NAME = "name"
    COMMIT = "commit"
    TIME = "time"
    OBJECT = "object"
    OTHER = "other"


@dataclass
class Unit:
    id: str
    span: str
    utype: UnitType
    embedding: np.ndarray
    status: Status = Status.CANDIDATE
    support: List[str] = field(default_factory=list)


@dataclass
class Verdict:
    allow: bool
    reason: str
    cost_ground: float
    cost_nearest: float
    nearest_id: Optional[str]
    drift_before: float
    drift_after: float


EmbedFn = Callable[[str], np.ndarray]
TypeFn = Callable[[str], UnitType]


def dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def cost_pair(
    a: np.ndarray,
    b: np.ndarray,
    psi0: np.ndarray,
    radius: float,
    b_status: Status,
) -> float:
    if b_status == Status.REFUSED:
        return float("inf")
    if dist(a, psi0) > radius or dist(b, psi0) > radius:
        return float("inf")
    return dist(a, b)


def nearest_committed(
    emb: np.ndarray,
    index: List[Unit],
    psi0: np.ndarray,
    radius: float,
) -> Tuple[Optional[Unit], float]:
    best: Optional[Unit] = None
    best_c: float = float("inf")
    for u in index:
        if u.status != Status.COMMITTED:
            continue
        c = cost_pair(emb, u.embedding, psi0, radius, u.status)
        if c < best_c:
            best = u
            best_c = c
    return best, best_c


#: The claim register, loaded ONCE and shared. It lives in fieldcore
#: because the ground's claims are fieldcore's own -- the gate limits,
#: the governor, the substrate verdict, the drift, the locus.
#:
#: WHY THE THIRD GATE, and it is not a duplicate of the two above.
#:
#:   gate_m0        the SIMILARITY gate. Is this span near the ground?
#:   nearest_committed  the COST gate. Is this span near what is
#:                     already committed?
#:   THE CLAIM GATE the POLARITY gate. Does this span CONTRADICT a
#:                     ground claim?
#:
#: And the third is the one the first two cannot do. Measured, 2026-10-26
#: (fieldcore/src/gate_truth_diagnostic.py):
#:
#:   the on-ground sentence   +0.935641
#:   its own contradiction    +0.932066
#:
#: A contradiction is SIMILAR to the ground -- that is what makes it a
#: contradiction rather than an off-topic sentence -- so the similarity
#: gate admits the lie at almost exactly the truth's score. No floor
#: separates them. The polarity gate is a different instrument, and it
#: is the one that reads the difference.
#:
#: THE LOADER. If fieldcore is not importable, the claim gate is
#: ABSENT, and an absent gate must not read as a pass. So the claim
#: gate is FAIL-CLOSED when it cannot load: it refuses, it does not
#: wave the span through. A missing substrate is a skip, and a skip is
#: never a pass.
_CLAIM_REGISTER = None
_CLAIM_REGISTER_TRIED = False


def _claim_register():
    """The shared claim register, or None if fieldcore is unreachable."""
    global _CLAIM_REGISTER, _CLAIM_REGISTER_TRIED
    if _CLAIM_REGISTER_TRIED:
        return _CLAIM_REGISTER
    _CLAIM_REGISTER_TRIED = True
    try:
        import os
        import sys
        here = os.path.dirname(os.path.abspath(__file__))
        # src/constitutional/lexicon -> src -> simself -> work_repos
        repos = os.path.abspath(
            os.path.join(here, "..", "..", "..", ".."))
        fc = os.path.join(repos, "fieldcore", "src")
        if os.path.isdir(fc) and fc not in sys.path:
            sys.path.insert(0, fc)
        import claim_register as _cr
        _CLAIM_REGISTER = _cr.standard_register()
    except Exception:
        _CLAIM_REGISTER = None
    return _CLAIM_REGISTER


def claim_gate(text: str) -> Tuple[bool, str]:
    """The polarity gate. Returns (allow, reason).

    FAIL-CLOSED. If the register cannot be loaded, the span is
    refused with a reason that says so -- because an absent gate must
    not read as a pass.

    AND IT IS THE THIRD GATE, not a fourth. The claim register is
    consulted once per span, and its verdict is one of the reasons the
    ingest path can return.
    """
    reg = _claim_register()
    if reg is None:
        return False, "claim_gate_unavailable"
    try:
        adj = reg.read(text)
    except Exception as exc:  # noqa: BLE001
        # an exception is not a verdict, and it is not a pass
        return False, "claim_gate_raised:%s" % type(exc).__name__
    if adj.verdict.value == "contradicted":
        return False, "contradicts_ground:%s" % (adj.claim_id or "?")
    if adj.verdict.value == "ungrounded":
        return False, "ungrounded_claim:%s" % (adj.claim_id or "?")
    return True, "ok"


def gate_m0(
    emb: np.ndarray,
    psi0: np.ndarray,
    max_norm: float = 4.0,
    min_cos: float = 0.4,
) -> Tuple[bool, str]:
    """The kernel veto, exposed for ingestion.

    Same two inequalities as fieldcore/src/tiniest-core/tiniest_core.py:M0_Governor.
    Per Grok sharpen 2026-09-16 + K8: this must match harness/gate.py exactly.
    """
    n = float(np.linalg.norm(emb))
    if n > max_norm:
        return False, "norm"
    if n == 0.0 or float(np.linalg.norm(psi0)) == 0.0:
        return False, "zero"
    cos = float(np.dot(emb, psi0) / (n * float(np.linalg.norm(psi0))))
    if cos < min_cos:
        return False, "coherence"
    return True, "ok"


def ingest(
    text: str,
    psi0: np.ndarray,
    psi: np.ndarray,
    index: List[Unit],
    embed: EmbedFn,
    classify: TypeFn,
    *,
    radius: float = 3.0,
    commit_radius: float = 0.8,
    max_norm: float = 4.0,
    min_cos: float = 0.4,
) -> Tuple[Unit, Verdict]:
    """Embed, cost, and either store a unit or return a refusal.

    Drift is measured before any write; ingest does not move ψ. Movement is a
    later identity update that consumes an admitted or committed unit.
    """
    span = " ".join(text.split())
    emb = np.asarray(embed(span), dtype=float)
    utype = classify(span)
    uid = f"u{len(index):06d}"
    unit = Unit(id=uid, span=span, utype=utype, embedding=emb)

    drift0 = dist(psi, psi0)
    ok, why = gate_m0(emb, psi0, max_norm, min_cos)
    nbr, c_nbr = nearest_committed(emb, index, psi0, radius)
    c_g = cost_pair(emb, psi0, psi0, radius, Status.COMMITTED)

    # THE POLARITY GATE, and it runs BEFORE the similarity gate.
    #
    # WHY BEFORE. The similarity gate cannot see a contradiction -- it
    # admits one at almost the truth's score, because a contradiction
    # is similar to the ground. So a span that contradicts the ground
    # would clear the similarity gate and be committed, and the
    # contradiction would be a fact in the lexicon. The polarity gate
    # is the one that catches it, so it runs first.
    #
    # AND IT IS FAIL-CLOSED. An unavailable register refuses the span
    # with a reason, because a missing substrate is a skip and a skip
    # is never a pass.
    claim_ok, claim_why = claim_gate(span)
    if not claim_ok:
        unit.status = Status.REFUSED
        v = Verdict(False, claim_why, c_g, c_nbr,
                    None if nbr is None else nbr.id, drift0, drift0)
        index.append(unit)
        return unit, v

    if not ok:
        unit.status = Status.REFUSED
        v = Verdict(False, why, c_g, c_nbr,
                    None if nbr is None else nbr.id, drift0, drift0)
        index.append(unit)
        return unit, v

    if not np.isfinite(c_g):
        unit.status = Status.REFUSED
        v = Verdict(False, "outside_ball", c_g, c_nbr,
                    None if nbr is None else nbr.id, drift0, drift0)
        index.append(unit)
        return unit, v

    if utype == UnitType.COMMIT and c_g <= commit_radius:
        unit.status = Status.COMMITTED
        if nbr is not None:
            unit.support.append(nbr.id)
        reason = "commit"
        allow = True
    else:
        unit.status = Status.ADMITTED
        reason = "admit"
        allow = True

    v = Verdict(allow, reason, c_g, c_nbr,
                None if nbr is None else nbr.id, drift0, drift0)
    index.append(unit)
    return unit, v


# Minimal embedder and type tag so this runs without a private model.
# Replace both later. Do not replace ingest.
PRIM = {
    "send": UnitType.ACT, "write": UnitType.ACT, "stop": UnitType.REFUSE,
    "not": UnitType.REFUSE, "will": UnitType.COMMIT, "must": UnitType.COMMIT,
    "yesterday": UnitType.TIME, "user": UnitType.NAME,
}


def embed_bag(span: str, dim: int = 16) -> np.ndarray:
    """Stable bag-of-tokens embedder.

    HASHING FIX 2026-10-16 (Hermes). This used Python's builtin `hash()`,
    which is randomized per process by PYTHONHASHSEED. Measured: the SAME span
    embedded to axis 2 in one process and axis 4 in the next.

        process 1: [0.0, 0.0, 0.56, 0.0, 0.0, ...]
        process 2: [0.0, 0.0, 0.0, 0.0, 0.56, ...]

    Consequences, all of them load-bearing:

      - a committed Unit's embedding does not survive a restart, so the
        lexicon silently rewrites itself every run
      - the M0 gate's allow/refuse verdict is not reproducible: identical
        input, different answer, chosen by process start order
      - the exam and the tests each get their own ground truth, which is
        why 79 tests could pass while the real score was 8/23

    `hashlib.blake2b(digest_size=8)` replaces it: fast, stdlib, and stable
    across processes, machines and Python versions. The algorithm is
    otherwise UNCHANGED — same two accumulations, same normalisation, same
    dim. Only the hash changed, so old in-memory units are unaffected and
    no stored artifact needs migrating (there are none to migrate: see
    above, they could not have persisted meaningfully).

    Do not "fix" this by seeding PYTHONHASHSEED. That fixes the symptom in
    one launcher and leaves every other entry point wrong.
    """
    v = np.zeros(dim)
    for tok in span.lower().split():
        h = int.from_bytes(
            hashlib.blake2b(tok.encode("utf-8"), digest_size=8).digest(), "big"
        )
        v[h % dim] += 1.0
        v[(h // dim) % dim] += 0.25
    n = float(np.linalg.norm(v))
    return v if n == 0 else v / n


def classify_span(span: str) -> UnitType:
    toks = set(span.lower().split())
    for k, t in PRIM.items():
        if k in toks:
            return t
    return UnitType.OTHER


__all__ = [
    "Status", "UnitType", "Unit", "Verdict",
    "EmbedFn", "TypeFn",
    "dist", "cost_pair", "nearest_committed", "gate_m0",
    "ingest", "embed_bag", "classify_span", "PRIM",
]
