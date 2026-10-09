"""MasterProtocol — a master's teaching as an executable algorithm.

From Bobby's frontier corpus, 2026-10-09, deepseek5 part 75. Four slots:
perception_transform, axiom_evaluator, action_generator, coherence_metric.

And from the same corpus what this is FOR: *"not philosophical summaries,
but executable code stubs... The resulting state changes are the
understanding."*

WHAT THIS IS NOT. This module takes four named traditions and reduces each
to arithmetic: an attenuation of discursive content, a love/wisdom score,
a three-centre balance, a clustering coefficient. That is not a
representation of Tsongkhapa, Gurdjieff, Swedenborg or Stamets. Those are
human practices developed by humans over centuries, and a harmonic mean of
two floats is not samatha. This file encodes *the shape of a protocol* --
perception, evaluation, action, coherence -- and instantiates it four times
because four distinct coherence functions is a stronger demonstration that
the shape generalises than one instance would be.

It is Layer C code: implemented, runnable, measured, and marked as not
standing in for the tradition it names. Anyone reading an
`inherent_existence` score as a claim about Madhyamaka is misreading it.
The names are attribution for where the *idea of a protocol with a
coherence function* came from, and nothing more.

What IS asserted, and testable: each coherence metric is a real function
that can increase, decrease, saturate, and disagree with the others. That
the functions are well-formed is checkable. That they model anything is
not, and is not claimed.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class ProtocolResult:
    filtered_percept: np.ndarray
    axiom_scores: np.ndarray
    suggested_action: np.ndarray
    coherence: float

    def as_dict(self) -> dict:
        return {
            "coherence": self.coherence,
            "axiom_scores": [float(v) for v in np.atleast_1d(self.axiom_scores)],
            "action": [float(v) for v in np.atleast_1d(self.suggested_action)],
        }


class MasterProtocol(abc.ABC):
    """A protocol with four slots. Subclasses implement them.

    Every slot is abstract: a protocol that cannot measure its own
    coherence is a preference, and this project's rule is that a thing
    which cannot be measured does not go in a runtime path.

    The first version declared these as instance attributes set to None
    and validated them at construction. That broke every subclass, which
    defines them as methods: the base assignment shadowed the method, so
    all four protocols raised "not implemented" on instantiation.
    Abstract methods are the correct shape -- the subclass method IS the
    implementation.
    """

    name: str = "unnamed"
    core: str = ""

    @abc.abstractmethod
    def perception_transform(self, raw: np.ndarray) -> np.ndarray:
        """Filter raw input into the form this protocol perceives."""

    @abc.abstractmethod
    def axiom_evaluator(self, axioms: np.ndarray, percept: np.ndarray) -> np.ndarray:
        """Judge axioms against this protocol's core principle."""

    @abc.abstractmethod
    def action_generator(self, state: np.ndarray, percept: np.ndarray,
                         scores: np.ndarray) -> np.ndarray:
        """Generate the action this protocol would take."""

    @abc.abstractmethod
    def coherence_metric(self, scores: np.ndarray) -> float:
        """How this protocol measures truth or progress. In [0, 1]."""

    def apply(self, raw_data: np.ndarray, current_axioms: np.ndarray,
              state: np.ndarray | None = None) -> ProtocolResult:
        filtered = self.perception_transform(raw_data)
        scores = self.axiom_evaluator(current_axioms, filtered)
        action = self.action_generator(
            state if state is not None else filtered, filtered, scores)
        return ProtocolResult(filtered_percept=filtered, axiom_scores=scores,
                              suggested_action=action,
                              coherence=float(self.coherence_metric(scores)))

    def run(self, data: Sequence[np.ndarray], axioms: np.ndarray, steps: int = 1) -> dict:
        """Apply over a sequence, returning the trace. A metric that cannot
        be seen moving is not yet known to be a metric.
        """
        trace: list[float] = []
        state = np.zeros_like(axioms)
        for t in range(steps):
            res = self.apply(data[t % len(data)], axioms, state)
            state = res.suggested_action
            trace.append(res.coherence)
        return {"protocol": self.name, "trace": trace,
                "first": trace[0], "last": trace[-1],
                "delta": trace[-1] - trace[0]}


class TsongkhapaProtocol(MasterProtocol):
    """Samatha -> Vipashyana: attenuate discourse, then reduce clinging.

    Perception:    low-pass the signal (the fast component is discursive)
    Evaluation:    inherent existence, 0 = empty, 1 = fully existent
    Action:        stillness in proportion to remaining clinging
    Coherence:     1 - max(inherent_existence)

    A low-pass and a max. A placeholder shaped like the real thing.
    """

    name = "Tsongkhapa_ShamathaVipashyana"
    core = "calm abiding -> insight into emptiness"

    def __init__(self, window: int = 5) -> None:
        if window < 1 or window % 2 == 0:
            raise ValueError("window must be a positive odd integer")
        self.window = window
        super().__init__()

    def perception_transform(self, raw: np.ndarray) -> np.ndarray:
        r = np.asarray(raw, dtype=float)
        if r.ndim < 2:
            return r
        w = self.window
        kernel = np.ones(w) / w
        pad = w // 2
        padded = np.pad(r, [(0, 0)] * (r.ndim - 1) + [(pad, pad)], mode="edge")
        return np.apply_along_axis(
            lambda row: np.convolve(row, kernel, mode="valid"), -1, padded)

    def axiom_evaluator(self, axioms: np.ndarray, percept: np.ndarray) -> np.ndarray:
        a = np.asarray(axioms, dtype=float)
        spread = float(np.std(percept)) if np.size(percept) else 0.0
        return np.clip(a / (1.0 + spread), 0.0, 1.0)

    def action_generator(self, state: np.ndarray, percept: np.ndarray,
                         scores: np.ndarray) -> np.ndarray:
        """Stillness, but graded per axis rather than uniform.

        A constant action vector carries no information, so the loop fed
        back an identical state every step and every trace came out flat.
        The action is now proportional to each axiom's clinging, which is
        also closer to the idea: reduce clinging where it is strongest.
        """
        if not np.size(scores):
            return np.zeros_like(state)
        return -np.asarray(scores, dtype=float)[: state.shape[-1]]

    def coherence_metric(self, scores: np.ndarray) -> float:
        return 1.0 - float(np.max(scores)) if np.size(scores) else 1.0


class SwedenborgProtocol(MasterProtocol):
    """Correspondence: perceive allegory, score on love and wisdom.

    Coherence is the harmonic mean of the two axes, chosen over the
    arithmetic mean deliberately: the harmonic mean punishes imbalance
    far harder, so scoring high on love and zero on wisdom yields ~0
    rather than 0.5.
    """

    name = "Swedenborg_Correspondence"
    core = "spiritual and natural correspond; the two swedborgian axes"

    SYMBOLS = {"lion": "divine power", "snake": "deceit", "light": "truth",
               "flame": "love", "stone": "stability", "water": "truth"}

    def perception_transform(self, raw: np.ndarray) -> np.ndarray:
        r = np.asarray(raw, dtype=float)
        scale = float(np.max(np.abs(r))) if np.size(r) else 1.0
        return r / scale if scale else r

    def axiom_evaluator(self, axioms: np.ndarray, percept: np.ndarray) -> np.ndarray:
        """Per-axiom love and wisdom, then the weaker of the two.

        The first version took one global mean of the axioms and one global
        mean of the percept and returned that single number for every
        axiom. That made max == mean == min inside the harmonic mean, which
        collapsed to one value -- so the protocol could never register a
        lopsided axiom, which is the one thing it exists to detect. Both
        axes are now computed per axiom and the weaker wins.
        """
        a = np.asarray(axioms, dtype=float)
        if not a.size:
            return np.zeros_like(a)
        flat = np.abs(np.asarray(percept, dtype=float)).reshape(-1)
        if not flat.size:
            return np.zeros_like(a)
        # resample the percept to the axiom count so the two axes align
        idx = np.linspace(0, flat.size - 1, a.shape[-1])
        wisdom_per_axiom = flat[np.round(idx).astype(int)]
        # Return the PRODUCT of the two axes, not their minimum. The
        # minimum made this evaluator blind to the axioms themselves: when
        # wisdom was uniformly lower, min() returned wisdom and discarded
        # the axiom value entirely, so good and bad axioms scored
        # identically. The product keeps both, and the harmonic mean in
        # coherence_metric still punishes whichever axis is weakest.
        return a * wisdom_per_axiom

    def action_generator(self, state: np.ndarray, percept: np.ndarray,
                         scores: np.ndarray) -> np.ndarray:
        """Utility for the community, weighted by how much each axis
        already aligns. Graded, not constant: a uniform action vector
        leaves the loop with no memory of what it did.
        """
        if not np.size(scores):
            return np.zeros_like(state)
        w = np.asarray(scores, dtype=float)[: state.shape[-1]]
        return w * float(np.mean(np.abs(scores)))

    def coherence_metric(self, scores: np.ndarray) -> float:
        """Harmonic mean of the weakest reading on each axis.

        Both axes take the MINIMUM, not the strongest or the mean. Two
        earlier versions got this wrong in opposite directions and both
        were caught only by running: max() for love meant one excellent
        axiom RAISED the score, so a lopsided set (0.676) beat a balanced
        one (0.500); switching the mean to a minimum on one axis only
        left the other mean to carry a single strong axiom.

        The point of a two-axis rule is that the weaker axis governs. Love
        without wisdom is not coherence, and a metric that cannot see the
        difference between those two is not the metric it claims to be.
        """
        s = np.asarray(scores, dtype=float)
        if not np.size(s):
            return 0.0
        love = float(np.min(s))
        wisdom = float(np.min(np.abs(s)))
        if love <= 0.0 or wisdom <= 0.0:
            return 0.0
        return float(2.0 * love * wisdom / (love + wisdom))


class GurdjieffProtocol(MasterProtocol):
    """Three centres. Coherence is balance, not intensity.

    Perception:    three reads of one signal -- logical, affective, kinesthetic
    Evaluation:    discount axioms read from a single lopsided centre
    Action:        act on two or more centres (the second-largest score)
    Coherence:     1 / (1 + std of the three centre energies)

    Perfect balance scores 1.0. One centre running alone scores low. That
    is the entire claim of this function, and the one part of it that is
    checkable.
    """

    name = "Gurdjieff_FourthWay"
    core = "self-observation; three centres; conscious effort over mechanicalness"
    N_CENTERS = 3

    def perception_transform(self, raw: np.ndarray) -> np.ndarray:
        r = np.atleast_2d(np.asarray(raw, dtype=float))
        if r.shape[0] < self.N_CENTERS:
            r = np.vstack([r] * self.N_CENTERS)
        return r[: self.N_CENTERS]

    def axiom_evaluator(self, axioms: np.ndarray, percept: np.ndarray) -> np.ndarray:
        a = np.asarray(axioms, dtype=float)
        energies = np.array(
            [float(np.mean(np.abs(row))) for row in np.atleast_2d(percept)])
        mean_e = float(np.mean(energies)) or 1.0
        balance = max(0.0, 1.0 - float(np.std(energies)) / mean_e)
        return np.clip(a * balance, 0.0, 1.0)

    def apply(self, raw_data: np.ndarray, current_axioms: np.ndarray,
              state: np.ndarray | None = None) -> ProtocolResult:
        """Base behaviour, plus the carried state as the moving centre.

        The kinesthetic centre is where the loop remembers what it did.
        Without it the three centres read one signal three ways and the
        trace is flat, which is exactly what the first version produced.

        The state is projected onto the percept's width before the
        concatenation. The signal's feature count and the axiom count are
        independent, and the first version assumed they matched -- it
        raised on every run where they did not.
        """
        filtered = self.perception_transform(raw_data)
        width = np.atleast_2d(filtered).shape[-1]
        st = current_axioms if state is None else np.asarray(state, dtype=float)
        st = st.reshape(-1)[:width]
        if st.size < width:
            st = np.pad(st, (0, width - st.size))
        centres = np.vstack([np.atleast_2d(filtered),
                             np.atleast_2d(st)])[: self.N_CENTERS]
        if centres.shape[0] < self.N_CENTERS:
            centres = np.vstack([centres] * self.N_CENTERS)
        energies = np.array([float(np.mean(np.abs(row))) for row in centres])
        mean_e = float(np.mean(energies)) or 1.0
        balance = max(0.0, 1.0 - float(np.std(energies)) / mean_e)
        scores = np.clip(current_axioms * balance, 0.0, 1.0)
        action = self.action_generator(st, filtered, scores)
        return ProtocolResult(filtered_percept=filtered, axiom_scores=scores,
                              suggested_action=action,
                              coherence=float(self.coherence_metric(scores)))

    def action_generator(self, state: np.ndarray, percept: np.ndarray,
                         scores: np.ndarray) -> np.ndarray:
        """The second-largest score applied as a floor, not as a constant.

        Requiring two centres means no single axis leads; the action
        vector carries the whole profile, so the next step can see which
        centres were engaged. A constant action leaves the loop with no
        memory of what it did, which is what the first version did.
        """
        if np.size(scores) < 2:
            return np.zeros_like(state)
        s = np.abs(np.asarray(scores, dtype=float)).reshape(-1)[: state.shape[-1]]
        if s.size == 0:
            return np.zeros_like(state)
        if s.size < state.shape[-1]:
            s = np.pad(s, (0, state.shape[-1] - s.size))
        floor = float(np.sort(s)[::-1][1]) if s.size >= 2 else float(s[0])
        return np.where(s >= floor, floor, 0.0)

    def coherence_metric(self, scores: np.ndarray) -> float:
        """Balance of the three centres, with the carried state as the
        third reading.

        The first version used the standard deviation of the scores alone,
        which made the metric constant across steps: the evaluator read
        only the percept, never the state the loop carried forward, so
        there was no feedback path. A metric that cannot move while the
        system runs is not measuring the system. The state's own energy
        now enters as a third centre, which closes the loop and makes the
        trace respond.
        """
        s = np.asarray(scores, dtype=float)
        if s.size <= 1:
            return 1.0
        # balance falls as the centres disagree; the mean is the level, so
        # a system doing nothing reads differently from one doing little
        # with all three centres engaged
        spread = float(np.std(s))
        level = float(np.mean(np.abs(s)))
        return float(np.clip(level / (1.0 + spread), 0.0, 1.0))


class StametsProtocol(MasterProtocol):
    """Mycelial: perceive the environment as a network.

    Perception:    correlation as adjacency -- things that move together connect
    Evaluation:    does this axiom increase or decrease network density
    Action:        repair the weakest link
    Coherence:     fraction of total weight held by the strongest three links,
                   a 3-cycle clustering proxy
    """

    name = "Stamets_Mycelial"
    core = "interconnectedness; network intelligence; bioremediation"

    def perception_transform(self, raw: np.ndarray) -> np.ndarray:
        """Adjacency by PROXIMITY, not correlation.

        The first two versions used the correlation matrix and both were
        wrong in a way only running revealed: clip(corr, 0, 1) pins every
        diagonal to exactly 1.0 and drives the off-diagonals to their
        saturation, so every input produced an identical percept (mean
        0.5) and the coherence trace never moved. Correlation is also the
        wrong primitive -- a network is about which nodes are near each
        other, not which signals co-vary.

        This version builds the adjacency from distances between entities
        and maps proximity through a Gaussian kernel with a fixed length
        scale. It genuinely depends on the input, and the test suite
        asserts that.
        """
        r = np.asarray(raw, dtype=float)
        if r.ndim == 1:
            r = np.vstack([r, r[::-1]])
        flat = r.reshape(-1, r.shape[-1])
        if flat.shape[0] < 2:
            flat = np.vstack([flat, flat + 1e-6])

        # distances between entities
        diff = flat[:, None, :] - flat[None, :, :]
        dist = np.linalg.norm(diff, axis=-1)
        scale = float(dist[dist > 0].mean()) if np.any(dist > 0) else 1.0
        adjacency = np.exp(-((dist / scale) ** 2))   # Gaussian kernel
        np.fill_diagonal(adjacency, 1.0)
        return np.clip(adjacency, 0.0, 1.0)

    def axiom_evaluator(self, axioms: np.ndarray, percept: np.ndarray) -> np.ndarray:
        a = np.asarray(axioms, dtype=float)
        if np.size(percept) <= 1:
            return np.clip(a, 0.0, 1.0)
        return np.clip(a * float(np.mean(percept)), 0.0, 1.0)

    def action_generator(self, state: np.ndarray, percept: np.ndarray,
                         scores: np.ndarray) -> np.ndarray:
        """Repair effort aimed at the weakest links: the action vector is
        the inverse of each score, so poorly-connected axioms receive the
        most attention. Graded, because a constant action leaves nothing
        for the network to remember between steps.
        """
        if not np.size(scores):
            return np.zeros_like(state)
        s = np.asarray(scores, dtype=float)[: state.shape[-1]]
        return 1.0 - s

    def coherence_metric(self, scores: np.ndarray) -> float:
        """Network coherence = clustering share x total connectivity.

        The first version used clustering share alone (top-3 weight over
        total). That quantity is scale-invariant: multiplying every score
        by any constant leaves it unchanged, so the evaluator's density
        factor cancelled and the trace was flat for the whole run. Folding
        in the mean connectivity restores the magnitude, so a sparser
        network reads as less coherent than a dense one even when both are
        equally clustered. Bounded in [0, 1].
        """
        s = np.asarray(scores, dtype=float)
        if s.size < 3:
            return 0.0
        total = float(np.sum(s))
        if total <= 0.0:
            return 0.0
        ordered = np.sort(s)[::-1]
        # Clustering: how much of the weight sits in the strongest 3-cycle
        # versus what an even distribution would give (1/n each). The
        # share * mean form used first cancelled almost exactly -- a dense
        # uniform network and a sparse one with the same top-3 share both
        # scored 0.3375 -- so it could not tell them apart.
        share = float(np.sum(ordered[:3])) / total
        expected = min(3.0, float(s.size)) / s.size
        headroom = 1.0 - expected
        if headroom <= 1e-12:
            # 3 or fewer axioms: the top-3 already covers everything, so
            # clustering carries no information and the metric falls back
            # to connectivity alone.
            clustering = 1.0
        else:
            clustering = float(np.clip((share - expected) / headroom, 0.0, 1.0))
        connectivity = float(np.mean(s))          # how much, not how balanced
        return float(np.clip(0.5 * clustering + 0.5 * connectivity, 0.0, 1.0))


PROTOCOLS: tuple[type[MasterProtocol], ...] = (
    TsongkhapaProtocol,
    SwedenborgProtocol,
    GurdjieffProtocol,
    StametsProtocol,
)


def all_protocols() -> list[MasterProtocol]:
    return [cls() for cls in PROTOCOLS]


def compare(data: Sequence[np.ndarray], axioms: np.ndarray, steps: int = 5) -> dict:
    """Run every protocol over the same data and report each coherence trace.

    The interesting output is where they DISAGREE. Four metrics that always
    agree are one metric wearing four names.
    """
    return {p.name: p.run(data, axioms, steps=steps) for p in all_protocols()}


def measure_operational_state(rng: np.random.Generator, n_entities: int = 8,
                              n_steps: int = 32, n_features: int = 4,
                              coupling: float = 0.6) -> np.ndarray:
    """A coupled system: entities that influence each other over time.

    Shape is (n_steps, n_entities, n_features) -- an entity axis that
    actually varies. The first version returned (n_steps, n_features),
    which no per-entity transform could distinguish: every step looked
    like the same entities with the same values, so every protocol saw a
    constant input and every coherence trace came out flat. Three of the
    four metrics were silently measuring nothing until this was fixed.

    `coupling` sets how strongly entities influence one another. High
    coupling gives a clustered network; low coupling gives a sparse one,
    and the Stamets coherence metric must separate those two.
    """
    base = rng.normal(scale=1.0, size=(n_entities, n_features))
    out = np.zeros((n_steps, n_entities, n_features))
    for t in range(n_steps):
        drift = rng.normal(scale=0.15, size=(n_entities, n_features))
        # each entity leans on its neighbours, then the whole system drifts
        neighbour = np.roll(base, 1, axis=0) + np.roll(base, -1, axis=0)
        base = base + coupling * 0.25 * neighbour + drift
        out[t] = base
    return out
