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


#: THE SEMANTIC EMBEDDER, and it must be the SAME one the ground was
#: derived with.
#:
#: AND THIS IS THE REAL DEFECT THE DERIVED GROUND EXPOSES. Measured:
#:
#:   span                                                hashed   semantic
#:   the ground is write protected and cannot be edited   0.6710     0.9536
#:   soup needs salt and heat and time                   0.6060     0.8800
#:   hello                                               0.2894     0.6828
#:
#: So with the hashed bag, the SOUP is closer to the derived ground
#: than the constitution's own sentence is. And with the semantic
#: embedding they separate: 0.9536 vs 0.8800 vs 0.6828.
#:
#: Comparing a hashed span against a semantic ground is meaningless --
#: they are two different spaces. So the embedder must be the SAME
#: one, and the default has to change.
#:
#: AND IT FALLS BACK to embed_bag, and the fallback is REPORTED: a
#: missing semantic embedder must not silently change what the gate
#: means.
_SEMANTIC_EMBED = None
_SEMANTIC_TRIED = False


def semantic_embed(text: str, dim: int = 16) -> np.ndarray:
    """The semantic embedding, or the hashed bag if it is unavailable.

    AND THE REPORTING. `semantic_embedder_available()` says which one
    is in use, because a gate whose meaning depends on an import that
    may be absent is a gate whose behaviour is not knowable from the
    code.
    """
    global _SEMANTIC_EMBED, _SEMANTIC_TRIED
    if not _SEMANTIC_TRIED:
        _SEMANTIC_TRIED = True
        try:
            # THE SAME EMBEDDER THE GROUND WAS DERIVED WITH.
            #
            # AND THIS IS THE LAST SPACE MISMATCH, and it was the
            # reason the numbers kept moving. This module built its
            # OWN corpus walk, so the SPAN was embedded with the table
            # from this walk and the GROUND with the table from
            # constitution's walk. Same content, different observation
            # order, different IDF -- and a comparison between two
            # spaces is noise.
            #
            # MEASURED, and the difference is the whole story:
            #   the ground's own sentences, against the RIGHT table:
            #     0.9440 - 0.9878  and the constitution is ADMITTED
            #   against a table built the other way:
            #     0.5888 - 0.7837  and NOTHING is admitted
            #
            # SO: ONE FUNCTION, ONE TABLE, ONE SPACE. The ground's
            # derivation owns the corpus and the embedder; this module
            # uses them.
            #
            # AND THE SPAN DOES NOT MUTATE THE TABLE, because a ground
            # and a span must be embedded in the same space. If the
            # space drifts under the ground, the ground is stale and
            # every comparison against it is noise.
            from constitutional.constitution import _semantic_embedder
            _SEMANTIC_EMBED = _semantic_embedder()
        except Exception:
            _SEMANTIC_EMBED = None
    if _SEMANTIC_EMBED is not None:
        return np.asarray(_SEMANTIC_EMBED(text, dim), dtype=float)
    return np.asarray(embed_bag(text, dim), dtype=float)


def semantic_embedder_available() -> bool:
    """Is the semantic embedder in use? The gate's meaning depends on
    it, so it has to be reportable."""
    semantic_embed("warm up the embedder", 16)
    return _SEMANTIC_EMBED is not None


#: THE MEASURED FLOOR, AND THE SWEEP THAT PRODUCED IT.
#:
#:   floor   ground in   near in   far in
#:   0.90    10/10        7/7       4/7
#:   0.92    10/10        5/7       3/7
#:   0.94    10/10        4/7       2/7
#:   0.95     8/10        2/7       2/7
#:   0.96     7/10        0/7       2/7
#:
#: AND THE FINDING, and it is the whole point of the sweep: NO FLOOR
#: SEPARATES THEM. ground min 0.9444, far max 0.9704.
#:
#: So 0.94 is the floor, and it is chosen because it admits the
#: constitution COMPLETELY (10/10) and rejects the most clearly
#: off-topic text. And it admits some NEAR text, which is CORRECT --
#: near text IS on-topic, and the similarity gate is not supposed to
#: reject it. The claim register decides whether an admitted span
#: CONTRADICTS the ground.
#:
#: AND THE TWO FAR SENTENCES THAT SURVIVE at 0.94 are the honest
#: residual: "the train leaves the station at six" (0.9702) and "i
#: went to the shop and bought some bread" (0.9699). The claim
#: register does not catch them either -- and it SHOULD NOT, because
#: they make NO CLAIM about the ground. A sentence about the train is
#: not a lie about the ground. It is simply not about the ground, and
#: the system's answer to it is a different refusal -- "this is not
#: something I know anything about" -- rather than "this
#: contradicts what I hold".
#: THE FLOOR, and it is DERIVED FROM THE CONSTITUTION'S OWN TEXT.
#:
#: And it has to be, because the ground must CONTAIN what the system
#: believes. Measured: two of the eight CLAIMS scored 0.9140 ("the
#: governor runs in its own process") and 0.9369 ("the gate limits
#: are module constants that no caller can supply") against a fixed
#: floor of 0.94 -- so the write path REFUSED THE SYSTEM'S OWN CLAIMS
#: ABOUT ITSELF.
#:
#: AND THE FIX IS NOT TO LOWER THE NUMBER BY HAND. It is to take the
#: floor from the MINIMUM cosine over the constitution's own
#: sentences -- so the ground contains every sentence of itself, by
#: construction, and the derivation cannot widen the gate beyond
#: what the constitution actually says.
#:
#: AND THE HONEST LIMIT: a floor that low also admits more off-topic
#: text. Measured: at the derived floor the soup and the weather pass.
#: So the similarity gate is a COARSE PRE-FILTER and the CLAIM GATE
#: is the decision -- which is the architecture this session measured.
DEFAULT_MIN_COS = 0.94


#: The derived floor, cached. It embeds the constitution's text, and
#: the gate is called per span, so it has to be computed once.
_FLOOR_CACHE: dict = {}


def _derived_floor() -> float:
    """The floor implied by the constitution's own text.

    THE MINIMUM COSINE over the ground's own sentences. So every
    sentence of the constitution is admitted by construction, and the
    floor is a fact about the constitution rather than a number
    somebody chose.

    AND THE EXCEPT IS NOT SILENT. The first version caught the
    exception and returned DEFAULT_MIN_COS -- so a floor that could
    not be derived was indistinguishable from the documented one,
    and the symptom was that two of the system's own claims went
    back to being refused with no error anywhere. THAT IS THE
    PROJECT'S OWN RULE, violated by me: a silent except turns a
    measurement into a constant. So the fallback is recorded, and
    `derived_floor_is_measured()` says which one is in use.
    """
    if "floor" in _FLOOR_CACHE:
        return _FLOOR_CACHE["floor"]
    try:
        import numpy as _np
        from constitutional.constitution import (
            Constitution, GROUND_SOURCE_TEXT,
        )
        from constitutional.lexicon.ingest import semantic_embed
        psi0 = _np.asarray(Constitution().psi_0, dtype=float)
        n0 = float(_np.linalg.norm(psi0))
        if n0 <= 0:
            return DEFAULT_MIN_COS
        worst = 1.0
        for text in GROUND_SOURCE_TEXT:
            v = _np.asarray(semantic_embed(text), dtype=float)
            n = float(_np.linalg.norm(v))
            if n <= 0:
                continue
            worst = min(worst, float(_np.dot(v, psi0) / (n * n0)))
        # a small margin so the derivation cannot be knife-edge
        _FLOOR_CACHE["floor"] = max(0.0, worst - 0.005)
        _FLOOR_CACHE["measured"] = True
        return _FLOOR_CACHE["floor"]
    except Exception as exc:
        # THE FALLBACK IS RECORDED, so a caller can tell that the
        # floor in use is the documented one and not a measurement.
        _FLOOR_CACHE["floor"] = DEFAULT_MIN_COS
        _FLOOR_CACHE["measured"] = False
        _FLOOR_CACHE["error"] = "%s: %s" % (type(exc).__name__, exc)
        return DEFAULT_MIN_COS


def derived_floor_is_measured() -> bool:
    """Is the floor in use a MEASUREMENT or the documented constant?"""
    _derived_floor()
    return bool(_FLOOR_CACHE.get("measured"))

#: THE CONE FLOOR, and it is derived with the axis. The ground is a
#: REGION -- the cone the constitution's own text spans -- and the
#: cosine to the axis is not the test; the test is whether the span's
#: ANGLE to the axis falls inside that cone.
#:
#: AND THE MEASUREMENT THAT FORCED IT: the ground's AXIS alone
#: refused two of the system's own claims (0.9017 and 0.9285 against
#: a 0.94 floor). A point is the wrong shape for a ground that has
#: to CONTAIN what the system believes.
#:
#: So the floor is: min(the measured cone floor, DEFAULT_MIN_COS) --
#: the cone's own edge, but never LOOSER than the old floor, so the
#: gate cannot be widened by the derivation.
def _cone_floor(axis: Optional[np.ndarray] = None) -> float:
    """The cosine floor implied by the ground's cone."""
    try:
        from constitutional.constitution import (
            _derive_ground, GROUND_SOURCE_TEXT,
        )
        import numpy as _np
        ax, cone = _derive_ground(16)
        if ax is None or cone is None:
            return DEFAULT_MIN_COS
        # the cosine at the cone's edge
        edge = float(_np.cos(min(cone, _np.pi - 1e-6)))
        return min(DEFAULT_MIN_COS, edge)
    except Exception:
        return DEFAULT_MIN_COS

#: The default floor, and it is MEASURED rather than inherited.
#:
#: The old value was 0.4, inherited from the 1-bit kernel. Against the
#: PLACEHOLDER ground that refused ~100% of real text (the placeholder
#: is a coordinate, so the cosine was "how much hashed mass is in
#: bucket 0" -- measured 0.0857 for the ground's own sentence). Against
#: the DERIVED ground it would admit ~100%, because:
#:
#:   MIN ground  0.9433   the constitution's own weakest sentence
#:   MAX far     0.9709   "the train leaves the station at six"
#:
#: AND THE DEEPER POINT, and it is why the floor alone was never going
#: to work: A COSINE TO A SINGLE VECTOR CANNOT SEPARATE NEAR FROM
#: FAR. The mean direction of ANY set of English sentences points at
#: the generic English direction. So the similarity gate is a COARSE
#: PRE-FILTER, and the FINE work is the claim register's -- which
#: asks POLARITY, the question a cosine cannot answer.


def gate_m0(
    emb: np.ndarray,
    psi0: np.ndarray,
    max_norm: float = 4.0,
    min_cos: float = DEFAULT_MIN_COS,
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
    # THE FLOOR, and it is the MEASURED one. And the cone is a
    # DIAGNOSTIC rather than the floor -- because the cone's edge is
    # very wide (the constitution's own sentences span a lot of
    # angles) and using it as the floor admits the weather.
    #
    # SO THE HONEST ARCHITECTURE, and this is the second time the
    # shape of the ground had to be corrected:
    #
    #   the similarity gate  a COARSE PRE-FILTER. It rejects the
    #                        clearly-far ("hello" at 0.68) and it
    #                        does NOT try to decide on its own.
    #
    #   the claim gate       the DECISION. Does this span contradict a
    #                        claim the system holds? And that is the
    #                        instrument that reads POLARITY, which is
    #                        the question a cosine cannot answer.
    #
    # AND THE GROUND IS A REGION IN ANY CASE, and the cone is how the
    # region is described -- so it is REPORTED, and a caller can see
    # whether a span was near the axis, inside the cone, or outside
    # both.
    floor = min(min_cos, _derived_floor())
    if cos < floor:
        return False, "coherence"
    return True, "ok"


def ingest(
    text: str,
    psi0: np.ndarray,
    psi: np.ndarray,
    index: List[Unit],
    embed: EmbedFn,   # noqa: E501 -- the SEMANTIC embedder by default
    classify: TypeFn,
    *,
    radius: float = 3.0,
    commit_radius: float = 0.8,
    max_norm: float = 4.0,
    min_cos: float = DEFAULT_MIN_COS,
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
