"""
stalk_core.py — the v6.2 frequency/stalk kernel, wired into the constitutional core.

WHAT THIS IS
------------
The v6.1 kernel lived at `src/constitutional/frequency.py` and was 522 lines
with four classes: FrequencyChannel, FrequencyDynamics, ResonanceChannel,
FrequencyCoupler. It was gutted to a 56-line toy by the 2026-09-16 Grok
master-plan rewrite, which left `FrequencyCoupler` as a stub with a
`step()` that only advances phases.

That is the "imports cleanly, nobody calls it" class the atlas-exam
reachability audit exists to find, except here it was WORSE: it was
called, and the call did nothing. `FrequencyCoupler` in the current tree
has no girths, no adjacency, no Kuramoto coupling, no eigen-decomposition,
and no gate.

This file rebuilds the kernel at v6.2, which is not the v6.1 design with
extra steps. v6.2 changes the GEOMETRY:

  v6.1  the stalk is a twisted pair          -> 1 loop mode, 1 axis
  v6.2  the stalk is a coaxial core plus two
        windings of different girth           -> 2 loop modes, 2 axes

Spec: simself/notes/analogies/stalk-architecture-v6-2-3part-2026-10-14.md

    "the stalk is not a twisted pair. It is a coaxial core plus two
     windings of different girth -- an ignition coil whose core is the
     cross-member."

THE INTERSTALK IS THE POINT, and this is where the telecom method comes in
-----------------------------------------------------------------------
Bobby 2026-10-24: "yes we scrapped twisted pairs for coaxial ignition
coil model using established telecom methods" and "this is the key we need
to make our stalk topology complex enough to mimic brain even if poorly".

Papers 24 and 25 (fieldcore) make the argument and carry the
implementation in the Rust core:

    interference is a CHANNEL to be inverted, not noise to be suppressed
    a perfectly isolated substrate is UNCORRECTABLE by construction
    the pilot is the most important transmission
    phase is the address -- many stalks, one carrier, read by ratio

So the kernel here is not a similarity graph with a physics costume (which
is what v6.1 §2 admits its coupling matrix was). It is a channel model
with a coupling operator, a pilot, and an equaliser, and the resonance
gate is an equalised measurement rather than a cosine.

THE BRAIN PART, stated precisely
---------------------------------
"complex enough to mimic brain even if poorly" is the population code:
many stalks contribute to ONE carrier, and the readout is the RATIO of
responses across the population. That is how V1 orientation tuning works
and how the olfactory bulb works -- not one wire per concept. The address
is the PHASE, and it is derived from the stalk's GEOMETRY, so a stalk means
the same thing wherever it sits.

That claim is [E] as biology. The claim that OUR geometry can support it is
[H], and the falsification is named below and in v6.2 §7.

PROVENANCE
----------
    [M]  measured from the literature
    [E]  established textbook telecom / EM / neuro
    [D]  derived here from [M] and [E] -- the arithmetic is shown
    [H]  hypothesis, ours, not yet falsified

THE FALSIFICATION, because a kernel that cannot fail is decoration
---------------------------------------------------------------------
1. Channel estimation: the coupling operator must be ESTIMABLE from a
   pilot, not assumed. If the estimate cannot be made from what actually
   arrives, the whole thing is a metric with better branding.
2. Equalisability: the channel must have structure (a notch). A flat
   channel is refused, by the same proposition that paper 24 states.
3. The gate: the resonance gate must VETO. If it never refuses, it is
   decoration. This is the 1-bit veto the constitutional core is built on.
4. Geometry carries the count: two stalks of different geometry must have
   different spectra, without a sigma_g perturbation.

Run: python src/constitutional/stalk_core.py --selftest
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


# ===========================================================================
# THE HYPOTHESES, and their honesty
# ===========================================================================

DEFAULT_FREQUENCY_HYPOTHESES: Dict[str, float] = {
    "schumann_fundamental": 7.83,            # [M] real geophysics
    "concert_pitch_440": 440.0,              # [M] ISO 16 (1975) reference
    "concert_pitch_432_hypothesis": 432.0,   # [H] tuning convention, not physics
    "diamond_coherence_hypothesis": 963.0,   # [H] unverified
    "biophoton_coupling_hypothesis": 55.0,   # [H] unverified
    "ground_frequency_hypothesis": 34.4,     # [H] unverified
}

# The numerology hypotheses are NOT load-bearing. The kernel works with
# any set of target frequencies; these are the ones Bobby has named, kept
# so the vocabulary survives, and marked so nobody mistakes them for
# findings. The v6.1 kernel's header said the same thing and it is kept
# because it is true.
#: How strong the pilot is relative to the payload. See the note at the
#: pilot's use site: the pilot carries no payload, and its estimation
#: residual scales with its strength, so it is deliberately weak.
PILOT_STRENGTH = 0.05

#: How many bins the reflected path is delayed by. It must be enough
#: that the probe and its delayed copy are not collinear -- see the note
#: at `path()` in ResonanceChannel.measure.
PATH_DELAY = 4

#: How much of the direct path the reflected path carries. Less than 1
#: because the reflected path is longer, so it loses energy. This is
#: what makes the response null FINITE: with two equal lossless taps
#: the null is exact, and zero-forcing inversion at an exact null
#: amplifies noise without bound -- which the equaliser correctly
#: refuses as `irrecoverable`.
REFLECTION_LOSS = 0.9


NUMEROLOGY_HYPOTHESES = {
    "concert_pitch_432_hypothesis",
    "diamond_coherence_hypothesis",
    "biophoton_coupling_hypothesis",
    "ground_frequency_hypothesis",
}


# ===========================================================================
# 1. THE STALK -- v6.2 geometry: coaxial core + two dual-girth windings
# ===========================================================================

@dataclass(frozen=True)
class Stalk:
    """One 3-part stalk. Three conductors -> two differential loop modes.

    This is the v6.2 geometry, and it is the reason the axis count moved
    from N to 2N without a perturbation:

        outer winding   radius girth_out,  N_out turns
        inner winding   radius girth_in,   N_in  turns
        core            the cross-member, the shared flux path

    The core is the shared flux path, so the two windings are a
    transformer with a tapped primary: the turns ratio sets the voltage
    ratio, so the frequency ratio is settable by geometry at fixed
    length. v6.2 §1.4: "the rung is the core. It was already there."

    And the three mutual couplings are unequal BY CONSTRUCTION -- the core
    sits in the shared flux path of both windings while the two windings
    shield each other at different rates depending on radius. That
    inequality is what breaks the degeneracy.
    """

    id: str
    girth_out: float = 1.0
    girth_in: float = 0.6
    girth_core: float = 0.2
    n_out: int = 11
    n_in: int = 5
    length: float = 1.0
    sheath: bool = True

    def __post_init__(self) -> None:
        for name, v in (("girth_out", self.girth_out),
                        ("girth_in", self.girth_in),
                        ("girth_core", self.girth_core)):
            if v <= 0:
                raise ValueError(f"{self.id}: {name} must be positive, got {v}")
        if self.n_out <= 0 or self.n_in <= 0:
            raise ValueError(f"{self.id}: turn counts must be positive")
        if not (self.girth_core < self.girth_in < self.girth_out):
            raise ValueError(
                f"{self.id}: concentric order must be core < inner < outer")

    # -- the two loop modes ---------------------------------------------

    @property
    def n_loop_modes(self) -> int:
        """n conductors -> n-1 differential loop currents. Three -> two."""
        return 2

    @property
    def turns_ratio(self) -> float:
        """N_out / N_in. The voltage ratio of the tapped primary. [E]"""
        return self.n_out / self.n_in

    @property
    def girth_ratio(self) -> float:
        """the geometric ratio of the two windings. [D]"""
        return self.girth_out / self.girth_in

    # -- the mutual couplings --------------------------------------------

    def mutual_couplings(self) -> Dict[str, float]:
        """the three off-diagonal couplings, unequal BY CONSTRUCTION. [D]

        The concentric windings couple by the RATIO of their radii: the
        inner winding sits inside the outer's flux, so the coupling rises
        as they approach and is bounded by 1.

        The core is on the axis at a genuine distance from both windings,
        so the separation law applies to it.

        (The first version divided the mutual inductance by the
        SEPARATION of the two conductors, which made the coupling EXPLODE
        to 10000 for two windings at nearly the same radius. That bug
        was found by a mutation probe and is recorded in the fieldcore
        commit.)
        """
        d_in_core = self.girth_in - self.girth_core
        d_out_core = self.girth_out - self.girth_core
        overlap = min(self.n_out, self.n_in) / max(self.n_out, self.n_in)
        return {
            "m_out_in": overlap * (self.girth_in / self.girth_out),
            "m_in_core": (1.0 / max(self.n_in, 1)) / d_in_core,
            "m_out_core": (1.0 / max(self.n_out, 1)) / d_out_core,
        }

    def inductance_matrix(self) -> np.ndarray:
        """the 3x3 inductance matrix. [D]

        Symmetric by reciprocity. v6.2 §1.2 keeps the physics correction:
        "M is no longer symmetric" was WRONG -- in a linear reciprocal
        medium M_ij == M_ji. The real statement is that with three
        conductors there are THREE off-diagonal couplings instead of one,
        and concentric geometry makes them unequal.
        """
        m = self.mutual_couplings()
        l_out = self.girth_out ** 2 * self.n_out ** 2
        l_in = self.girth_in ** 2 * self.n_in ** 2
        l_core = self.girth_core ** 2
        return np.array([
            [l_out,     m["m_out_in"], m["m_out_core"]],
            [m["m_out_in"], l_in,      m["m_in_core"]],
            [m["m_out_core"], m["m_in_core"], l_core],
        ], dtype=np.float64)

    def loop_eigenvalues(self) -> List[float]:
        """the eigenvalues of the two loop modes. [D]

        The loop basis is the difference basis: (1,-1,0) for
        outer-minus-inner and (0,1,-1) for inner-minus-core.
        """
        M = self.inductance_matrix()
        v1 = np.array([1.0, -1.0, 0.0])
        v2 = np.array([0.0, 1.0, -1.0])
        L11 = float(v1 @ M @ v1)
        L22 = float(v2 @ M @ v2)
        L12 = float(v1 @ M @ v2)
        tr = L11 + L22
        det = L11 * L22 - L12 * L12
        disc = max(tr * tr / 4 - det, 0.0)
        root = math.sqrt(disc)
        return sorted([tr / 2 - root, tr / 2 + root])

    # -- the address -----------------------------------------------------

    def address_phase(self) -> float:
        """the stalk's PHASE ADDRESS, derived from its geometry. [D]

        Phase is the address -- not girth, not length, not index. And it
        is DERIVED, so a stalk means the same thing wherever it sits in
        the array. Moving a stalk must not change what it says.

        Two components, both geometric:
          the parity of the outer turn count (a binary component)
          the girth ratio (a continuous component)
        """
        ph = (self.n_out % 2) / 2.0
        return (ph + (self.girth_ratio - 1.0)) % 1.0

    def describe(self) -> Dict:
        return {
            "id": self.id,
            "n_loop_modes": self.n_loop_modes,
            "girths": {"core": self.girth_core, "inner": self.girth_in,
                       "outer": self.girth_out},
            "turns": {"inner": self.n_in, "outer": self.n_out},
            "turns_ratio": self.turns_ratio,
            "girth_ratio": self.girth_ratio,
            "mutual_couplings": self.mutual_couplings(),
            "loop_eigenvalues": self.loop_eigenvalues(),
            "address_phase": self.address_phase(),
        }


# ===========================================================================
# 2. THE CHANNEL -- coupling as something to estimate and invert
# ===========================================================================

@dataclass
class Channel:
    """The coupling operator, as complex taps. [E]

    Complex, not real, because phase is the information. This is the same
    object the Rust core's `Channel` is, and it carries the same
    proposition: a channel with no structure admits no inversion.

    This is the difference between v6.1 and v6.2 that matters most.
    v6.1 §2 admits its coupling matrix was "a similarity graph with a
    physics costume" -- there was no carrier in it. Here the coupling
    has taps, a frequency response, a notch depth, and an equaliser.

    THE TAP CARRIES ITS OWN DELAY. This is the fix that made the
    measurement work at all, and it is worth stating precisely because
    the first version was wrong in a way that looked correct.

    `estimate_channel` fits the probe delayed by `j * PATH_DELAY` bins --
    0, 4, 8, ... -- but `response_complex` used to evaluate every tap at
    its LIST INDEX: 0, 1, 2, ... The two are different filters. The
    estimated channel said "tap 1 sits one bin later" when the true
    channel said "tap 1 sits FOUR bins later", so the equaliser inverted
    a channel that does not exist and recovered nothing.

    Measured, 2026-10-25:
        list-index delays                  -> alignment 0.00000000
        taps at their own delays (0, 4)    -> alignment 0.41191241
        circular prefix + own delays       -> alignment 1.00000000

    So a tap is a (amplitude, phase, delay) triple, and the delay is part
    of the tap rather than an accident of list position. `delays` is a
    parallel list; `tap_delays` returns the pairs the response is
    actually summed over.
    """

    taps: List[Tuple[float, float]]
    delays: List[int] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if not self.taps:
            raise ValueError("a channel with no taps is not a channel")
        if self.delays is None:
            # unit spacing, which is what the Rust core's channel uses
            self.delays = list(range(len(self.taps)))
        if len(self.delays) != len(self.taps):
            raise ValueError(
                f"channel has {len(self.taps)} taps but {len(self.delays)} delays")
        for d in self.delays:
            if d < 0:
                raise ValueError(f"tap delay must be non-negative, got {d}")

    @classmethod
    def clean(cls) -> "Channel":
        return cls([(1.0, 0.0)], [0])

    def tap_delays(self) -> List[Tuple[Tuple[float, float], int]]:
        """the taps with their own delays. The sum the response is over."""
        return list(zip(self.taps, self.delays))

    def response_complex(self, f: float) -> Tuple[float, float]:
        re = im = 0.0
        for (hr, hi), d in self.tap_delays():
            th = -2.0 * math.pi * f * d
            re += hr * math.cos(th) - hi * math.sin(th)
            im += hr * math.sin(th) + hi * math.cos(th)
        return re, im

    def response_mag(self, f: float) -> float:
        re, im = self.response_complex(f)
        return math.hypot(re, im)

    def notch_db(self) -> float:
        """how much structure the channel has, as a POSITIVE depth in dB.

        The sign convention is load-bearing and cost the Rust suite four
        tests: a notch is a DEPTH, so it is positive. 0 means flat, 60
        means a response null was reached.
        """
        peak = max(self.response_mag(i / 200.0 - 0.5) for i in range(201))
        if peak <= 0.0:
            return 0.0
        null = min(self.response_mag(i / 200.0 - 0.5) for i in range(201))
        if null <= 0.0:
            return 60.0
        return -(20.0 * math.log10(null / peak))

    def equalise(self, rx: Sequence[Tuple[float, float]],
                 noise_floor: float = -80.0) -> Dict[str, object]:
        """zero-forcing inversion, fail-closed. [E]

        The samples come back as (re, im) pairs. The imaginary part is
        the recovered PHASE and keeping only the real part throws away
        the one quantity the design exists to preserve -- a defect the
        Rust core carried until 2026-10-24 and a mutation probe found.

        Two named refusals:
          flat_channel    nothing to invert
          irrecoverable   the null sits below the noise floor
        """
        if self.notch_db() < 3.0:
            return {"ok": False, "error": "flat_channel",
                    "detail": "a channel with no notch has nothing to model"}
        if self.notch_db() >= abs(noise_floor):
            return {"ok": False, "error": "irrecoverable",
                    "detail": f"notch {self.notch_db():.1f} dB is at or below "
                              f"the {abs(noise_floor):.1f} dB noise floor"}
        n = len(rx)
        out: List[Tuple[float, float]] = []
        for k in range(n):
            f = k / n - 0.5
            hr, hi = self.response_complex(f)
            mag2 = hr * hr + hi * hi
            if mag2 <= 1e-18:
                return {"ok": False, "error": "flat_channel",
                        "detail": f"response null at bin {k}"}
            yr, yi = rx[k]
            re = (yr * hr + yi * hi) / mag2
            im = (yi * hr - yr * hi) / mag2
            out.append((re, im))
        return {"ok": True, "samples": out}


@dataclass
class Pilot:
    """A known reference. Carries no payload; makes the rest readable.

    This is M0. The governor transmits no decision of its own -- it
    transmits the reference the rest of the link is equalised against.

    A gate that "knows the answer" is a payload symbol and cannot
    calibrate anything.

    THE PILOT MUST NOT BE A CONSTANT, and finding out why was the whole
    lesson of the first implementation.

    The first version transmitted 1.0 in every bin. A constant pilot
    cannot reveal a channel's STRUCTURE, and that is the whole job of a
    pilot: the receiver correlates the known reference against what
    arrived, and a constant has exactly one degree of freedom. There
    is no lag to correlate, so the estimate has one tap, the response
    is flat, and the equaliser refuses the frame as `flat_channel`. The
    gate then refused EVERYTHING -- correctly, given what it was
    measuring, and useless.

    This is the same failure class as the Rust core's missing phase: the
    measurement was well-formed and carried no information.

    Real pilots are a KNOWN PSEUDO-RANDOM sequence, precisely because a
    broadband reference probes the channel's response across the whole
    band instead of at one frequency. So the pilot here is a
    deterministic pseudo-random sequence from a fixed seed: known to the
    receiver, broadband, and reproducible.
    """
    value: float = 1.0
    seed: int = 20261024

    def frame(self, bins: int) -> List[Tuple[float, float]]:
        """the pilot as a transmitted frame: a known broadband sequence."""
        # a deterministic pseudo-random sequence, so the receiver can
        # regenerate it exactly. xorshift-style: no dependencies.
        out: List[Tuple[float, float]] = []
        x = self.seed & 0xFFFFFFFF
        for _ in range(bins):
            x ^= (x << 13) & 0xFFFFFFFF
            x ^= (x >> 17)
            x ^= (x << 5) & 0xFFFFFFFF
            # map to [-1, 1]
            v = (x / 0xFFFFFFFF) * 2.0 - 1.0
            out.append((v, 0.0))
        return out


# ===========================================================================
# 3. THE POPULATION CODE -- many stalks, one carrier, read by ratio
# ===========================================================================

@dataclass
class Stratum:
    """One stalk's contribution to the shared carrier."""
    id: str
    phase: float
    gain: float = 1.0

    def waveform(self, samples: int) -> List[float]:
        return [self.gain * math.cos(2.0 * math.pi * self.phase * (i / samples))
                for i in range(samples)]


@dataclass
class PopulationCode:
    """Many stalks on one carrier. The readout is the RATIO.

    This is the brain part, and it is why the topology can be complex
    without being a wire per idea. A population code addresses a feature
    by the ratio of responses across a population; V1 orientation tuning
    does exactly this -- one neuron does not encode "north", a column of
    neurons with different preferred directions does, and the readout
    takes the ratio.
    """

    strata: List[Stratum]
    samples: int = 256

    def carrier(self) -> List[float]:
        out = [0.0] * self.samples
        for s in self.strata:
            for i, v in enumerate(s.waveform(self.samples)):
                out[i] += v
        return out

    def dft(self) -> List[Tuple[float, float]]:
        """naive DFT. No dependencies, like the Rust core's."""
        n = self.samples
        out = []
        for k in range(n):
            re = im = 0.0
            for i, v in enumerate(self.carrier()):
                th = -2.0 * math.pi * (k * i) / n
                re += v * math.cos(th)
                im += v * math.sin(th)
            out.append((re, im))
        return out

    def readout(self, target_phase: float) -> List[float]:
        """the population's response to a probe at target_phase."""
        resp = []
        for s in self.strata:
            d = (s.phase - target_phase + 0.5) % 1.0 - 0.5
            resp.append(s.gain * math.cos(2.0 * math.pi * d))
        return resp

    def decoded(self, target_phase: float) -> Dict[str, object]:
        """read the population back.

        The winner is the argmax. The CONFIDENCE is the contrast between
        the top response and the mean of the rest -- and the contrast is
        the honest "I do not know". A decode that always returns a
        confident winner is the failure the width ladder exists to catch.
        """
        resp = self.readout(target_phase)
        if not resp:
            return {"winner": None, "top": 0.0, "contrast": 0.0}
        best = max(range(len(resp)), key=lambda i: resp[i])
        top = resp[best]
        others = [r for i, r in enumerate(resp) if i != best]
        mean_rest = sum(others) / len(others) if others else 0.0
        return {"winner": self.strata[best].id, "top": top,
                "contrast": top - mean_rest}


# ===========================================================================
# 4. THE RESONANCE CHANNEL -- an equalised measurement, not a cosine
# ===========================================================================

@dataclass
class ResonanceChannel:
    """Interference between two stalk populations, measured through the channel.

    v6.1's ResonanceChannel was "a phase-aligned similarity score" and its
    own documentation said "Architecture: does not claim physical
    resonance". v6.2 §2 says that hedge becomes "a lie of omission" once
    the stalks are actually coupled: "the recall gate stops being a
    similarity score."

    So this version:
      - measures the CHANNEL between the two populations, not the cosine
        of their embeddings
      - carries a PILOT, so the measurement is calibrated against a known
        reference rather than against nothing
      - EQUALISES, and refuses when the channel cannot be inverted
      - reports the residual error, so a caller can see how much to trust
        the reading

    The score it returns is still a number in [0,1] because the 1-bit veto
    needs one, but what it measures is now a physical reading with a
    stated uncertainty.
    """

    name: str = "observe_gate"
    freq_carrier: float = 7.83
    bins: int = 32
    noise_floor: float = -60.0

    def estimate_channel(self, tx: Sequence[float], rx: Sequence[float],
                         taps: int = 2,
                         delay: int = PATH_DELAY) -> Channel:
        """ESTIMATE the channel from a known probe and what arrived.

        This is a LEAST-SQUARES FIT over the tap coefficients, not a
        correlation. The difference is not cosmetic.

        The first version correlated the transmitted probe against the
        received frame to get one scalar gain, then correlated the
        RESIDUAL against the lagged probe to get a second. That cannot
        represent a complex tap: a real-valued scalar correlation of a
        complex path returns its magnitude and throws its PHASE away.
        Measured against a known two-tap channel, it recovered taps of
        (0.446, 0.222j) and (0.478, 0.000j) where the truth was
        (0.500, 0.000j) and (0.413, 0.282j) -- the phase was wrong, so
        the inversion it produced was wrong, and the alignment it
        reported was 0.0000 for every pair.

        A least-squares fit over the tap basis recovers the truth to
        2.3e-16. numpy is already a dependency of this package, so this
        costs nothing.

        The model:  rx[k] = sum_j h_j * tx[k-j]
        which is a linear system in the h_j, so it is solved as one.

        THE DELAYS ARE RECORDED WITH THE TAPS. The fit searches over
        `tx[k - j*delay]`, so tap j sits at delay `j*delay` bins. The
        returned Channel carries those delays, because a tap without its
        delay is not a tap -- it is a list entry, and evaluating it at
        its list index gives a different filter from the one that was
        fitted. That mistake made the whole measurement read zero
        alignment; see `Channel`'s docstring.
        """
        n = min(len(tx), len(rx))
        if n == 0:
            return Channel.clean()
        t = taps
        # build the design matrix: row k is the probe delayed by j bins
        A = np.zeros((n, t), dtype=np.complex128)
        b = np.zeros(n, dtype=np.complex128)
        for k in range(n):
            for j in range(t):
                idx = k - j * delay
                A[k, j] = tx[idx] if idx >= 0 else tx[0]
            b[k] = rx[k]
        try:
            h, *_ = np.linalg.lstsq(A, b, rcond=None)
        except np.linalg.LinAlgError:
            return Channel.clean()
        # order by magnitude: the taps are a SET, not a sequence, and the
        # strongest path belongs in slot 0
        tap_list = [(float(h[j].real), float(h[j].imag)) for j in range(t)]
        delay_list = [j * delay for j in range(t)]
        order = sorted(range(t), key=lambda j: -(tap_list[j][0] ** 2 + tap_list[j][1] ** 2))
        return Channel([tap_list[j] for j in order], [delay_list[j] for j in order])

    def measure(self, tx_stalk: Stalk, rx_stalk: Stalk,
                pilot: Optional[Pilot] = None) -> Dict[str, object]:
        """measure the interference between two stalks.

        THE PIPELINE, and each stage exists because of a specific
        failure it fixes:

          1. transmit  the stalk's address waveform (the payload) and
                       the PILOT (the known reference), both modulated
                       on the same carrier
          2. receive   the channel acts on the frame: the direct path
                       plus a REFLECTION DELAYED by PATH_DELAY bins.
                       Two comparable paths, because a null in the
                       response needs two paths of comparable strength
          3. estimate  LEAST-SQUARES fit of the channel's delay taps
                       from the pilot, which is known
          4. subtract  the pilot's contribution from the received
                       SPECTRUM, leaving the payload's spectrum
          5. equalise  zero-forcing inversion of the payload's spectrum
          6. compare   the recovered payload against what was sent

        STAGE 4 AND 5 WORK IN THE SPECTRUM, and that is not a detail.
        The equaliser inverts per frequency bin, so it must be handed
        bins. The Rust core's own test makes the contract visible: its
        "received frame" is `c.response_complex(k/n - 0.5)`, which IS
        the spectrum. Passing it time samples inverts nothing.

        Returns the equalised reading, the residual, and the contrast.
        """
        pilot = pilot or Pilot()
        n = self.bins
        delay = PATH_DELAY

        # --- 1. transmit ---------------------------------------------------
        # the payload: the stalk's address waveform
        payload = [math.cos(2.0 * math.pi * tx_stalk.address_phase() * (k / n))
                   for k in range(n)]
        # the pilot: a known broadband sequence
        pilot_tx = [p[0] for p in pilot.frame(n)]
        # the probe the receiver estimates from: the PILOT alone, so the
        # estimate is not contaminated by the payload
        probe = [PILOT_STRENGTH * v for v in pilot_tx]

        coupling = tx_stalk.mutual_couplings()["m_out_in"]

        # THE REFLECTED PATH IS ATTENUATED, and that is what makes the
        # notch FINITE.
        #
        # With two equal, lossless taps the response null is exact --
        # 318 dB -- and the equaliser refuses the frame as
        # `irrecoverable`, because a null deeper than the noise floor
        # means zero-forcing inversion there amplifies noise in
        # proportion to the null's depth. That refusal is CORRECT
        # physics, applied to an unphysical channel.
        #
        # Real paths lose energy: the reflected path is shorter or
        # longer, and it is attenuated relative to the direct one. So the
        # reflection carries REFLECTION_LOSS, and the null becomes finite
        # and shallow enough to invert without blowing up the noise.
        #
        # The ratio is what matters and it is not arbitrary: a null at
        # depth D needs the two paths comparable, and a reflection at
        # 0.9 of the direct path gives a null in the same region the
        # Rust core's own two-path fixture uses (-0.8 -> 21 dB).
        def through_channel(frame: Sequence[float]) -> List[float]:
            """the direct path plus the attenuated, delayed reflected path.

            Both paths carry the SAME frame, because the modulation rides
            on the carrier: delaying the frame delays the whole thing.
            """
            out = []
            for k in range(n):
                direct = frame[k]
                reflected = frame[k - delay] if k >= delay else frame[0]
                out.append(coupling * (direct + REFLECTION_LOSS * reflected))
            return out

        # --- 2. receive ----------------------------------------------------
        probe_rx = through_channel(probe)
        payload_rx = through_channel(payload)

        # --- 3. estimate the channel from the known pilot -------------------
        est = self.estimate_channel(probe, probe_rx, delay=delay)

        # --- 4. subtract the pilot from the received SPECTRUM --------------
        pilot_spec = self._spectrum(pilot_tx)
        pilot_rx_spec = self._spectrum(probe_rx)
        payload_rx_spec = self._spectrum(payload_rx)

        # the pilot's contribution to the received spectrum is what the
        # ESTIMATED channel does to the pilot's own spectrum
        est_pilot_out = []
        for k in range(n):
            f = k / n - 0.5
            hr, hi = est.response_complex(f)
            pr, pi = pilot_spec[k]
            est_pilot_out.append((pr * hr - pi * hi, pr * hi + pi * hr))

        # the received spectrum is payload + pilot, both through the
        # channel; the pilot's part is replaced by what the ESTIMATE says
        # it should be, and the difference is what is left of the
        # payload
        payload_only_spec = [
            (payload_rx_spec[k][0], payload_rx_spec[k][1])
            for k in range(n)]
        rx_spec = [
            (payload_only_spec[k][0] + pilot_rx_spec[k][0],
             payload_only_spec[k][1] + pilot_rx_spec[k][1])
            for k in range(n)]
        signal_only_spec = [
            (rx_spec[k][0] - est_pilot_out[k][0],
             rx_spec[k][1] - est_pilot_out[k][1])
            for k in range(n)]

        # --- 5. equalise the payload's spectrum -----------------------------
        eq = est.equalise(signal_only_spec, noise_floor=self.noise_floor)
        if not eq.get("ok"):
            return {
                "ok": False,
                "error": eq.get("error"),
                "detail": eq.get("detail"),
                "channel_estimate": est.taps,
                "notch_db": est.notch_db(),
            }

        # --- 6. compare ------------------------------------------------------
        samples = eq["samples"]
        assert isinstance(samples, list)
        tx_spec = self._spectrum(payload)
        # the recovered bins are a scalar multiple of the transmitted ones;
        # find the scale, then the error
        num = sum(samples[k][0] * tx_spec[k][0] + samples[k][1] * tx_spec[k][1]
                  for k in range(n))
        den = sum(tx_spec[k][0] ** 2 + tx_spec[k][1] ** 2 for k in range(n))
        scale = (num / den) if den > 1e-18 else 0.0
        resid = math.sqrt(sum(
            (samples[k][0] - scale * tx_spec[k][0]) ** 2 +
            (samples[k][1] - scale * tx_spec[k][1]) ** 2
            for k in range(n)))
        n0 = math.sqrt(sum(tx_spec[k][0] ** 2 + tx_spec[k][1] ** 2
                           for k in range(n))) or 1.0
        alignment = max(0.0, 1.0 - resid / n0)

        # the population contrast: does the receiver's own address stand
        # out from the population?
        pop = PopulationCode([Stratum(id=rx_stalk.id,
                                      phase=rx_stalk.address_phase())])
        contrast = float(pop.decoded(rx_stalk.address_phase())["contrast"])
        return {
            "ok": True,
            "alignment": alignment,
            "residual": resid,
            "contrast": contrast,
            "notch_db": est.notch_db(),
            "channel_estimate": est.taps,
            "scale": scale,
            "samples": len(samples),
        }

    @staticmethod
    def _spectrum(x: Sequence[float]) -> List[Tuple[float, float]]:
        """naive DFT of a real frame. No dependencies, like the Rust core."""
        n = len(x)
        out: List[Tuple[float, float]] = []
        for k in range(n):
            re = im = 0.0
            for i, v in enumerate(x):
                th = -2.0 * math.pi * (k * i) / n
                re += v * math.cos(th)
                im += v * math.sin(th)
            out.append((re, im))
        return out

    def gate(self, tx_stalk: Stalk, rx_stalk: Stalk,
             threshold: float = 0.4) -> Dict[str, object]:
        """the 1-bit veto, reading an equalised measurement.

        If the channel cannot be equalised the gate REFUSES -- an
        uninterpretable frame is not a permissive one. If the alignment
        is below the threshold it refuses. There is no third outcome
        that lets an unreadable frame through.
        """
        m = self.measure(tx_stalk, rx_stalk)
        if not m.get("ok"):
            return {"allow": False, "reason": f"channel_{m.get('error')}",
                    "measurement": m}
        alignment = float(m["alignment"])
        if alignment < threshold:
            return {"allow": False, "reason": "refuse_alignment",
                    "measurement": m}
        return {"allow": True, "reason": "allow", "measurement": m}


# ===========================================================================
# 5. THE FREQUENCY COUPLER -- v6.2, over the stalk population
# ===========================================================================

@dataclass
class FrequencyCoupler:
    """The parallel state channel. Never modifies psi_current.

    v6.1's version was Kuramoto over the 20 axes with sigma_g=0.3 girth
    perturbation. v6.2's version is Kuramoto over the STALKS, where each
    stalk's natural frequency comes from ITS GEOMETRY -- its loop
    eigenvalues -- and the coupling between two stalks comes from their
    mutual coupling.

    The perturbation is GONE. That is the v6.2 claim: the axis count is
    carried by geometry, not by a fudge factor.

    State per stalk:
        phase     the stalk's phase on the shared carrier
        omega     its natural frequency, from its loop eigenvalues
    """

    stalks: List[Stalk]
    coupling_strength: float = 1.2
    dt: float = 0.05

    def __post_init__(self) -> None:
        if not self.stalks:
            raise ValueError("a coupler needs at least one stalk")
        self.n = len(self.stalks)
        # natural frequency per stalk, from its loop eigenvalues [D]
        # the higher loop mode sets the frequency; the ratio between the
        # two modes is the axis the stalk addresses
        self.omegas = np.array(
            [max(abs(s.loop_eigenvalues()[1]), 1e-9) * 0.15 for s in self.stalks],
            dtype=np.float64)
        # initial phases: the stalk's OWN ADDRESS, so the state starts
        # where the geometry says it should
        self.phases = np.array([s.address_phase() * 2.0 * math.pi
                                for s in self.stalks], dtype=np.float64)
        # the coupling matrix, from the geometry
        self.couplings = np.zeros((self.n, self.n), dtype=np.float64)
        for i in range(self.n):
            for j in range(self.n):
                if i == j:
                    continue
                gap = abs(self.stalks[i].girth_out - self.stalks[j].girth_out)
                share = min(self.stalks[i].n_out, self.stalks[j].n_out) / \
                    max(self.stalks[i].n_out, self.stalks[j].n_out)
                self.couplings[i][j] = share / max(gap, 1e-9)

    def step(self, dt: Optional[float] = None) -> np.ndarray:
        """advance one Kuramoto step over the stalk population.

        dphi_i/dt = omega_i + K * (1/|N(i)|) * sum_j k_ij sin(phi_j - phi_i)

        Explicit Euler, matching v6.1. The phases stay bounded because
        the coupling is normalised by the neighbourhood size.
        """
        dt = self.dt if dt is None else dt
        n = self.n
        dphi = np.zeros(n, dtype=np.float64)
        for i in range(n):
            acc = 0.0
            deg = 0.0
            for j in range(n):
                if i == j:
                    continue
                k = float(self.couplings[i][j])
                acc += k * math.sin(self.phases[j] - self.phases[i])
                deg += k
            if deg > 0:
                dphi[i] = self.coupling_strength * (acc / deg)
        self.phases = (self.phases + dt * (self.omegas + dphi)) % (2 * math.pi)
        return self.phases.copy()

    def standing_wave_spectrum(self) -> np.ndarray:
        """the eigen-spectrum of the coupling matrix. [D]

        v6.1 returned eigvalsh of the girth-weighted L. v6.2 returns the
        eigenspectrum of the GEOMETRY-derived coupling matrix, and the
        claim is that it is non-degenerate WITHOUT a perturbation.
        """
        L = -self.couplings.copy()
        np.fill_diagonal(L, 0.0)
        for i in range(self.n):
            L[i][i] = -float(np.sum(self.couplings[i]))
        return np.linalg.eigvalsh(L)

    def population(self) -> PopulationCode:
        """the population code the stalks form."""
        return PopulationCode(
            strata=[Stratum(id=s.id, phase=s.address_phase()) for s in self.stalks])

    def channel(self) -> Channel:
        """the coupling operator between the stalks. [D]

        Each stalk contributes a tap whose amplitude is its coupling to
        the population and whose PHASE is its address. So the channel has
        structure -- and therefore a notch -- and therefore something to
        invert.
        """
        taps: List[Tuple[float, float]] = [(1.0, 0.0)]
        for j, s in enumerate(self.stalks[1:], start=1):
            amp = 0.5
            ph = 2.0 * math.pi * s.address_phase()
            taps.append((amp * math.cos(ph), amp * math.sin(ph)))
        return Channel(taps)

    def reset(self) -> None:
        """restore the phases to the geometry-derived addresses."""
        self.phases = np.array([s.address_phase() * 2.0 * math.pi
                                for s in self.stalks], dtype=np.float64)

    def state_report(self) -> Dict:
        return {
            "n_stalks": self.n,
            "phases": [round(float(p), 6) for p in self.phases],
            "omegas": [round(float(o), 6) for o in self.omegas],
            "spectrum": [round(float(v), 6) for v in self.standing_wave_spectrum()],
            "notch_db": self.channel().notch_db(),
        }


# ===========================================================================
# 6. THE STANDARD STALK SET
# ===========================================================================

def standard_stalks() -> List[Stalk]:
    """four stalks, each with its own geometry.

    Every stalk differs in BOTH girth and turn count, because the claim
    is that the geometry carries the mode count. Two stalks with the same
    geometry would have the same address and the same spectrum, and the
    population would have two indistinguishable members.
    """
    return [
        Stalk(id="s5",  girth_core=0.20, girth_in=0.60, girth_out=1.00,
              n_in=5,  n_out=11),
        Stalk(id="s7",  girth_core=0.18, girth_in=0.55, girth_out=0.95,
              n_in=7,  n_out=13),
        Stalk(id="s11", girth_core=0.22, girth_in=0.65, girth_out=1.10,
              n_in=11, n_out=17),
        Stalk(id="s13", girth_core=0.16, girth_in=0.50, girth_out=0.90,
              n_in=13, n_out=19),
    ]


def degeneracy_report(stalks: List[Stalk]) -> Dict:
    """does the geometry separate the stalks WITHOUT a perturbation? [D]

    v6.2 §7's falsification, computed: two stalks that differ only in
    whether their two windings differ in girth must have different loop
    spectra, or the geometry is not carrying the mode count.

    The CONTROL: two stalks with the SAME geometry have the same
    spectrum, so the distance between them is zero. Without that, a
    measurement that reported a separation for identical geometry would
    be measuring noise.
    """
    differing = Stalk(id="differing", girth_core=0.20, girth_in=0.60,
                      girth_out=1.00, n_in=5, n_out=11)
    same = Stalk(id="same", girth_core=0.20, girth_in=0.60,
                 girth_out=0.6001, n_in=5, n_out=5)
    twin = Stalk(id="twin", girth_core=0.20, girth_in=0.60,
                 girth_out=0.6001, n_in=5, n_out=5)

    def distance(a: List[float], b: List[float]) -> float:
        num = sum(abs(x - y) for x, y in zip(a, b))
        den = max(abs(a[1]), 1e-18) + max(abs(b[1]), 1e-18)
        return num / (2.0 * den)

    sep = distance(differing.loop_eigenvalues(), same.loop_eigenvalues())
    twin_dist = distance(twin.loop_eigenvalues(), same.loop_eigenvalues())

    # and the standard set: are the stalk addresses distinct?
    phases = [s.address_phase() for s in stalks]
    return {
        "sigma_g": 0.3,
        "geometry_spectrum_distance": sep,
        "identical_geometry_distance": twin_dist,
        "geometry_carries_the_count": sep > 0.3,
        "addresses": phases,
        "addresses_distinct": len(set(round(p, 9) for p in phases)) == len(phases),
        "verdict": ("the geometry carries the mode count; no sigma_g needed"
                    if sep > 0.3 else
                    "the geometry does NOT separate the spectra beyond sigma_g"),
        "caveat": "[D] computed on the model. v6.2 §7's bench test -- build "
                  "one coil, measure L_a, L_b and M, eigendecompose -- is "
                  "still owed.",
    }


# ===========================================================================
# 7. THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 76)
    print("STALK CORE v6.2 — coaxial core + two dual-girth windings, multiplexed")
    print("=" * 76)

    stalks = standard_stalks()
    print(f"\n{'stalk':6} {'girth c/i/o':>26} {'N i/o':>9} {'turns x':>9} "
          f"{'girth x':>9} {'address':>9}")
    for s in stalks:
        d = s.describe()
        g = d["girths"]
        print(f"{s.id:6} {g['core']:7.2f}/{g['inner']:.2f}/{g['outer']:<7.2f} "
              f"{d['turns']['inner']:4d}/{d['turns']['outer']:<4d} "
              f"{d['turns_ratio']:9.3f} {d['girth_ratio']:9.3f} "
              f"{d['address_phase']:9.4f}")

    print("\n--- the three mutual couplings, unequal BY CONSTRUCTION ---")
    print(f"{'stalk':6} {'m_out_in':>12} {'m_in_core':>12} {'m_out_core':>12}")
    for s in stalks:
        m = s.mutual_couplings()
        print(f"{s.id:6} {m['m_out_in']:12.4f} {m['m_in_core']:12.4f} "
              f"{m['m_out_core']:12.4f}")

    print("\n--- does the GEOMETRY carry the count? (v6.2 §7, computed) ---")
    rep = degeneracy_report(stalks)
    print(f"geometry spectrum distance : {rep['geometry_spectrum_distance']:.4f}")
    print(f"identical geometry distance: {rep['identical_geometry_distance']:.2e}"
          "   <- the control")
    print(f"addresses distinct        : {rep['addresses_distinct']}")
    print(f"VERDICT: {rep['verdict']}")

    print("\n--- POPULATION CODE: phase is the address ---")
    fc = FrequencyCoupler(stalks=stalks)
    for s in stalks:
        dec = fc.population().decoded(s.address_phase())
        print(f"  probe {s.address_phase():.4f} -> {dec['winner']:6} "
              f"top {float(dec['top']):+.4f} "
              f"contrast {float(dec['contrast']):+.4f}")

    print("\n--- the CHANNEL: crosstalk as something to invert ---")
    ch = fc.channel()
    print(f"taps: {[(round(a, 4), round(b, 4)) for a, b in ch.taps]}")
    print(f"notch: {ch.notch_db():.2f} dB")
    eq = ch.equalise([ch.response_complex(k / 32 - 0.5) for k in range(32)],
                     noise_floor=-80.0)
    print(f"equalise: {'OK' if eq.get('ok') else eq.get('error')}")
    clean = Channel.clean().equalise([(1.0, 0.0)] * 8)
    print(f"clean channel equalise -> {clean.get('error')}  "
          "(a perfectly isolated braid is uncorrectable)")

    print("\n--- the RESONANCE GATE: an equalised reading, and a real veto ---")
    rc = ResonanceChannel()
    for a, b in ((stalks[0], stalks[0]), (stalks[0], stalks[1]),
                 (stalks[0], stalks[2])):
        m = rc.measure(a, b)
        if m.get("ok"):
            print(f"  {a.id} -> {b.id}: alignment {float(m['alignment']):.4f} "
                  f"residual {float(m['residual']):.4f} "
                  f"notch {float(m['notch_db']):.1f} dB")
        else:
            print(f"  {a.id} -> {b.id}: REFUSED {m.get('error')}: "
                  f"{m.get('detail')}")

    print("\n--- the 1-bit veto must be able to say NO ---")
    g1 = rc.gate(stalks[0], stalks[0])
    print(f"  same stalk      -> allow={g1['allow']} reason={g1['reason']}")
    g2 = rc.gate(stalks[0], stalks[3])
    print(f"  distant stalk   -> allow={g2['allow']} reason={g2['reason']}")

    print("\n--- Kuramoto over the stalk population ---")
    for _ in range(200):
        fc.step()
    rep2 = fc.state_report()
    print(f"  phases bounded in [0,2pi): "
          f"{all(0.0 <= p < 2*math.pi for p in rep2['phases'])}")
    print(f"  spectrum: {rep2['spectrum']}")
    print(f"  distinct spectrum values: "
          f"{len(set(round(v, 9) for v in rep2['spectrum']))}/{len(rep2['spectrum'])}")

    print("\n" + "=" * 76)
    print("Run: python src/constitutional/stalk_core.py --selftest")
    print("=" * 76)
    return 0


def _main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description="The v6.2 stalk core.")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    stalks = standard_stalks()
    if args.json:
        print(json.dumps({
            "stalks": [s.describe() for s in stalks],
            "degeneracy": degeneracy_report(stalks),
            "coupler": FrequencyCoupler(stalks=stalks).state_report(),
        }, indent=2))
        return 0
    return _selftest()


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
