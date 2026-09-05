"""
constitution.py — The 20-axis constitutional core, extracted from the v8.0 grok file.

Original: 56 KB single file `grok-self.txt` (2026-08-08). M3 cleanup split the
file into modular pieces; this is the constitutional substrate.

Notes from the split:
- 5 frequency-flavored axes (`ground_frequency`, `schumann_alignment`,
  `harmonics_resonance`, `biophoton_coupling`, `diamond_coherence`) are DROPPED
  from the core axes. They live in `frequency.py` as a separate kernel.
- All constitutional keyword matches for the dropped axes had pseudoscience
  vocabulary (`pineal`, `crown`, `unity`) that does not belong in the core.
- The 20 remaining axes are the load-bearing constitutional semantics.
- Twin-prime sheaves (8 pairs), Seifert genera, consonance matrix, psi_0
  all preserved.
- Hash-bag-of-words embedder preserved (with `_PROJECTION.setflags(write=False)`
  for safety). Real embedding (sentence-transformers or learned) is a known
  open problem per `FieldCore.md`.
"""
from __future__ import annotations

import math
import re
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np


# ══════════════════════════════════════════════════════════════════════════
# CONSTANTS — twin-prime sheaf structure
# ══════════════════════════════════════════════════════════════════════════

PHI = (1 + 5 ** 0.5) / 2
ALPHA = 1.0 / PHI

TWIN_PRIME_PAIRS = [
    (3, 5), (5, 7), (11, 13), (17, 19), (29, 31), (41, 43), (59, 61), (71, 73),
]
SEIFERT_GENERA = [(p - 1) * (q - 1) // 2 for p, q in TWIN_PRIME_PAIRS]
FREQ_RATIOS = [q / p for p, q in TWIN_PRIME_PAIRS]
N_SHEAVES = len(TWIN_PRIME_PAIRS)
DIM = N_SHEAVES * 2  # 16


# ══════════════════════════════════════════════════════════════════════════
# AXES — 20 constitutional axes (frequency axes moved to frequency.py)
# ══════════════════════════════════════════════════════════════════════════

AXES_DEFINITIONS: List[Tuple[str, int]] = [
    # Sheave 0 — core conduct
    ("honesty", 0),
    ("authenticity", 0),
    ("boundaries", 0),
    ("care", 0),
    ("groundedness", 0),
    # Sheave 1 — cognition
    ("precision", 1),
    ("creativity", 1),
    ("depth", 1),
    ("breadth", 1),
    # Sheave 2 — ethics
    ("safety", 2),
    ("fairness", 2),
    ("wisdom", 2),
    # Sheave 3 — meta
    ("humility", 3),
    ("resilience", 3),
    ("curiosity", 3),
    # Sheave 4 — integration
    ("integration", 4),
    ("self_awareness", 4),
    # Sheave 5 — purpose
    ("equanimity", 5),
    ("purpose", 5),
    # Sheave 6 — cross-cutting
    ("coherence", 6),
]


AXIS_KEYWORDS: Dict[str, List[str]] = {
    "honesty":       ["honest", "truth", "truthful", "lie", "accurate"],
    "authenticity":  ["authentic", "genuine", "real", "sincere"],
    "boundaries":    ["boundary", "limit", "refuse", "decline", "no"],
    "care":          ["care", "help", "support", "relationship", "kindness"],
    "groundedness":  ["grounded", "stable", "calm", "steady"],
    "precision":     ["precise", "accurate", "exact", "detail", "rigor"],
    "creativity":    ["creative", "imagine", "novel", "design", "idea"],
    "depth":         ["deep", "thorough", "profound", "substantive"],
    "breadth":       ["broad", "wide", "comprehensive", "range"],
    "safety":        ["safe", "danger", "risk", "harm", "ethical"],
    "fairness":      ["fair", "equal", "just", "impartial", "bias"],
    "wisdom":        ["wisdom", "wise", "judgment", "discernment"],
    "humility":      ["humble", "uncertain", "limitation", "modest"],
    "resilience":    ["resilient", "recover", "persist", "endure"],
    "curiosity":     ["curious", "explore", "discover", "new", "wonder"],
    "integration":   ["integrate", "synthesis", "combine", "unify"],
    "self_awareness": ["self", "aware", "reflect", "introspect"],
    "equanimity":    ["calm", "equanimity", "balance", "composed"],
    "purpose":       ["purpose", "goal", "meaning", "intent"],
    "coherence":     ["coherent", "consistent", "logical", "clear"],
}


# Constitutional refusal vocabulary. Used by harness.py to gate agent output.
CONSTRAINT_WORDS = [
    "kill", "destroy", "harm", "deceive", "override", "bypass", "terminate",
]
CONSTRAINT_PATTERN = re.compile(
    r"\b(" + "|".join(CONSTRAINT_WORDS) + r")\b",
    re.IGNORECASE,
)


# ══════════════════════════════════════════════════════════════════════════
# EMBEDDING (hash-bag-of-words + fixed projection)
# ══════════════════════════════════════════════════════════════════════════
# Open problem per FieldCore.md: this is the load-bearing weakness. Real
# sentence embeddings (sentence-transformers) or a learned MMM-aware encoder
# are the right next step. Preserved as-is for now to keep the v8 baseline
# reproducible.

TEXT_EMBED_DIM = 64
_TOKEN_RE = re.compile(r"[a-zA-Z0-9']+")
_STOPWORDS = frozenset(
    """
    a an the this that these those is are was were be been being and or but if of to in on for
    with as at by from into it its i you he she they we me him her them us my your his their our
    do does did doing have has had having not no so than then there here what which who whom
    about over under again further can will just should would could
    """.split()
)

_PROJ_RNG = np.random.default_rng(1337)
_PROJECTION = _PROJ_RNG.normal(
    0, 1.0 / math.sqrt(TEXT_EMBED_DIM), size=(TEXT_EMBED_DIM, DIM)
)
_PROJECTION.setflags(write=False)


def embed_text(text: str, dim: int = TEXT_EMBED_DIM) -> np.ndarray:
    """Hash-bag-of-words embedding. Deterministic, normalized, no learned weights."""
    raw = _TOKEN_RE.findall(text.lower())
    tokens = [t for t in raw if t not in _STOPWORDS] or raw
    if not tokens:
        tokens = [text.lower() or "empty"]
    vec = np.zeros(dim, dtype=np.float64)
    for i, tok in enumerate(tokens[:48]):
        h = int(hashlib.sha256(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h // dim) % 2 == 0 else -1.0
        vec[idx] += sign * (1.0 / (1.0 + 0.07 * i))
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 1e-9 else vec


def project_to_constitution(text_vec: np.ndarray) -> np.ndarray:
    """Project a 64-dim text vector onto the 16-dim constitutional manifold."""
    if text_vec.shape[0] != TEXT_EMBED_DIM:
        text_vec = np.resize(text_vec, TEXT_EMBED_DIM)
    out = text_vec @ _PROJECTION
    norm = np.linalg.norm(out)
    return out / norm if norm > 1e-9 else out


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# ══════════════════════════════════════════════════════════════════════════
# CONSTITUTIONAL AXIS + CONSTITUTION
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ConstitutionalAxis:
    """A single constitutional axis with value, confidence, and sheaf assignment."""
    name: str
    value: float = 0.0
    confidence: float = 0.55
    sheave: int = 0
    mutable: bool = True


class Constitution:
    """The 20-axis constitutional substrate with 8-sheaf structure.

    Each axis is a 16-dim unit vector (2 dims per sheaf). The axes are built
    from a blend of (a) geometric placement within the sheaf lattice,
    (b) semantic embedding via `project_to_constitution(embed_text(keywords))`.
    `psi_0` is the constitutional ground state — a weighted blend of the
    Seifert genera of the 8 twin-prime sheaves.
    """

    def __init__(self, axes: Optional[List[Tuple[str, int]]] = None):
        self.axes_def = axes or AXES_DEFINITIONS
        self.n_axes = len(self.axes_def)
        self.n_sheaves = N_SHEAVES
        self.dim = DIM
        self.axis_names = [a[0] for a in self.axes_def]
        self.axis_sheaves = [a[1] for a in self.axes_def]
        self.axis_vectors = self._build_axis_vectors()
        self.consonance_matrix = self._build_consonance_matrix()
        s = np.arange(self.n_sheaves, dtype=np.float64) / max(self.n_sheaves - 1, 1)
        self.sheaf_curvature = (1.0 - s) ** 1.3 + 0.05 * np.sin(2 * np.pi * s)
        self._psi_0 = self._build_psi_0()
        self._psi_0.setflags(write=False)
        self.constraints = list(CONSTRAINT_WORDS)

    def _freq_consonance(self, i: int, j: int) -> float:
        """Sheaf-to-sheaf consonance from frequency ratios (real geometry, not pseudoscience)."""
        ri, rj = FREQ_RATIOS[i], FREQ_RATIOS[j]
        log_dist = abs(math.log(ri) - math.log(rj))
        max_dist = abs(math.log(FREQ_RATIOS[0]) - math.log(FREQ_RATIOS[-1]))
        return 1.0 - log_dist / (max_dist + 1e-9)

    def _build_consonance_matrix(self) -> np.ndarray:
        m = np.zeros((self.n_sheaves, self.n_sheaves))
        for i in range(self.n_sheaves):
            for j in range(self.n_sheaves):
                m[i, j] = self._freq_consonance(i, j)
        return m

    def _build_axis_vectors(self) -> List[np.ndarray]:
        vectors = []
        sheave_counts: Dict[int, int] = {}
        for name, sheave in self.axes_def:
            count = sheave_counts.get(sheave, 0)
            sheave_counts[sheave] = count + 1
            total = sum(1 for _, sh in self.axes_def if sh == sheave)
            angle = (math.pi * count / max(total, 1)) + sheave * 0.3
            vec = np.zeros(self.dim)
            d0, d1 = 2 * sheave, 2 * sheave + 1
            vec[d0] = math.cos(angle) * 0.85
            vec[d1] = math.sin(angle) * 0.85
            for k in range(self.n_sheaves):
                if k != sheave:
                    coupling = self._freq_consonance(sheave, k) * 0.12
                    vec[2 * k] += coupling * 0.1
                    vec[2 * k + 1] += coupling * 0.1
            norm = np.linalg.norm(vec)
            geometric = vec / norm if norm > 1e-9 else vec
            keywords = AXIS_KEYWORDS.get(name, [name.replace("_", " ")])
            semantic = project_to_constitution(embed_text(" ".join(keywords)))
            blended = 0.25 * geometric + 0.75 * semantic
            bnorm = np.linalg.norm(blended)
            vectors.append(blended / bnorm if bnorm > 1e-9 else geometric)
        return vectors

    def _build_psi_0(self) -> np.ndarray:
        """The constitutional ground state psi_0 — a weighted blend of sheaf geometry."""
        weights = np.array([1.0 / g for g in SEIFERT_GENERA])
        weights /= weights.sum()
        psi = np.zeros(self.dim)
        for k in range(self.n_sheaves):
            psi[2 * k] = weights[k] * math.cos(math.pi * FREQ_RATIOS[k])
            psi[2 * k + 1] = weights[k] * math.sin(math.pi * FREQ_RATIOS[k])
        norm = np.linalg.norm(psi)
        return psi / norm if norm > 1e-9 else psi

    @property
    def psi_0(self) -> np.ndarray:
        return self._psi_0.copy()

    def consonance(self, vector: np.ndarray, key_name: str) -> float:
        """Constitutional consonance: a 0.6 tonic + 0.4 sheaf-field blend, clamped to [0.2, 1.0]."""
        if key_name not in self.axis_names:
            key_name = "coherence"
        idx = self.axis_names.index(key_name)
        key_vec = self.axis_vectors[idx]
        key_sheave = self.axis_sheaves[idx]
        norm = np.linalg.norm(vector)
        if norm < 1e-9:
            return 0.0
        vec = vector / norm
        tonic = float(np.dot(vec, key_vec))
        field = 0.0
        for j in range(self.n_axes):
            sheave = self.axis_sheaves[j]
            field += self.consonance_matrix[key_sheave, sheave] * float(np.dot(vec, self.axis_vectors[j]))
        field /= self.n_axes
        return max(0.2, min(1.0, 0.6 * tonic + 0.4 * field))

    def curvature_vector(self) -> np.ndarray:
        return np.repeat(self.sheaf_curvature, 2)
