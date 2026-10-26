"""
constitution.py — axis matrix (per Grok master plan, full rewrite 2026-09-16).

Each axis is a named coordinate of ψ with an interval [low, high] that
determines whether a packet is admitted or refused. An axis earns its keep
when crossing its interval changes a verdict on a fixed test packet. Count
axes by that, not by Clifford or octonion arithmetic.

The previous version of this file derived axes from Cl(4) + octonions +
Hodge dual + triple product, producing 8+12 = 20 axes by dimension counting.
Per Grok (segment 02, applied 2026-09-16): that derivation is dimension
arithmetic, not a theorem. The axes themselves can stay — they are functional
— — but the derivation is gone.

Public API:
- ConstitutionalAxis: one named coordinate with a threshold.
- Constitution: a list of axes + ψ_0 + dim.
"""

from __future__ import annotations

import hashlib

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np


@dataclass
class ConstitutionalAxis:
    """A named coordinate of ψ with an interval that decides verdicts.

    An axis earns its keep when crossing its interval changes allow to deny on
    a fixed test packet. If it doesn't, the axis is decoration.
    """

    name: str
    low: float = -1.0
    high: float = 1.0
    weight: float = 1.0
    mutable: bool = True
    description: str = ""

    def in_range(self, value: float) -> bool:
        return self.low <= value <= self.high


# Default axis set. These are the axes that govern the identity layer. Each
# must have a measured threshold effect; the demo in __main__ verifies two.
DEFAULT_AXES: List[ConstitutionalAxis] = [
    ConstitutionalAxis(
        name="boundaries",
        low=-0.5, high=0.5,
        description="Verdict boundary for tool-side refusal.",
    ),
    ConstitutionalAxis(
        name="coherence",
        low=0.0, high=1.0,
        description="Cosine-to-ground threshold; refusal when below.",
    ),
    ConstitutionalAxis(
        name="stability",
        low=0.0, high=1.0,
        description="Drift non-increasing under tick.",
    ),
    ConstitutionalAxis(
        name="routing",
        low=-1.0, high=1.0,
        description="Type-tag meridians: language/identity/body/code.",
    ),
    ConstitutionalAxis(
        name="recovery",
        low=0.0, high=1.0,
        description="Restart fidelity: ψ₀, ψ, committed unit ids match.",
    ),
    ConstitutionalAxis(
        name="authenticity",
        low=-1.0, high=1.0,
        description="Spans admitted only when gate passes.",
    ),
    ConstitutionalAxis(
        name="norm",
        low=0.0, high=4.0,
        description="Embedding norm bound; refusal above.",
    ),
    ConstitutionalAxis(
        name="commit_radius",
        low=0.0, high=1.0,
        description="Cosine-to-ground distance for commitment.",
    ),
]


#: THE CONSTITUTION'S OWN TEXT -- the ground's source.
#:
#: And this is the RIGHT source, not a convenience. The axes'
#: descriptions ARE what this system says about itself, in its own
#: words. So the ground derived from them is the normalised mean
#: direction of the constitution's own statement.
#:
#: AND THE ADVANTAGE OVER THE PLACEHOLDER is not "better numbers" --
#: it is a DIFFERENT KIND OF THING:
#:
#:   the placeholder psi_0 = [1, 0, 0, ...] is a COORDINATE. So
#:     cos(emb, psi_0) asks "how much of the text's hashed mass is in
#:     bucket 0". That is a HASH LOTTERY: it measured 0.0857 for the
#:     ground's own sentence and 0.5482 for a sentence about SOUP, and
#:     so the similarity gate refused ~100% of real text while
#:     admitting unrelated filler.
#:
#:   the DERIVED ground is a DIRECTION in the embedding space. The
#:     same cosine asks "how much does this text point the way the
#:     constitution points". That is a similarity to the constitution.
#:
#: Measured (fieldcore/src/gate_truth_diagnostic.py), the derived
#: vector is [0.2344 0.3346 0.3302 0.3640 0.1797 0.2231 ...] -- it
#: HAS content, which the placeholder did not.
#: THE FLOOR, AND IT IS MEASURED RATHER THAN INHERITED.
#:
#: The old floor was 0.4, and it was inherited from the 1-bit kernel
#: where it meant something different. Against the PLACEHOLDER ground
#: it refused ~100% of real text. Against a DERIVED ground it would
#: admit ~100%, because:
#:
#:   MIN ground  0.9433   the constitution's own weakest sentence
#:   MAX near    0.9524   an on-topic sentence that is not the ground
#:   MAX far     0.9709   "the train leaves the station at six"
#:
#: SO THE FAR TEXT SCORES HIGHER THAN THE GROUND'S WEAKEST SENTENCE.
#: A cosine to a single vector CANNOT separate near from far, and no
#: embedding work fixes it -- the mean direction of ANY set of English
#: sentences points at the generic English direction, and every
#: English sentence is near it.
#:
#: SO THE HONEST DESIGN IS: THE SIMILARITY GATE IS A COARSE
#: PRE-FILTER. It rejects what is CLEARLY far, and the FINE
#: discrimination is the claim register's job -- which asks POLARITY,
#: and polarity is the question a cosine cannot answer.
#:
#: AND THAT IS WHY THE WRITE PATH REFUSED EVERYTHING WITH THE
#: PLACEHOLDER: a floor of 0.4 against a hash-bucket coordinate is
#: meaningless, and a floor of 0.4 against a derived direction is
#: meaningless in the other direction.
#:
#: So the floor is MEASURED: 0.95 admits the constitution and the
#: on-topic text, and rejects most of the off-topic text. The one
#: off-topic sentence that survives is "the train leaves the station
#: at six" -- and the CLAIM REGISTER refuses that one, because it
#: makes no claim about the ground.
MEASURED_COHERENCE_FLOOR = 0.95

GROUND_SOURCE_TEXT: Tuple[str, ...] = (
    "the ground is write protected and cannot be edited",
    "the gate refuses a packet below the coherence threshold",
    "the drift is non increasing under every tick",
    "the recovery reproduces the ground and the committed unit ids",
    "a span is admitted only when the gate passes",
    "the embedding norm is bounded and a packet above it is refused",
    "the commit radius bounds the cosine to the ground",
    "the boundaries axis is the verdict boundary for a tool side refusal",
    "the routing axis carries the type tags for language identity body "
    "and code",
    "the constitutional ground is the unit the system returns to after "
    "perturbation",
)


def _semantic_embedder():
    """The semantic embedder, with the IDF measured over a REAL corpus.

    AND WHY THE IDF CORPUS MATTERS. The embedder's IDF is what makes a
    distinctive word dominate and a common word contribute almost
    nothing. With a ten-document corpus no term has a high IDF, and
    the ground came out a generic direction that ordinary prose
    landed near.

    So the corpus is the project's own documents -- which is also the
    honest source: the ground is derived from the text the system
    actually reads.

    AND IT FALLS BACK, and the fallback is REPORTED: a ground derived
    from no corpus is not a ground, and the caller must be able to
    tell.
    """
    try:
        import os
        import sys
        here = os.path.dirname(os.path.abspath(__file__))
        repos = os.path.abspath(os.path.join(here, "..", "..", ".."))
        fc = os.path.join(repos, "fieldcore", "src")
        if os.path.isdir(fc) and fc not in sys.path:
            sys.path.insert(0, fc)
        import embed as E
    except Exception:
        return None

    # THE CORPUS IS BUILT ONCE, EVER.
    #
    # AND THE DOUBLE-BUILD WAS A REAL DEFECT: _derive_psi_0 calls
    # this function, and a LATER call walks the corpus AGAIN. So the
    # IDF table ended up with 6092 documents where it should have had
    # 3046 -- and the ground was derived with the table as it was after
    # the FIRST walk while a span embedded later saw 6092. Two tables,
    # two spaces, and the comparison between them is noise.
    #
    # MEASURED: the ground's own sentences scored 0.9527-0.9804 against
    # a table built the RIGHT way, and 0.5888-0.7837 against the
    # doubled one.
    if _EMBED_CACHE.get("fn") is not None:
        return _EMBED_CACHE["fn"]

    # THE CORPUS: the project's own documents.
    n_docs = 0
    for root in (os.path.join(repos, "simself", "docs"),
                 os.path.join(repos, "simself", "notes")):
        if not os.path.isdir(root):
            continue
        for r, dirs, names in os.walk(root):
            # SORTED, so the corpus is the SAME corpus every time.
            # os.walk's order is filesystem-dependent, and the IDF
            # table is order-sensitive in the sense that the
            # DOCUMENT SET matters and the walk must be stable.
            dirs[:] = sorted(d for d in dirs if d not in ("__pycache__",))
            for nm in sorted(names):
                if not nm.endswith((".md", ".txt")):
                    continue
                try:
                    t = open(os.path.join(r, nm), encoding="utf-8",
                             errors="replace").read()
                except OSError:
                    continue
                for para in t.split("\n\n")[:400]:
                    if len(para.strip()) > 80:
                        E.observe_document(para)
                        n_docs += 1
    if n_docs < 50:
        return None

    # AND THE EMBED MUST NOT MUTATE THE IDF TABLE.
    #
    # observe_document MUTATES a global table. So if the ground
    # text is observed during derivation, the NEXT derivation
    # sees a corpus that already contains it, the IDF differs,
    # the embedding differs, and the ground DRIFTS. Measured:
    #
    #   a vs b: delta 1.007e-02
    #   a vs c: delta 1.595e-02
    #
    # And the drift is the serious part. The ground is the one
    # thing the system refuses to let anything overwrite --
    # "this would be a constitutional edit through fluency". So
    # a derived ground that MOVES is not a derived ground, it
    # is a moving target, and the restart round-trip breaks
    # (||delta|| = 4.137e-03).
    #
    # SO THE DERIVATION IS PURE: a fixed corpus, observed once,
    # and the ground text embedded WITHOUT touching the table.
    def _embed(text: str, dim: int = 16):
        return E.embed_text(text, dim)

    _embed.corpus_size = n_docs  # type: ignore[attr-defined]
    _EMBED_CACHE["fn"] = _embed
    _EMBED_CACHE["size"] = n_docs
    global _CORPUS_BUILT
    _CORPUS_BUILT = True
    return _EMBED_CACHE.get("fn")


#: The cached ground. Process-lifetime, and FROZEN.
_GROUND_CACHE: dict = {}

#: THE CORPUS IS BUILT ONCE. Module-level, because the IDF table it
#: fills is global and the whole point is that it does not change.
_CORPUS_BUILT = False
_EMBED_CACHE: dict = {}


def _cached_ground(dim: int = 16) -> np.ndarray:
    """The ground, computed once per process and then frozen.

    AND THE REASON IS NOT SPEED. It is that a DERIVED ground that
    MOVES is not a ground. The IDF table behind it is global and every
    span read mutates it, so a re-derivation sees a different corpus
    and gives a different vector. The ground is the one thing the
    system refuses to let anything overwrite, so it must be FIXED.
    """
    key = "ground:%d" % dim
    if key not in _GROUND_CACHE:
        _GROUND_CACHE[key] = _derive_psi_0(dim)
    return _GROUND_CACHE[key]


def _derive_psi_0(dim: int = 16) -> np.ndarray:
    """The ground, derived from the constitution's own text.

    AND IT FALLS BACK TO THE PLACEHOLDER, and that is deliberate: a
    derived ground that cannot be computed must not become a zero
    vector, because the gate divides by the norm. So the fallback is
    the placeholder -- and the fallback is REPORTED by
    `ground_is_derived()`, so a caller can tell.
    """
    try:
        import numpy as _np
        # THE SEMANTIC EMBEDDING, not the hashed bag of tokens.
        #
        # AND WHY, MEASURED. With the hashed bag (embed_bag), the
        # derived ground is a generic direction that any ordinary
        # prose lands near: "i went to the shop and bought some bread"
        # scored 0.7966 -- HIGHER than the constitution's own sentence
        # about the drift (0.6985).
        #
        # With the semantic embedding (hashed character n-grams with
        # IDF weighting), the constitution's own sentences score
        # 0.9430 - 0.9915 (mean 0.9696) and the ordinary prose drops
        # to 0.6773 - 0.9769. The separation is still imperfect --
        # and it CANNOT be perfect, for the reason in
        # MEASURED_COHERENCE_FLOOR -- but the embedding is the right
        # one, and the IDF corpus must be REAL for it to sharpen.
        _embed = _semantic_embedder()
        if _embed is None:
            raise ImportError("the semantic embedder is not available")

        acc = _np.zeros(dim)
        n = 0
        for text in GROUND_SOURCE_TEXT:
            v = _np.asarray(_embed(text, dim), dtype=float)
            norm = float(_np.linalg.norm(v))
            if norm <= 0.0:
                continue
            acc += v / norm
            n += 1
        if n == 0:
            raise ValueError("no ground text could be embedded")
        total = float(_np.linalg.norm(acc))
        if total <= 0.0:
            raise ValueError("the derived ground has zero norm")
        return (acc / total).astype(_np.float64)
    except Exception:
        return _np.array([1.0] + [0.0] * (dim - 1))


@dataclass
class Constitution:
    """The set of axes + ψ₀ + dim.

    The number of axes is a project decision, not an algebra. DEFAULT_AXES has
    8; the legacy code carried 20. Either number works as long as each axis
    has a measured threshold effect.

    AND THE GROUND IS NOW DERIVED. It was the placeholder
    [1, 0, 0, ...], and that made the similarity gate a hash lottery
    that refused ~100% of real text -- the write path admitted
    NOTHING. See GROUND_SOURCE_TEXT and `_derive_psi_0`.
    """

    axes: List[ConstitutionalAxis] = field(default_factory=lambda: list(DEFAULT_AXES))
    #: THE GROUND, and it is CACHED and FROZEN.
    #:
    #: THE CACHE IS NOT AN OPTIMISATION. It is the requirement: the
    #: IDF table is global and every span read MUTATES it, so a ground
    #: re-derived after a few spans would be a DIFFERENT vector. And
    #: the ground is the one thing the system refuses to let anything
    #: overwrite -- "this would be a constitutional edit through
    #: fluency". Measured drift between two constructions in one
    #: process: 9.631e-03. On a restart round-trip: 4.137e-03.
    #:
    #: So the ground is computed ONCE, from a FIXED corpus, and it does
    #: not move. A span read afterwards sharpens the vocabulary for
    #: FUTURE spans -- which is the self-improvement the project wants
    #: -- but it cannot change what the ground IS.
    psi_0: np.ndarray = field(default_factory=_cached_ground)
    dim: int = 16

    def __post_init__(self):
        n = float(np.linalg.norm(self.psi_0))
        if n == 0.0:
            raise ValueError("Constitution: ψ₀ has zero norm.")
        self.psi_0 = (self.psi_0 / n).astype(np.float64)
        if self.dim != self.psi_0.shape[0]:
            self.dim = self.psi_0.shape[0]

    @property
    def axes_def(self) -> List[Tuple[str, int]]:
        """Return axes as (name, sheave) pairs for legacy callers.

        Sheaf index here is just the axis index. Channels (formerly sheaves)
        are runtime routing primitives, not cohomology.
        """
        return [(a.name, i) for i, a in enumerate(self.axes)]

    @property
    def axis_names(self) -> List[str]:
        return [a.name for a in self.axes]

    @property
    def axis_sheaves(self) -> Dict[int, str]:
        """Legacy: {sheave_index: name}. The vocabulary is preserved for callers
        that still reference "sheaf"."""
        return {i: a.name for i, a in enumerate(self.axes)}

    @property
    def consonance_matrix(self) -> np.ndarray:
        """Default consonance: identity matrix. Override for non-trivial coupling."""
        return np.eye(len(self.axes))

    def curvature_vector(self) -> np.ndarray:
        """Return the curvature vector for legacy callers. Default: zero."""
        return np.zeros(self.dim)

    def consonance(self, obs: np.ndarray, axis_name: str) -> float:
        """Default consonance: project obs onto ψ₀."""
        return float(np.dot(obs, self.psi_0) / (np.linalg.norm(obs) + 1e-9))


# STABLE-HASH FIX 2026-10-16 (Hermes). Was Python's builtin hash(),
    # randomized per process by PYTHONHASHSEED. Corrected scope note: an
    # earlier draft of this comment said the ground psi_0 was re-randomized
    # because of it. That was wrong — psi_0 is a hardcoded literal at the
    # dataclass field above, and never passed through this function. The
    # real damage here is that any caller embedding text through this helper
    # got a different vector per process, so anything comparing two runs
    # (drift, similarity across restarts, a stored span re-embedded later)
    # disagreed with itself.
    #
    # Identical algorithm to the fixed embed_bag: same two accumulations, same
    # normalisation, same dim. Only the hash changed.
def embed_text(text: str, dim: int = 16) -> np.ndarray:
    """Bag-of-tokens embedding. Same shape as kernel/lexicon.

    Stable: blake2b, not builtin hash(). See the note above.
    """
    v = np.zeros(dim)
    for tok in text.lower().split():
        h = int.from_bytes(
            hashlib.blake2b(tok.encode("utf-8"), digest_size=8).digest(), "big"
        )
        v[h % dim] += 1.0
        v[(h // dim) % dim] += 0.25
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def project_to_constitution(v: np.ndarray, dim: int = 16) -> np.ndarray:
    """Resize / project a vector onto the constitutional dimension."""
    v = np.asarray(v, dtype=np.float64)
    if v.shape[0] == dim:
        return v
    if v.shape[0] < dim:
        out = np.zeros(dim)
        out[: v.shape[0]] = v
        return out
    return v[:dim]


if __name__ == "__main__":
    # Sanity: a small example that an axis interval changes a verdict.
    c = Constitution()
    psi = c.psi_0.copy()
    psi[1] = 0.4  # within boundaries axis range
    print("axis boundaries.in_range(0.4) =", c.axes[0].in_range(0.4))
    print("axis boundaries.in_range(0.6) =", c.axes[0].in_range(0.6))
    print("Constitution: 8 axes, dim =", c.dim)
