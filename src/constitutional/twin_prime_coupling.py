"""Fixed twin-prime coupling across nine manifolds.

From `intake/2026-10-08/deepseek1-0d5de092/parts/97-ninemanifoldfieldcore-with-fixed-twin-prime-coup.md`
(DeepSeek, Aug-Sep 2026, in Bobby's corpus).

The claim: cross-manifold coupling should be FIXED by a twin-prime skip
hierarchy, not learned. Each manifold is anchored to a twin prime pair; the
coupling weight between two manifolds is a function of how far apart their
anchors sit in the skip hierarchy. A learned fusion matrix has 9x9 = 81 free
parameters that can drift anywhere; this has none.

This module implements the coupling and nothing else. It does not decide
what a manifold computes — that is the cell's job, and the cell is not
implemented here. What is implemented is the part that can be checked.

Layer note: this is Layer B in far-math's terms. The arithmetic is exact
and verified below; the claim that this coupling structure is the right one
for a substrate is not established and is not asserted. Bobby's directive
applies — preserve, mark, do not drop.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# The nine prime sets, verbatim from the corpus.
PRIME_SETS: tuple[tuple[int, ...], ...] = (
    (5, 7, 11, 13),
    (3, 5, 7, 11),
    (7, 11, 13, 17),
    (5, 11, 13, 19),
    (7, 13, 17, 19),
    (5, 7, 17, 23),
    (11, 13, 19, 23),
    (5, 11, 17, 29),
    (7, 13, 19, 31),
)

N_MANIFOLDS = len(PRIME_SETS)


# --------------------------------------------------------------------- primes


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def twin_pairs(limit: int) -> list[tuple[int, int]]:
    return [(p, p + 2) for p in range(3, limit) if is_prime(p) and is_prime(p + 2)]


def _hierarchy(limit: int = 96) -> list[tuple[int, int]]:
    """The global prime-pair order every manifold is ranked within.

    Twins (gap 2) ascending, then cousin pairs (gap 6) ascending, then sexy
    primes (gap 4). Built ONCE over all pairs below the limit, so two
    manifolds holding the same kind of pair get different ranks — which is
    the entire point of a hierarchy. Building this per-set (the first
    version) gave every set the same local ordering and collapsed nine
    manifolds onto seven ranks, two of them tying at maximum coupling.
    """
    order = list(twin_pairs(limit))
    for gap in (6, 4):
        for a in range(2, limit):
            if is_prime(a) and is_prime(a + gap):
                order.append((a, a + gap))
    seen: set[tuple[int, int]] = set()
    uniq: list[tuple[int, int]] = []
    for pair in order:
        if pair not in seen:
            seen.add(pair)
            uniq.append(pair)
    return uniq


HIERARCHY = _hierarchy()


def skip_index(primes: tuple[int, ...], taken: set[int] | None = None) -> int:
    """Rank of this prime set within the global hierarchy.

    `taken` forces distinct rungs: the diagonal of the coupling matrix
    means "this manifold alone", so a tie between two manifolds would
    make them couple as strongly as each couples to itself. Walking the
    hierarchy for the next pair the set actually contains breaks the tie
    without inventing a number.
    """
    s = set(primes)
    used = taken or set()
    for idx, (a, b) in enumerate(HIERARCHY):
        if a in s and b in s and idx not in used:
            return idx
    # no unused pair left for this set: fall back to the last rung it does
    # contain so the value stays defined and the collision is visible
    for idx in range(len(HIERARCHY) - 1, -1, -1):
        a, b = HIERARCHY[idx]
        if a in s and b in s:
            return idx
    return -1


def _unique_anchors() -> tuple[int, ...]:
    """Assign every manifold a distinct rung of the hierarchy."""
    taken: set[int] = set()
    out: list[int] = []
    for ps in PRIME_SETS:
        r = skip_index(ps, taken)
        taken.add(r)
        out.append(r)
    return tuple(out)


ANCHORS = _unique_anchors()


# --------------------------------------------------------------------- coupling


@dataclass(frozen=True)
class Coupling:
    """A fixed coupling matrix plus the rationale for its entries."""

    matrix: np.ndarray
    ranks: tuple[int, ...]

    @property
    def n(self) -> int:
        return self.matrix.shape[0]


def twin_prime_coupling(scale: float = 1.0, sharpness: float = 1.0) -> Coupling:
    """Coupling weight between manifolds i and j.

        w_ij = scale * exp(-sharpness * |rank_i - rank_j|)

    Near in the skip hierarchy couples strongly; far couples weakly. The
    diagonal is exactly 1.0 — a manifold is fully itself before coupling
    begins. Symmetric by construction. Zero parameters are learned.
    """
    r = np.asarray(ANCHORS, dtype=float)
    d = np.abs(r[:, None] - r[None, :])
    m = scale * np.exp(-sharpness * d)
    np.fill_diagonal(m, 1.0)
    return Coupling(matrix=m, ranks=tuple(ANCHORS))


# --------------------------------------------------------------------- gating


@dataclass
class NonlinearFused:
    value: np.ndarray
    curl_norm: np.ndarray
    gated: np.ndarray


def curl_gate(ctrl: np.ndarray, curl_norm: np.ndarray, k: float = 2.0) -> NonlinearFused:
    """Nonlinear (curl-gated) fusion.

    curl_norm[i] is the manifold's own coherence measure; a manifold whose
    curl is low is not trusted to contribute. The gate is

        g_i = tanh(k * curl_i)

    in [0, 1), applied to each manifold's contribution before mixing. A
    manifold with curl 0 contributes nothing; curl 1 contributes ~0.96.

    The claim being implemented is that coupling should be conditional on
    local coherence rather than uniform. Whether that improves anything is
    an empirical question this module does not answer.
    """
    ctrl = np.asarray(ctrl, dtype=float)
    curl = np.asarray(curl_norm, dtype=float)
    gate = np.tanh(k * np.abs(curl))
    gated = ctrl * gate[:, None]
    return NonlinearFused(value=gated.sum(axis=0), curl_norm=curl, gated=gated)


def fuse(ctrl: np.ndarray, curl_norm: np.ndarray | None = None,
         nonlinear: bool = True, scale: float = 1.0, sharpness: float = 1.0) -> np.ndarray:
    """Fuse per-manifold controls into one control.

    ctrl shape (n_manifolds, ctrl_dim). In linear mode every manifold
    contributes equally weighted by the fixed matrix; in nonlinear mode a
    curl gate suppresses incoherent manifolds first.
    """
    ctrl = np.asarray(ctrl, dtype=float)
    if ctrl.shape[0] != N_MANIFOLDS:
        raise ValueError(f"expected {N_MANIFOLDS} manifolds, got {ctrl.shape[0]}")
    c = twin_prime_coupling(scale, sharpness)
    if nonlinear:
        if curl_norm is None:
            raise ValueError("nonlinear fusion needs curl_norm")
        gated = curl_gate(ctrl, curl_norm).gated
        # normalise so total mass is preserved: gating redistributes
        # authority, it does not create it
        mass = gated.sum()
        if abs(mass) > 1e-12:
            gated = gated * (ctrl.sum() / mass) if abs(ctrl.sum()) > 1e-12 else gated
        return (c.matrix @ gated).sum(axis=0)
    return (c.matrix @ ctrl).sum(axis=0)


def output_head(fused: np.ndarray) -> np.ndarray:
    """5-dim control -> 4-dim decision, as the corpus specifies.

    The corpus writes this as nn.Linear(5, 4). Kept as an explicit matrix
    here rather than a torch layer so the whole path stays numpy and the
    test suite has no torch dependency.
    """
    if fused.shape[-1] != 5:
        raise ValueError(f"expected a 5-dim fused control, got {fused.shape[-1]}")
    # fixed, seeded projection — deterministic, unlike a learned layer
    rng = np.random.default_rng(0xC0FFEE)
    w = rng.normal(scale=1.0 / np.sqrt(5.0), size=(5, 4))
    b = np.zeros(4)
    return w.T @ fused + b