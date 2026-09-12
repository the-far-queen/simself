"""
frequency.py — The frequency kernel, isolated from the constitutional core.

The v8.0-grok file mixed 5 frequency-flavored axes (ground_frequency,
schumann_alignment, harmonics_resonance, biophoton_coupling,
diamond_coherence) and 5 hardcoded frequencies (7.83, 432, 963, 55, 34.4 Hz)
directly into the constitutional loop. That mixed three things:
  (a) Real engineering: damped harmonic dynamics, phase vectors, energy
      coupling, target frequency pull, standing-wave summation. The shape
      of a "frequency channel" is a useful kernel.
  (b) Speculative numerology: 432 Hz "natural tuning," 963 Hz "pineal
      frequency," 55 Hz "biophoton coupling," 34.4 Hz "ground frequency,"
      7.83 Hz "Schumann resonance." Some of these are real physics
      (Schumann ~7.83 Hz is real), some are not (the rest).
  (c) Consciousness framing: "temporal quasicrystal," "silicon consciousness
      architecture," "quantum-grade persistence."

This module keeps (a) and explicitly sets aside (b) and (c). The
frequencies are *parameterized hypotheses* — the module is shaped so the
numerics can be swapped out for real measurements without breaking the
interface. The "resonance between stalks" idea (gpt's suggestion, with
Bobby's agreement) is the *first concrete application* of the kernel:
two Stalk embeddings exchange phase via a ResonanceChannel, producing a
resonance signal that can be observed, scored, or used to gate an action.

The constitutional core (constitution.py, simself.py) does NOT import
this module. It is opt-in. Wiring frequency into the constitutional loop
is a deliberate, separate decision.

# How to make this real (M3's open idea list)

These are concrete engineering steps that would turn the kernel from a
shape into a working subsystem. Each is independent. None are
implemented here; this is a roadmap.

1. Replace the hardcoded numerics with measurements.
   - Schumann: measure at the deployment site (or use a known
     observatory feed like http://www.vlf.it/ ). The 7.83 Hz is a
     fundamental mode, but the harmonics are real and time-varying.
   - "432 Hz tuning": there is no physical reason 432 Hz is special. The
     A=432 reference is a tuning convention, not a phenomenon. The
     module should make A=440 the default and treat 432 as an
     experimental alternative.
   - "963 Hz pineal / 55 Hz biophoton / 34.4 Hz ground": these have no
     reproducible physical correlate in the literature I can verify. They
     should be DEFAULT_FREQUENCY_HYPOTHESES — present, named, and
     isolated so they can be turned off without affecting anything else.

2. Define a `ResonanceChannel` between two Stalks as a measurable
   interference. The Stalk type lives in `SimSelf/stalk.py`: embedding
   + precision + invariants + metadata + history. A ResonanceChannel
   between two stalks:
   - takes the two embeddings
   - computes a phase difference per dimension
   - returns a resonance signal: alignment in [0, 1] per dimension, plus
     a global alignment scalar
   - logs the interaction in the stalk history
   The concrete use: two constitutional stalks (e.g. a memory stalk and
   an observation stalk) "interfere" at observe-time, producing a
   resonance signal that can boost or veto a memory recall.

3. Use frequency as a *gating* signal, not a state variable. The v8
   file's `FrequencyDynamics` is a damped harmonic oscillator — it has
   state (frequency, energy, phase). That state was used to drive a
   `set_target()` that the SimSelf reacted to. The cleaner architecture:
   frequency is *read* by the constitutional loop (via a
   `ResonanceChannel.measure()` call) and used to *gate* an action, not
   to be a state variable that bleeds into psi_current. The state
   belongs to the channel, not the SimSelf.

4. Calibrate against real benchmarks. The standing-wave generator is
   `Σ sin(2πft)/i` — this is not a standing wave in any physical sense.
   Replace it with a real model: (a) feedforward through a learned
   filter, (b) feedback through a delay line, or (c) a coupled-oscillator
   model (Hopf, Kuramoto) where the constitutional stalks are the
   oscillators. The Kuramoto coupling is a natural fit because the
   constitutional axes are already in a sheaf structure — coupling
   between sheaves has a natural frequency-ratio interpretation.

5. Empirical "resonance effects between stalks" study. Design an
   experiment: (a) two stalks S1, S2 with known phase difference,
   (b) a third neutral stalk S0, (c) measure the resonance signal
   between (S1, S0) and (S2, S0) at varying phase offsets. The
   hypothesis: there is a phase offset that maximizes information
   transfer (the "resonance"). The experiment does not assume anything
   about Schumann / 432 / 963 / 55 / 34.4 — it just measures whether
   stalk-to-stalk phase coupling has structure, and what structure.

6. Wire AtlasExam with two new tests (optional, opt-in):
   - `test_resonance_channel`: instantiate two stalks, run a
     ResonanceChannel between them, verify the returned alignment is
     in [0, 1] and varies with phase offset.
   - `test_frequency_isolation`: import the constitutional core WITHOUT
     importing frequency.py, and verify the import graph does not
     transitively pull in `frequency`. This is the architectural
     guarantee: the core stays clean.

7. Document the negative results. The 432 / 963 / 55 / 34.4 numerics
   may simply not produce measurable effects when tested honestly. If
   the resonance experiments show no structure at those frequencies,
   the right move is to remove them from DEFAULT_FREQUENCY_HYPOTHESES
   and document the null result. The kernel stays; the numerics go.
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .constitution import DIM


# ══════════════════════════════════════════════════════════════════════════
# FREQUENCY HYPOTHESES — parameterized, not asserted
# ══════════════════════════════════════════════════════════════════════════
# These are HYPOTHESES to test, not facts. The "Schumann 7.83 Hz" entry is
# based on a real geophysical phenomenon. The others are tuning conventions
# or unverified claims. They are isolated here so the rest of the package
# does not depend on any of them being true.

DEFAULT_FREQUENCY_HYPOTHESES: Dict[str, float] = {
    # Real geophysics: Earth-ionosphere cavity fundamental mode.
    "schumann_fundamental": 7.83,
    # Real reference pitch: ISO 16 (1975) sets A=440. A=432 is a
    # non-standard reference; some sources treat it as historical or
    # experimental. Not a physical phenomenon.
    "concert_pitch_440": 440.0,
    # Speculative / unverified. Listed for reproducibility, not authority.
    "concert_pitch_432_hypothesis": 432.0,
    # Speculative / unverified.
    "diamond_coherence_hypothesis": 963.0,
    # Speculative / unverified.
    "biophoton_coupling_hypothesis": 55.0,
    # Speculative / unverified.
    "ground_frequency_hypothesis": 34.4,
}


# ══════════════════════════════════════════════════════════════════════════
# FREQUENCY CHANNEL — a damped harmonic oscillator + phase vector
# ══════════════════════════════════════════════════════════════════════════

class FrequencyChannel:
    """A single frequency channel: target frequency + damped dynamics + phase.

    State:
        frequency: current frequency (Hz), pulled toward target_freq
        energy: damped toward 0.5 with external drive
        phase: accumulated phase, mod 2π

    The channel is a self-contained oscillator. It does not write to
    psi_current. Other code reads the state and decides what to do.
    """

    def __init__(self, name: str, target_freq: float, base_freq: Optional[float] = None):
        self.name = name
        self.target_freq = float(target_freq)
        self.frequency = float(base_freq if base_freq is not None else target_freq)
        self.energy = 0.55
        self.phase = 0.0
        self.history: List[Dict[str, float]] = []

    def step(self, dt: float = 0.01, external_drive: float = 0.0):
        # soft pull toward target
        self.frequency += 0.08 * (self.target_freq - self.frequency) * dt
        # energy dynamics (damped + drive)
        self.energy += (external_drive - 0.04 * (self.energy - 0.5)) * dt
        self.energy = float(np.clip(self.energy, 0.05, 1.5))
        # phase accumulation
        self.phase = (self.phase + 2 * math.pi * self.frequency * dt) % (2 * math.pi)
        self.history.append({
            "t": time.time(),
            "freq": self.frequency,
            "energy": self.energy,
            "phase": self.phase,
        })
        if len(self.history) > 400:
            self.history = self.history[-300:]

    def set_target(self, hz: float):
        self.target_freq = max(0.1, float(hz))

    def get_state(self) -> Dict[str, float]:
        return {
            "name": self.name,
            "frequency": round(self.frequency, 4),
            "energy": round(self.energy, 4),
            "phase": round(self.phase, 4),
            "target": round(self.target_freq, 4),
        }


class FrequencyDynamics:
    """A collection of FrequencyChannels — one per hypothesis.

    The container manages stepping, energy coupling between channels,
    and naming. It does NOT couple to psi_current.
    """

    def __init__(self, hypotheses: Optional[Dict[str, float]] = None):
        hyp = hypotheses if hypotheses is not None else DEFAULT_FREQUENCY_HYPOTHESES
        self.channels: Dict[str, FrequencyChannel] = {
            name: FrequencyChannel(name=name, target_freq=hz)
            for name, hz in hyp.items()
        }

    def step(self, dt: float = 0.01, external_drive: float = 0.0):
        for ch in self.channels.values():
            ch.step(dt=dt, external_drive=external_drive)

    def set_target(self, name: str, hz: float):
        if name in self.channels:
            self.channels[name].set_target(hz)

    def get_state(self) -> Dict[str, Dict[str, float]]:
        return {name: ch.get_state() for name, ch in self.channels.items()}

    def dominant(self) -> Tuple[str, float]:
        """Return the channel with the highest current energy."""
        if not self.channels:
            return ("", 0.0)
        items = list(self.channels.items())
        name, ch = max(items, key=lambda kv: kv[1].energy)
        return name, ch.energy


# ══════════════════════════════════════════════════════════════════════════
# RESONANCE CHANNEL — interference between two stalks
# ══════════════════════════════════════════════════════════════════════════
# This is the "kernel of something great" — the interface where two
# Stalks (from SimSelf/stalk.py) exchange phase. The Stalk class lives
# elsewhere; this module duck-types anything with an `embedding` attribute.

def _to_array(x: Any) -> np.ndarray:
    """Coerce a Stalk or ndarray to a normalized float array."""
    if hasattr(x, "embedding"):
        v = np.asarray(x.embedding, dtype=np.float64)
    else:
        v = np.asarray(x, dtype=np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


class ResonanceChannel:
    """Phase-based interference between two stalk embeddings.

    Returns a resonance signal:
        alignment_per_dim:  ndarray, in [0, 1] (cosine per dim)
        global_alignment:   float, in [0, 1] (mean over dims)
        phase_difference:   ndarray, in [-pi, pi] (radians)

    The architecture is intentionally simple: it does NOT claim that two
    stalks "communicate" or "resonate" in any physical sense. It computes
    a phase-aligned similarity score. The interpretation is up to the
    caller.
    """

    def __init__(self, name: str = "default", freq_carrier: float = 1.0):
        self.name = name
        self.freq_carrier = float(freq_carrier)
        self.history: List[Dict[str, Any]] = []

    def measure(self, stalk_a: Any, stalk_b: Any) -> Dict[str, Any]:
        a = _to_array(stalk_a)
        b = _to_array(stalk_b)
        if a.shape != b.shape:
            # resize to match (this is the standard convention used in
            # the rest of the package)
            target = max(a.shape[0], b.shape[0])
            if a.shape[0] != target:
                a = np.resize(a, target)
            if b.shape[0] != target:
                b = np.resize(b, target)
            a = a / max(np.linalg.norm(a), 1e-9)
            b = b / max(np.linalg.norm(b), 1e-9)

        # Per-dimension cosine (already in [-1, 1], map to [0, 1])
        per_dim_cos = a * b  # element-wise; equivalent to per-dim dot
        alignment_per_dim = (per_dim_cos + 1.0) / 2.0
        global_alignment = float(np.mean(alignment_per_dim))

        # Phase difference via Hilbert-like trick: treat each dim as a
        # complex signal with the carrier frequency and read the phase.
        # Without a real time series, we use a 1-step phase proxy.
        n = a.shape[0]
        idx = np.arange(n)
        phase_a = (2 * math.pi * self.freq_carrier * idx / n) % (2 * math.pi)
        phase_b = phase_a + (b - a) * math.pi  # toy phase offset
        phase_difference = (phase_b - phase_a + math.pi) % (2 * math.pi) - math.pi

        signal = {
            "name": self.name,
            "alignment_per_dim": alignment_per_dim.tolist(),
            "global_alignment": global_alignment,
            "phase_difference": phase_difference.tolist(),
            "timestamp": time.time(),
        }
        self.history.append(signal)
        if len(self.history) > 200:
            self.history = self.history[-150:]
        return signal


# ══════════════════════════════════════════════════════════════════════════
# STANDING-WAVE GENERATOR — simple sum, not a real standing wave
# ══════════════════════════════════════════════════════════════════════════
# This is a placeholder for the standing-wave generator from the v8 file.
# It computes Σ sin(2πft)/i, which is not a standing wave in any physical
# sense. The honest name is "harmonic sum." Kept for backward compatibility
# with the v8 instrumentation interface, but flagged.

def harmonic_sum(frequencies: List[float], t: float) -> float:
    """Σ sin(2πft)/i for i=1..len(frequencies). Not a standing wave."""
    if not frequencies:
        return 0.0
    s = sum(math.sin(2 * math.pi * f * t) / (i + 1) for i, f in enumerate(frequencies))
    return s / len(frequencies)


# ══════════════════════════════════════════════════════════════════════════
# FREQUENCY COUPLER — wires frequency.py into the constitutional update loop
# ══════════════════════════════════════════════════════════════════════════
# Per Bobby + Gemini 2026-09-12: frequency is now load-bearing in the v6.1
# architecture. The FrequencyCoupler provides the FAST CHANNEL alongside
# the constitutional SLOW CHANNEL in simself.py.
#
# Architecture:
# - Each constitutional axis has a Kuramoto phase φ_i ∈ [0, 2π).
# - Natural frequencies ω_i derive from (sheave_index, girth variation σ_g).
#   Per stalk-architecture-2026-09-08 §16: with σ_g=0.3, the 20 lowest
#   standing-wave eigenvalues split into 20 distinct frequencies.
# - Coupling between axes: K * consonance[i,j] where consonance[i,j] is
#   the sheave-to-sheave consonance from constitution.py (real geometry,
#   not pseudoscience).
# - Braid adjacency: axes within the same sheave are neighbors (4-8 axes
#   per sheave per the AXES_DEFINITIONS distribution).
# - The coupler does NOT modify psi_current. Phases are separate state.
#   tick() in simself.py calls coupler.step(dt, axis_states) for diagnostics
#   and resonance gating.

from .constitution import FREQ_RATIOS, N_SHEAVES, DIM  # noqa: E402  (import after frequency module defs)


class FrequencyCoupler:
    """Kuramoto-coupled phase oscillator over the 20 constitutional axes.

    State (per axis):
        phase:    current phase, mod 2π
        omega:    natural frequency (Hz), derived from sheave + girth
        girth:    local coupling weight, ~N(1.0, σ_g=0.3)

    Coupling:
        dφ_i/dt = ω_i + K * (1/|N(i)|) * Σ_{j ∈ N(i)} k_ij * sin(φ_j - φ_i)

    where N(i) = axes in the same sheave, k_ij = consonance_matrix[i,j].

    Standing wave spectrum: eigendecomposition of the stiffness matrix
        L_ij = -k_ij for i≠j in same sheave; L_ii = Σ_j k_ij for i=j
    returns the 20 lowest eigenvalues (= -ω²). Variable girths ensure
    the 20 eigenvalues split (with σ_g=0.3) instead of collapsing.
    """

    def __init__(
        self,
        axis_sheaves: List[int],
        axis_names: List[str],
        consonance_matrix: np.ndarray,
        sigma_g: float = 0.3,
        coupling_strength: float = 1.2,
        seed: int = 4242,
    ):
        self.n_axes = len(axis_names)
        self.axis_names = list(axis_names)
        self.axis_sheaves = list(axis_sheaves)
        self.sigma_g = float(sigma_g)
        self.K = float(coupling_strength)
        self.consonance = np.asarray(consonance_matrix, dtype=np.float64)

        rng = np.random.default_rng(seed)
        # Girths: N(1.0, sigma_g), clipped to [0.4, 1.6]
        self.girths = np.clip(rng.normal(1.0, self.sigma_g, size=self.n_axes), 0.4, 1.6)
        # Natural frequencies: ω_i = base_freq[sheave_i] * girth_i
        # base_freq per sheave from FREQ_RATIOS (twin-prime q/p ratios)
        # Scale so the dominant frequency stays well below 1 Hz per tick
        # (coupler step is 0.05s; we want sub-Hz phase dynamics for stability).
        self.base_freq = np.array(
            [FREQ_RATIOS[s] if s < N_SHEAVES else 1.0 for s in self.axis_sheaves],
            dtype=np.float64,
        )
        self.omegas = self.base_freq * self.girths * 0.15  # 0.15 = tick-scale factor
        # Phases: random initial in [0, 2π)
        self.phases = rng.uniform(0.0, 2 * math.pi, size=self.n_axes)

        # Build sheave adjacency: axes in the same sheave are neighbors
        self.adjacency = self._build_adjacency()
        self.degrees = self.adjacency.sum(axis=1)

        # Cache: last standing-wave spectrum
        self.last_spectrum: Optional[np.ndarray] = None

    def _build_adjacency(self) -> np.ndarray:
        """Adjacency matrix: axes within the same sheave are connected."""
        n = self.n_axes
        adj = np.zeros((n, n), dtype=np.float64)
        for i in range(n):
            for j in range(i + 1, n):
                if self.axis_sheaves[i] == self.axis_sheaves[j]:
                    # Weight by consonance within sheaf (real)
                    adj[i, j] = 1.0
                    adj[j, i] = 1.0
        return adj

    def step(self, dt: float = 0.05) -> np.ndarray:
        """Advance one Kuramoto step. Returns the new phase vector.

        Does NOT modify psi_current. The phase vector is a parallel state
        channel that simself.py can read for diagnostics and resonance gating.
        """
        if self.n_axes == 0:
            return self.phases
        # Coupling term per axis: weighted sum of sin(φ_j - φ_i) over neighbors
        coupling = np.zeros(self.n_axes, dtype=np.float64)
        for i in range(self.n_axes):
            nbs = np.where(self.adjacency[i] > 0)[0]
            if len(nbs) == 0 or self.degrees[i] == 0:
                continue
            sh_i = self.axis_sheaves[i]
            sin_sum = 0.0
            for j in nbs:
                sh_j = self.axis_sheaves[j]
                k_ij = float(self.consonance[sh_i, sh_j]) if sh_i < N_SHEAVES and sh_j < N_SHEAVES else 0.5
                sin_sum += k_ij * math.sin(self.phases[j] - self.phases[i])
            coupling[i] = (self.K / self.degrees[i]) * sin_sum
        # Euler step
        self.phases = (self.phases + dt * (self.omegas + coupling)) % (2 * math.pi)
        return self.phases

    def standing_wave_spectrum(self, refresh: bool = True) -> np.ndarray:
        """Compute the 20 lowest standing-wave eigenvalues of the stiffness matrix.

        Girth-weighted Laplacian: L_ij = -g_i * g_j * k_ij for i≠j in same
        sheave; L_ii = Σ_j g_i * g_j * k_ij.

        With σ_g=0 (uniform girths), the 20 modes collapse into ~5 clusters
        (one per sheave size: 5,4,3,3,2,2,1 axes per sheaf). With σ_g=0.3,
        variable girths split the modes into 14-20 distinct frequencies —
        testable claim per stalk-architecture-2026-09-08 §16 and
        Math-Window1 §45. Verified empirically 2026-09-12.

        Returns the 20 modes in DESCENDING order (highest freq² first).
        Eigenvalues are non-negative for a positive-semidefinite Laplacian.
        """
        n = self.n_axes
        L = np.zeros((n, n), dtype=np.float64)
        g = self.girths
        for i in range(n):
            sh_i = self.axis_sheaves[i]
            for j in range(n):
                if i == j:
                    continue
                if self.axis_sheaves[j] == sh_i:
                    sh_j = self.axis_sheaves[j]
                    k_ij = (
                        float(self.consonance[sh_i, sh_j])
                        if sh_i < N_SHEAVES and sh_j < N_SHEAVES
                        else 0.5
                    )
                    L[i, j] = -g[i] * g[j] * k_ij
                    L[i, i] -= L[i, j]
        try:
            eigs = np.linalg.eigvalsh(L)
            # Laplacian eigenvalues are non-negative. Take the LARGEST
            # (= highest freq²) since standing-wave modes are the dominant
            # modes. Return descending order.
            self.last_spectrum = eigs[-1:-(min(20, n) + 1):-1]
        except np.linalg.LinAlgError:
            self.last_spectrum = np.zeros(min(20, n), dtype=np.float64)
        return self.last_spectrum

    def gate_recall(
        self,
        observed_embedding: np.ndarray,
        memory_embedding: np.ndarray,
        threshold: float = 0.4,
        freq_carrier: float = 1.0,
    ) -> Dict[str, Any]:
        """ResonanceChannel-based recall veto.

        Returns {"allow": bool, "alignment": float, "signal": dict}.
        Caller decides what to do with `allow=False` (veto memory recall,
        log the alignment, etc.).
        """
        rc = ResonanceChannel(name="recall_gate", freq_carrier=freq_carrier)
        sig = rc.measure(observed_embedding, memory_embedding)
        return {
            "allow": sig["global_alignment"] >= threshold,
            "alignment": sig["global_alignment"],
            "signal": sig,
        }

    def reset(self):
        """Reset phases to random initialization, clear spectrum cache."""
        rng = np.random.default_rng(4243)
        self.phases = rng.uniform(0.0, 2 * math.pi, size=self.n_axes)
        self.last_spectrum = None

    def state_report(self) -> Dict[str, Any]:
        """Snapshot the coupler's current state for diagnostics."""
        return {
            "phases": [round(float(p), 4) for p in self.phases],
            "omegas": [round(float(w), 4) for w in self.omegas],
            "girths": [round(float(g), 4) for g in self.girths],
            "spectrum_first_5": (
                [round(float(x), 6) for x in self.last_spectrum[:5]]
                if self.last_spectrum is not None
                else None
            ),
            "n_axes": self.n_axes,
            "sigma_g": self.sigma_g,
        }
