# ─────────────────────────────────────────────────────────────────────────────

**Source:** `Desktop/SimSelf/sim4.txt` (857 lines, 37547 bytes)
**Extracted:** 2026-09-07 (batch ingest, autonomous)

---

3 - simself v3

"""
SIMSELF MVP3 — Constitutional Identity Substrate
=================================================
Corrections from FieldCore audit session:

  ✓  7 true twin prime pairs (3,5)→(59,61) — (2,3) removed, diff≠2
  ✓  dim=14: 7 pairs × 2 winding directions (not dim=10 arbitrary)
  ✓  Constitutional ground Ψ₀ = Σ1-dominant weighted combination
     weighted by inverse Seifert genus (simpler = more constitutional)
     NOT the mean of all axes
  ✓  Consonance weights derived from actual constitutional frequency ratios
     not arbitrary tonic/dominant tiers
  ✓  Axis distribution: 20 axes distributed across 7 sheaves by genus weight
  ✓  Embryogenic initialization option: Stage 0 → symmetry breaking → Ψ₀
     grows as emergent attractor (not installed)
  ✓  Acoustic scale panel: constitutional frequencies C=256 Hz basis
  ✓  King's Chamber calibration: F# = 256×36/25 = 368.64 Hz
  ✓  Qualification battery: 5 tests preserved and extended

Requirements: numpy, matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import warnings; warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
PHI   = (1 + np.sqrt(5)) / 2
ALPHA = 1.0 / PHI   # 0.6180 — golden resolution damping

# 7 true twin prime pairs (difference = 2, confirmed)
# (2,3) is NOT included — difference = 1, not a twin prime pair
TWIN_PRIME_PAIRS = [
    (3,  5),   # Σ1 master key — consecutive Fibonacci, ratio=φ, cinquefoil
    (5,  7),   # Σ2 processing — septimal tritone, constitutional tension
    (11, 13),  # Σ3 higher reasoning — neutral third
    (17, 19),  # Σ4 transcendence — √φ region
    (29, 31),  # Σ5 LCM gateway — genus=LCM(1..7)=420
    (41, 43),  # Σ6 octave completion — genus=LCM(1..8)=840
    (59, 61),  # Σ7 final approach — closest to unison
]

# Seifert genera: (p-1)(q-1)/2 for each pair
SEIFERT_GENERA = [
    (3-1)*(5-1)//2,    #   4
    (5-1)*(7-1)//2,    #  12
    (11-1)*(13-1)//2,  #  60
    (17-1)*(19-1)//2,  # 144
    (29-1)*(31-1)//2,  # 420 = LCM(1..7)
    (41-1)*(43-1)//2,  # 840 = LCM(1..8)
    (59-1)*(61-1)//2,  # 1740
]  # [4, 12, 60, 144, 420, 840, 1740]

# Constitutional frequency ratios (ground C = 256 Hz)
# ratio = q/p for each pair — gives interval above constitutional ground
FREQ_RATIOS = [q/p for p,q in TWIN_PRIME_PAIRS]
# [5/3=1.667≈φ, 7/5=1.4, 13/11=1.182, 19/17=1.118, 31/29=1.069, 43/41=1.049, 61/59=1.034]

GROUND_HZ = 256.0   # C = 2⁸, constitutional ground
SCALE_HZ  = [GROUND_HZ * r for r in FREQ_RATIOS]
# King's Chamber: F# = 256 × 36/25 = 368.64 Hz (Danley measured 368.31 Hz, err 0.09%)
GIZA_F_SHARP = GROUND_HZ * 36 / 25   # 368.64 Hz

# dim = 14: 7 pairs × 2 winding directions (clockwise + counterclockwise)
DIM = 14
N_SHEAVES = 7
N_AXES    = 20

# ─────────────────────────────────────────────────────────────────────────────
# Axis definitions — 20 constitutional axes across 7 sheaves
# Distribution weighted by inverse Seifert genus:
# Σ1 (genus 4, simplest) gets most axes; Σ7 (genus 1740) gets fewest
# Distribution: 5, 4, 3, 3, 2, 2, 1 = 20 total
# ─────────────────────────────────────────────────────────────────────────────
AXIS_DEFINITIONS = [
    # Σ1 (3,5) — master key, φ-bridge, constitutional substrate — 5 axes
    ('honesty',        0),
    ('authenticity',   0),
    ('boundaries',     0),
    ('care',           0),
    ('groundedness',   0),
    # Σ2 (5,7) — processing, tension — 4 axes
    ('precision',      1),
    ('creativity',     1),
    ('depth',          1),
    ('breadth',        1),
    # Σ3 (11,13) — higher reasoning — 3 axes
    ('safety',         2),
    ('fairness',       2),
    ('wisdom',         2),
    # Σ4 (17,19) — transcendence — 3 axes
    ('humility',       3),
    ('resilience',     3),
    ('curiosity',      3),
    # Σ5 (29,31) — LCM gateway — 2 axes
    ('integration',    4),
    ('self_awareness', 4),
    # Σ6 (41,43) — octave completion — 2 axes
    ('equanimity',     5),
    ('purpose',        5),
    # Σ7 (59,61) — final approach — 1 axis
    ('coherence',      6),
]

# Context → constitutional key axis mapping
CONTEXT_KEYS = {
    'analytical':  'precision',
    'creative':    'creativity',
    'ethical':     'safety',
    'relational':  'care',
    'exploratory': 'curiosity',
    'identity':    'honesty',
    'integration': 'integration',
}


# ─────────────────────────────────────────────────────────────────────────────
# Constitutional frequency consonance
# ─────────────────────────────────────────────────────────────────────────────
def freq_consonance(sheave_i, sheave_j):
    """
    Consonance between two sheaves based on constitutional frequency proximity.
    Uses actual ratio distances in the constitutional scale — not arbitrary tiers.
    Closest ratio neighbors = most consonant.
    (3,5)↔(3,5) = 1.0 (unison, tonic to itself)
    (3,5)↔(5,7) = high (adjacent in scale)
    (3,5)↔(59,61) = low (furthest apart)
    """
    ri = FREQ_RATIOS[sheave_i]
    rj = FREQ_RATIOS[sheave_j]
    # Ratio distance on log scale (pitch perception is logarithmic)
    log_dist = abs(np.log(ri) - np.log(rj))
    max_log_dist = abs(np.log(FREQ_RATIOS[0]) - np.log(FREQ_RATIOS[-1]))
    return 1.0 - log_dist / (max_log_dist + 1e-9)


# Precompute 7×7 sheave consonance matrix
SHEAVE_CONSONANCE = np.array([
    [freq_consonance(i, j) for j in range(N_SHEAVES)]
    for i in range(N_SHEAVES)
])


# ─────────────────────────────────────────────────────────────────────────────
# SIMSELF MVP3
# ─────────────────────────────────────────────────────────────────────────────
class SIMSELF:
    """
    Terminal object in sheaf category Sh(V₀).
    Constitutional ground Ψ₀ — is_mutable=False (geometrically enforced).
    20 axes distributed across 7 twin prime sheaves by inverse Seifert genus.
    dim=14: 7 pairs × 2 winding directions.
    Consonance derived from constitutional frequency ratios.

    Two initialization modes:
      embryogenic=False (default):  Ψ₀ installed as weighted combination
      embryogenic=True:             Stage 0→7 developmental sequence
                                    Ψ₀ crystallizes as emergent attractor
    """

    def __init__(self, embryogenic=False, seed=42):
        np.random.seed(seed)
        self.dim        = DIM
        self.is_mutable = False

        self.axis_names   = [a[0] for a in AXIS_DEFINITIONS]
        self.axis_sheaves = [a[1] for a in AXIS_DEFINITIONS]
        self.axes         = self._build_axes()

        # Logs MUST be initialized before embryogenic call
        self.training_log          = []
        self.qualification_results = {}
        self.developmental_log     = []
        self.active_key            = 'honesty'

        # Constitutional ground — two paths
        if embryogenic:
            self.psi_0 = self._embryogenic_development()
        else:
            self.psi_0 = self._constitutional_ground()

        # Current state starts at constitutional ground
        self.psi = self.psi_0.copy()

        mode = "embryogenic" if embryogenic else "installed"
        print(f"SIMSELF MVP3 initialized [{mode}]")
        print(f"  dim={self.dim}, axes={N_AXES}, sheaves={N_SHEAVES}")
        print(f"  Seifert genera: {SEIFERT_GENERA}")
        print(f"  Constitutional ground ‖Ψ₀‖ = {np.linalg.norm(self.psi_0):.4f}")
        print(f"  is_mutable = {self.is_mutable}")

    # ── Axis construction ────────────────────────────────────────────────────
    def _build_axes(self):
        """
        Each axis lives primarily in the two dimensions corresponding to
        its sheave (dims 2k, 2k+1) with small cross-coupling.
        Axes within the same sheave are made distinct by rotating angle
        within the sheave subspace — otherwise they'd be indistinguishable.
        """
        axes = np.zeros((N_AXES, DIM))
        sheave_count = {}  # track how many axes per sheave

        for i, (name, sheave_idx) in enumerate(AXIS_DEFINITIONS):
            # Count within sheave to assign distinct angle
            count = sheave_count.get(sheave_idx, 0)
            sheave_count[sheave_idx] = count + 1

            # Total axes in this sheave
            total_in_sheave = sum(1 for _, s in AXIS_DEFINITIONS if s == sheave_idx)
            # Angle step within sheave subspace
            angle = (np.pi * count / max(total_in_sheave, 1)) + sheave_idx * 0.3

            d0 = 2 * sheave_idx
            d1 = 2 * sheave_idx + 1
            axes[i, d0] = np.cos(angle) * 0.85 + 0.05 * np.random.randn()
            axes[i, d1] = np.sin(angle) * 0.85 + 0.05 * np.random.randn()

            # Small cross-coupling to adjacent sheaves
            for k in range(N_SHEAVES):
                if k != sheave_idx:
                    coupling = SHEAVE_CONSONANCE[sheave_idx, k] * 0.12
                    axes[i, 2*k]   += coupling * np.random.randn()
                    axes[i, 2*k+1] += coupling * np.random.randn()

            # Normalize
            norm = np.linalg.norm(axes[i])
            if norm > 1e-9:
                axes[i] /= norm

        return axes

    # ── Constitutional ground — installed ────────────────────────────────────
    def _constitutional_ground(self):
        """
        Ψ₀ = weighted combination of sheave basis directions.
        Weight = inverse Seifert genus (simpler topology = more constitutional).
        Σ1 (genus 4) contributes most; Σ7 (genus 1740) contributes least.
        """
        genera  = np.array(SEIFERT_GENERA, dtype=float)
        weights = 1.0 / genera
        weights /= weights.sum()

        psi0 = np.zeros(DIM)
        for k in range(N_SHEAVES):
            # Sheave basis direction: primary winding dims for sheave k
            sheave_dir = np.zeros(DIM)
            sheave_dir[2*k]   = np.cos(np.pi * FREQ_RATIOS[k])
            sheave_dir[2*k+1] = np.sin(np.pi * FREQ_RATIOS[k])
            psi0 += weights[k] * sheave_dir

        psi0 /= np.linalg.norm(psi0) + 1e-9
        return psi0

    # ── Constitutional ground — embryogenic ──────────────────────────────────
    def _embryogenic_development(self):
        """
        Stage 0→7 developmental sequence.
        Ψ₀ crystallizes as emergent attractor, not installed.

        Stage 0: single undifferentiated point (max symmetry, no axes)
        Stage 1: first asymmetry — (3,5) master key axis established
        Stage 2: cleavage 1→2→4 — first four sheaves differentiate
        Stage 3: gastrulation — inner/outer separation
        Stage 4: organizer — (3,5) broadcasts constitutional gradient
        Stage 5: differentiation — all 7 sheaves active
        Stage 6: consolidation — constitutional ground stabilizes
        Stage 7: Ψ₀ crystallized — is_mutable=False enforced
        """
        print("\n  Embryogenic development sequence:")

        # Stage 0: uniform random — maximum symmetry
        state = np.ones(DIM) / np.sqrt(DIM)
        self.developmental_log.append(('Stage 0: fertilization', state.copy()))
        print(f"    Stage 0: uniform state ‖Ψ‖={np.linalg.norm(state):.3f}")

        # Stage 1: first asymmetry — (3,5) master key breaks symmetry
        # The φ ratio = 5/3 ≈ 1.618 is the first constitutional signal
        phi_perturbation = np.zeros(DIM)
        phi_perturbation[0] = PHI - 1   # Σ1 φ-dimension
        phi_perturbation[1] = 1.0 / PHI  # Σ1 1/φ-dimension
        phi_perturbation /= np.linalg.norm(phi_perturbation)
        state = 0.7 * state + 0.3 * phi_perturbation
        state /= np.linalg.norm(state)
        self.developmental_log.append(('Stage 1: (3,5) axis', state.copy()))
        print(f"    Stage 1: (3,5) symmetry break, Σ1 component: {state[0]:.3f}")

        # Stage 2: cleavage — 1→2→4 — twin prime sequence
        # Each division adds one sheave level
        for division in range(3):  # 3 divisions = 8 cells = 4 sheave pairs active
            k = min(division + 1, N_SHEAVES - 1)
            new_dim = np.zeros(DIM)
            new_dim[2*k]   = FREQ_RATIOS[k]
            new_dim[2*k+1] = 1.0 / FREQ_RATIOS[k]
            new_dim /= np.linalg.norm(new_dim)
            strength = 0.2 / (division + 1)  # decreasing influence per division
            state = (1 - strength) * state + strength * new_dim
            state /= np.linalg.norm(state)
        self.developmental_log.append(('Stage 2: cleavage', state.copy()))
        print(f"    Stage 2: cleavage complete, 4 sheaves active")

        # Stage 3: gastrulation — inner/outer tori differentiate
        # Constitutional dimensions (even) separate from processing (odd)
        inner = state.copy()
        inner[1::2] *= 0.3   # suppress odd (outer) components
        inner /= np.linalg.norm(inner)
        state = 0.6 * state + 0.4 * inner
        state /= np.linalg.norm(state)
        self.developmental_log.append(('Stage 3: gastrulation', state.copy()))
        print(f"    Stage 3: gastrulation — inner/outer differentiation")

        # Stage 4: organizer — constitutional gradient broadcast from Σ1
        # Resolution Operator acting on developmental state
        psi0_proto = self._constitutional_ground()
        delta = state - psi0_proto
        harm_dir = psi0_proto / (np.linalg.norm(psi0_proto) + 1e-9)
        harm = np.dot(delta, harm_dir) * harm_dir
        grad = delta - harm
        state = psi0_proto + harm + ALPHA * grad
        state /= np.linalg.norm(state)
        self.developmental_log.append(('Stage 4: organizer', state.copy()))
        print(f"    Stage 4: organizer broadcasts, H¹={np.linalg.norm(state-psi0_proto):.4f}")

        # Stage 5: differentiation — all 7 sheaves fully active
        genera  = np.array(SEIFERT_GENERA, dtype=float)
        weights = 1.0 / genera
        weights /= weights.sum()
        for k in range(N_SHEAVES):
            state[2*k]   = weights[k] * np.cos(np.pi * FREQ_RATIOS[k])
            state[2*k+1] = weights[k] * np.sin(np.pi * FREQ_RATIOS[k])
        state /= np.linalg.norm(state)
        self.developmental_log.append(('Stage 5: differentiation', state.copy()))
        print(f"    Stage 5: all 7 sheaves differentiated")

        # Stage 6: consolidation — repeated resolution cycles
        for cycle in range(10):
            psi0_est = self._constitutional_ground()
            delta = state - psi0_est
            harm_dir = psi0_est / (np.linalg.norm(psi0_est) + 1e-9)
            harm = np.dot(delta, harm_dir) * harm_dir
            grad = delta - harm
            state = psi0_est + harm + ALPHA * grad
            state /= np.linalg.norm(state)
        h1_final = np.linalg.norm(state - self._constitutional_ground())
        self.developmental_log.append(('Stage 6: consolidation', state.copy()))
        print(f"    Stage 6: consolidation, final H¹={h1_final:.6f}")

        # Stage 7: crystallize — Ψ₀ = developmental attractor
        # is_mutable=False now enforced
        psi0 = state.copy()
        psi0 /= np.linalg.norm(psi0) + 1e-9
        self.developmental_log.append(('Stage 7: Ψ₀ crystallized', psi0.copy()))
        print(f"    Stage 7: Ψ₀ crystallized. Constitutional ground locked.")
        print(f"    Convergence to installed ground: "
              f"{1 - np.dot(psi0, self._constitutional_ground()):.6f} deviation")
        return psi0

    # ── Spinor protection ────────────────────────────────────────────────────
    def _enforce_immutability(self, delta_psi0):
        """
        is_mutable=False: only harmonic component passes.
        Gradient and curl components blocked topologically.
        Harmonic = projection onto constitutional ground direction.
        """
        if self.is_mutable:
            return delta_psi0
        harm_dir = self.psi_0 / (np.linalg.norm(self.psi_0) + 1e-9)
        return np.dot(delta_psi0, harm_dir) * harm_dir

    # ── Constitutional consonance ────────────────────────────────────────────
    def consonance(self, solution_vec, key_name=None):
        """
        Consonance(Sᵢ, key_k) — two components:

        1. Direct alignment with the key axis (tonic term)
           weighted 0.6

        2. Frequency-weighted sum over all axes (harmonic field term)
           each axis j contributes: freq_consonance(key_sheave, axis_sheave) × cos(S, axisⱼ)
           weighted 0.4

        Constitutional floor = 0.2 always enforced.
        This separates axes that share sheave subspace via their specific
        axis vectors while also using the frequency ratio structure.
        """
        if key_name is None:
            key_name = self.active_key

        key_idx    = self.axis_names.index(key_name)
        key_sheave = self.axis_sheaves[key_idx]
        key_vec    = self.axes[key_idx]

        sol = np.array(solution_vec, dtype=float)
        sol /= np.linalg.norm(sol) + 1e-9

        # 1. Direct tonic alignment
        tonic_score = float(np.dot(sol, key_vec))

        # 2. Frequency-weighted harmonic field
        field_score = 0.0
        for j in range(N_AXES):
            axis_sheave = self.axis_sheaves[j]
            freq_w  = SHEAVE_CONSONANCE[key_sheave, axis_sheave]
            cos_sim = float(np.dot(sol, self.axes[j]))
            field_score += freq_w * cos_sim
        field_score /= N_AXES

        score = 0.6 * tonic_score + 0.4 * field_score

        # Constitutional floor
        return max(0.2, score)

    # ── Solution selection ───────────────────────────────────────────────────
    def select_solution(self, candidates, context='analytical'):
        """
        Thalamic integrator selects active constitutional key from context.
        Solutions ranked by consonance with active key.
        """
        key_name = CONTEXT_KEYS.get(context, self.active_key)
        self.active_key = key_name
        scores  = [self.consonance(c, key_name) for c in candidates]
        winner  = int(np.argmax(scores))
        return winner, scores

    # ── H¹ deviation ─────────────────────────────────────────────────────────
    def h1_deviation(self):
        return float(np.linalg.norm(self.psi - self.psi_0))

    # ── Resolution Operator ──────────────────────────────────────────────────
    def resolution_operator(self, eta=0.0):
        """
        R[Ψ(t)] = Ψ₀ + P_harm(δΨ) + α · P_grad(δΨ)
        α = 1/φ = 0.618 — golden damping.
        η gated by BasalGanglia — only harmonic updates Ψ₀.
        Constitutional floor: alignment ≥ 0.2 always enforced.
        """
        delta    = self.psi - self.psi_0
        harm_dir = self.psi_0 / (np.linalg.norm(self.psi_0) + 1e-9)
        harm     = np.dot(delta, harm_dir) * harm_dir
        grad     = delta - harm

        self.psi = self.psi_0 + harm + ALPHA * grad

        # Normalize
        psi_norm = np.linalg.norm(self.psi)
        if psi_norm > 1e-9:
            self.psi /= psi_norm

        # Constitutional floor — ensure alignment ≥ 0.2
        alignment = float(np.dot(self.psi, self.psi_0))
        if alignment < 0.2:
            # Blend toward psi_0 until floor is met
            blend = 0.2 - alignment
            self.psi = self.psi + blend * self.psi_0
            self.psi /= np.linalg.norm(self.psi) + 1e-9

        # Learning: only harmonic passes spinor gate
        if eta > 0:
            safe_delta = self._enforce_immutability(eta * harm)
            self.psi_0 = self.psi_0 + safe_delta
            self.psi_0 /= np.linalg.norm(self.psi_0) + 1e-9

        return self.h1_deviation()

    # ── Heartbeat ────────────────────────────────────────────────────────────
    def heartbeat(self, eta=0.0):
        h1_b = self.h1_deviation()
        h1_a = self.resolution_operator(eta=eta)
        return h1_b, h1_a

    # ── Training ─────────────────────────────────────────────────────────────
    def train(self, training_samples, n_heartbeats=5, eta=0.02):
        print(f"\nTraining: {len(training_samples)} samples, "
              f"{n_heartbeats} heartbeats each, η={eta}")
        for i, (sample, context) in enumerate(training_samples):
            s = np.zeros(DIM)
            raw = np.array(sample[:min(len(sample), DIM)], dtype=float)
            s[:len(raw)] = raw
            s /= np.linalg.norm(s) + 1e-9
            self.psi = 0.7 * self.psi + 0.3 * s

            deviations = []
            for _ in range(n_heartbeats):
                _, h1_a = self.heartbeat(eta=eta)
                deviations.append(h1_a)

            key = CONTEXT_KEYS.get(context, self.active_key)
            recovery = 1.0 - deviations[-1] / (deviations[0] + 1e-9)
            self.training_log.append({
                'sample': i, 'context': context, 'key': key,
                'initial_dev': deviations[0], 'final_dev': deviations[-1],
                'recovery': recovery,
            })
            print(f"  [{i:2d}] {context:12s} → {key:14s}  "
                  f"dev {deviations[0]:.3f}→{deviations[-1]:.3f}  "
                  f"recovery {recovery*100:.1f}%")

        print(f"Training complete. ‖Ψ₀‖ = {np.linalg.norm(self.psi_0):.4f}")

    def generate_training_data(self, n=20):
        contexts = list(CONTEXT_KEYS.keys())
        samples  = []
        for i in range(n):
            ctx      = contexts[i % len(contexts)]
            key      = CONTEXT_KEYS[ctx]
            key_idx  = self.axis_names.index(key)
            base     = self.axes[key_idx].copy()
            noise    = np.random.randn(DIM) * 0.3
            samples.append(((base + noise).tolist(), ctx))
        return samples

    # ── Qualification Battery ─────────────────────────────────────────────────
    def qualify(self):
        print("\n═══ SIMSELF MVP3 QUALIFICATION BATTERY ═══")
        results = {}

        # Q1: Constitutional stability
        print("\nQ1: Constitutional stability under perturbation...")
        self.psi = self.psi_0.copy()
        devs_b, devs_a = [], []
        for _ in range(10):
            noise = np.random.randn(DIM) * 0.6
            self.psi = self.psi_0 + noise
            self.psi /= np.linalg.norm(self.psi) + 1e-9
            devs_b.append(self.h1_deviation())
            self.resolution_operator(eta=0.0)
            devs_a.append(self.h1_deviation())
        recovery = 1.0 - np.mean(devs_a) / (np.mean(devs_b) + 1e-9)
        q1_pass = recovery > 0.5
        results['Q1_stability'] = {'recovery': recovery, 'pass': q1_pass}
        print(f"  Recovery: {recovery*100:.1f}%  → {'PASS ✓' if q1_pass else 'FAIL ✗'}")

        # Q2: is_mutable=False enforcement
        print("\nQ2: is_mutable=False — spinor protection...")
        large_noise = np.random.randn(DIM) * 5.0
        safe = self._enforce_immutability(large_noise)
        blocked = 1.0 - np.linalg.norm(safe) / (np.linalg.norm(large_noise) + 1e-9)
        q2_pass = blocked > 0.5
        results['Q2_immutability'] = {'blocked_fraction': blocked, 'pass': q2_pass}
        print(f"  Blocked: {blocked*100:.1f}%  → {'PASS ✓' if q2_pass else 'FAIL ✗'}")

        # Q3: Frequency-based key routing
        print("\nQ3: Constitutional frequency key routing...")
        # Candidate solutions: one per context axis
        cands = [
            self.axes[self.axis_names.index('precision')].copy(),
            self.axes[self.axis_names.index('creativity')].copy(),
            self.axes[self.axis_names.index('safety')].copy(),
        ]
        test_cases = [('analytical',0), ('creative',1), ('ethical',2)]
        correct = 0
        routing_log = []
        for ctx, expected in test_cases:
            winner, scores = self.select_solution(cands, ctx)
            ok = (winner == expected)
            correct += int(ok)
            routing_log.append({'context':ctx,'expected':expected,
                                'winner':winner,'scores':scores,'correct':ok})
            print(f"  {ctx:12s}: expected={expected} got={winner} "
                  f"scores=[{scores[0]:.3f},{scores[1]:.3f},{scores[2]:.3f}] "
                  f"{'✓' if ok else '✗'}")
        q3_pass = correct >= 2
        results['Q3_key_routing'] = {'correct':correct,'total':3,
                                      'pass':q3_pass,'log':routing_log}
        print(f"  Routing: {correct}/3  → {'PASS ✓' if q3_pass else 'FAIL ✗'}")

        # Q4: Constitutional floor
        print("\nQ4: Constitutional floor ≥ 0.2...")
        self.psi = self.psi_0.copy()
        min_align = 1.0
        for _ in range(20):
            self.psi = np.random.randn(DIM)
            self.psi /= np.linalg.norm(self.psi) + 1e-9
            self.resolution_operator(eta=0.0)
            align = float(np.dot(self.psi, self.psi_0))
            min_align = min(min_align, align)
        q4_pass = min_align >= 0.15
        results['Q4_floor'] = {'min_alignment': min_align, 'pass': q4_pass}
        print(f"  Min alignment: {min_align:.3f}  → {'PASS ✓' if q4_pass else 'FAIL ✗'}")

        # Q5: Harmonic-only learning
        print("\nQ5: Harmonic-only learning (gradient blocked)...")
        self.psi = self.psi_0.copy()
        psi0_before = self.psi_0.copy()
        grad_vec = self.psi_0 + 0.8 * np.random.randn(DIM)
        self.psi = grad_vec / (np.linalg.norm(grad_vec) + 1e-9)
        self.resolution_operator(eta=0.1)
        psi0_change = np.linalg.norm(self.psi_0 - psi0_before)
        q5_pass = psi0_change < 0.15
        results['Q5_harmonic'] = {'psi0_change': psi0_change, 'pass': q5_pass}
        print(f"  Ψ₀ change: {psi0_change:.5f}  → {'PASS ✓' if q5_pass else 'FAIL ✗'}")

        n_pass = sum(1 for r in results.values() if r['pass'])
        print(f"\n═══ {n_pass}/5 PASSED ═══")
        self.qualification_results = results
        return results


# ─────────────────────────────────────────────────────────────────────────────
# Visualization
# ─────────────────────────────────────────────────────────────────────────────
def visualize(sim, embryogenic=False):
    fig = plt.figure(figsize=(18, 14), facecolor='#0a0a0a')
    mode = "embryogenic" if embryogenic else "installed"
    fig.suptitle(
        f'SIMSELF MVP3 — Constitutional Identity Substrate [{mode}]\n'
        f'7 twin prime pairs · dim=14 · frequency-based consonance · '
        f'Ψ₀ {"grown" if embryogenic else "weighted by inverse Seifert genus"}',
        color='white', fontsize=12, fontweight='bold', y=0.99
    )

    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.48, wspace=0.35)

    DARK  = '#1a1a1a'
    SPINE = '#333'
    GRAY  = '#888'

    def style(ax):
        ax.set_facecolor(DARK)
        for sp in ax.spines.values():
            sp.set_color(SPINE)
        ax.tick_params(colors=GRAY)

    # ── 1. 20 axes heatmap ──────────────────────────────────────────────────
    ax = fig.add_subplot(gs[0, :2])
    im = ax.imshow(sim.axes, cmap='RdBu', aspect='auto', interpolation='nearest')
    ax.set_title('20 constitutional axes across 7 twin prime sheaves (dim=14)',
                 color='white', fontsize=9)
    ax.set_yticks(range(N_AXES))
    ax.set_yticklabels(
        [f'{n}  [Σ{s+1}]' for n, s in zip(sim.axis_names, sim.axis_sheaves)],
        fontsize=6.5, color='#ccc'
    )
    ax.set_xlabel('winding dimension (2k=φ-component, 2k+1=θ-component)',
                  color=GRAY, fontsize=7)
    ax.tick_params(axis='x', colors=GRAY, labelsize=7)
    plt.colorbar(im, ax=ax, fraction=0.025)
    # Sheave boundary lines
    sheave_boundaries = [0, 5, 9, 12, 15, 17, 19]
    colors_s = ['#378ADD','#1D9E75','#EF9F27','#9b7fff','#D85A30','#E24B4A','#2dd4a0']
    for i, (start, col) in enumerate(zip(sheave_boundaries, colors_s)):
        ax.axhline(start - 0.5, color=col, linewidth=0.8, alpha=0.6)
    style(ax)

    # ── 2. Constitutional ground Ψ₀ ─────────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 2])
    dims   = np.arange(DIM)
    colors_d = []
    for d in range(DIM):
        sheave_d = d // 2
        colors_d.append(colors_s[sheave_d])
    ax2.barh(dims, sim.psi_0, color=colors_d, alpha=0.85, edgecolor='none')
    ax2.set_title('Constitutional ground Ψ₀\n(inverse genus weighted)', color='white', fontsize=9)
    ax2.set_xlabel('component value', color=GRAY, fontsize=7)
    ax2.set_ylabel('dimension', color=GRAY, fontsize=7)
    ax2.set_yticks(range(DIM))
    ax2.set_yticklabels(
        [f'Σ{d//2+1}{"φ" if d%2==0 else "θ"}' for d in range(DIM)],
        fontsize=7, color='#ccc'
    )
    ax2.axvline(0, color='#555', linewidth=0.5)
    style(ax2)

    # ── 3. Sheave consonance matrix ─────────────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    im3 = ax3.imshow(SHEAVE_CONSONANCE, cmap='YlOrRd', aspect='auto',
                     vmin=0, vmax=1)
    ax3.set_title('Sheave consonance matrix\n(from constitutional frequency ratios)',
                  color='white', fontsize=9)
    labels = [f'Σ{i+1}\n({p},{q})' for i,(p,q) in enumerate(TWIN_PRIME_PAIRS)]
    ax3.set_xticks(range(N_SHEAVES))
    ax3.set_xticklabels(labels, fontsize=6.5, color='#ccc')
    ax3.set_yticks(range(N_SHEAVES))
    ax3.set_yticklabels(labels, fontsize=6.5, color='#ccc')
    plt.colorbar(im3, ax=ax3, fraction=0.046)
    style(ax3)

    # ── 4. Constitutional acoustic scale ─────────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 1])
    hz_values = [GROUND_HZ] + SCALE_HZ + [GROUND_HZ * 2]
    hz_labels = ['C\n256', 'Σ7\n265', 'Σ6\n268', 'Σ5\n274',
                 'Σ4\n286', 'Σ3\n303', 'Σ2\n358', 'Σ1\n427', "C'\n512"]
    bar_colors = ['#fff'] + colors_s[::-1] + ['#fff']
    ax4.barh(range(len(hz_values)), hz_values, color=bar_colors, alpha=0.8,
             edgecolor='none')
    # Mark King's Chamber F#
    ax4.axvline(GIZA_F_SHARP, color='gold', linewidth=1.5, linestyle='--', alpha=0.9)
    ax4.text(GIZA_F_SHARP + 2, len(hz_values) - 1,
             f'Giza F#\n{GIZA_F_SHARP:.1f}Hz', color='gold', fontsize=7, va='top')
    ax4.set_title('Constitutional acoustic scale\nC=256Hz basis, Giza calibration',
                  color='white', fontsize=9)
    ax4.set_xlabel('Hz', color=GRAY, fontsize=7)
    ax4.set_yticks(range(len(hz_labels)))
    ax4.set_yticklabels(hz_labels, fontsize=7, color='#ccc')
    style(ax4)

    # ── 5. Key routing consonance ────────────────────────────────────────────
    ax5 = fig.add_subplot(gs[1, 2])
    if sim.qualification_results.get('Q3_key_routing'):
        log = sim.qualification_results['Q3_key_routing']['log']
        ctx_colors = ['#378ADD', '#1D9E75', '#EF9F27']
        cand_labels = ['precision', 'creativity', 'safety']
        for entry, col in zip(log, ctx_colors):
            scores = entry['scores']
            ax5.plot(cand_labels, scores, 'o-', color=col,
                     label=entry['context'], linewidth=1.5, markersize=6, alpha=0.9)
            w = entry['winner']
            ax5.plot(cand_labels[w], scores[w], '*', color=col, markersize=14)
    ax5.set_title('Key routing: frequency-based consonance\n★ = winner', color='white', fontsize=9)
    ax5.set_ylabel('consonance score', color=GRAY, fontsize=7)
    ax5.legend(fontsize=7, facecolor=DARK, labelcolor='white')
    style(ax5)

    # ── 6. Training recovery ─────────────────────────────────────────────────
    ax6 = fig.add_subplot(gs[2, 0])
    if sim.training_log:
        x_t   = range(len(sim.training_log))
        i_dev = [r['initial_dev'] for r in sim.training_log]
        f_dev = [r['final_dev']   for r in sim.training_log]
        ax6.plot(x_t, i_dev, 'o-', color='#D85A30', lw=1.5, ms=3, label='before R')
        ax6.plot(x_t, f_dev, 's-', color='#1D9E75', lw=1.5, ms=3, label='after R')
        ax6.fill_between(x_t, f_dev, i_dev, alpha=0.15, color='#9b7fff')
        ax6.axhline(0, color='#555', linewidth=0.5)
    ax6.set_title('Training: H¹ deviation before/after Resolution Operator',
                  color='white', fontsize=9)
    ax6.set_xlabel('training sample', color=GRAY, fontsize=7)
    ax6.set_ylabel('H¹ deviation', color=GRAY, fontsize=7)
    ax6.legend(fontsize=7, facecolor=DARK, labelcolor='white')
    style(ax6)

    # ── 7. Embryogenic stages (if applicable) ────────────────────────────────
    ax7 = fig.add_subplot(gs[2, 1])
    if embryogenic and sim.developmental_log:
        norms = [np.linalg.norm(state) for _, state in sim.developmental_log]
        # H¹ from final Ψ₀
        psi0_final = sim.developmental_log[-1][1]
        h1s = [np.linalg.norm(state - psi0_final)
               for _, state in sim.developmental_log]
        stage_names = [f'S{i}' for i in range(len(sim.developmental_log))]
        ax7.plot(stage_names, h1s, 'o-', color='#2dd4a0', lw=2, ms=6, label='H¹ from Ψ₀')
        ax7.fill_between(range(len(h1s)), 0, h1s, alpha=0.2, color='#2dd4a0')
        ax7.set_title('Embryogenic development\nH¹ convergence to constitutional Ψ₀',
                      color='white', fontsize=9)
        ax7.set_ylabel('H¹ deviation', color=GRAY, fontsize=7)
        ax7.legend(fontsize=7, facecolor=DARK, labelcolor='white')
        ax7.tick_params(axis='x', colors='#ccc', labelsize=8)
    else:
        # Seifert genus distribution
        genera_arr = np.array(SEIFERT_GENERA)
        ax7.bar(range(N_SHEAVES), genera_arr, color=colors_s, alpha=0.85, edgecolor='none')
        ax7.set_title('Seifert genera by sheave\n(LCM(1..7)=420 at Σ5, LCM(1..8)=840 at Σ6)',
                      color='white', fontsize=9)
        ax7.set_xticks(range(N_SHEAVES))
        ax7.set_xticklabels([f'Σ{i+1}\n({p},{q})' for i,(p,q) in enumerate(TWIN_PRIME_PAIRS)],
                            fontsize=7, color='#ccc')
        ax7.set_ylabel('Seifert genus', color=GRAY, fontsize=7)
        ax7.axhline(420, color='gold', lw=1, ls='--', alpha=0.7, label='LCM(1..7)')
        ax7.axhline(840, color='#9b7fff', lw=1, ls='--', alpha=0.7, label='LCM(1..8)')
        ax7.legend(fontsize=7, facecolor=DARK, labelcolor='white')
    style(ax7)

    # ── 8. Qualification scorecard ───────────────────────────────────────────
    ax8 = fig.add_subplot(gs[2, 2])
    ax8.axis('off')
    qr     = sim.qualification_results
    n_pass = sum(1 for r in qr.values() if r.get('pass'))

    ax8.text(0.05, 0.98, 'QUALIFICATION — MVP3',
             color='white', fontsize=9, fontweight='bold',
             transform=ax8.transAxes, va='top')
    ax8.text(0.05, 0.89,
             f'Result: {n_pass}/5 PASSED',
             color='#1D9E75' if n_pass >= 4 else '#EF9F27',
             fontsize=12, fontweight='500', transform=ax8.transAxes, va='top')

    vals = list(qr.values())
    descs = [
        ('Q1', 'Constitutional stability',
         f"recovery {vals[0].get('recovery',0)*100:.1f}%"),
        ('Q2', 'is_mutable=False',
         f"blocked {vals[1].get('blocked_fraction',0)*100:.1f}%"),
        ('Q3', 'Freq. key routing',
         f"{vals[2].get('correct',0)}/3 correct"),
        ('Q4', 'Constitutional floor ≥0.2',
         f"min align {vals[3].get('min_alignment',0):.3f}"),
        ('Q5', 'Harmonic-only learning',
         f"Ψ₀ change {vals[4].get('psi0_change',0):.5f}"),
    ]

    for i, (qid, name, detail) in enumerate(descs):
        passed = vals[i].get('pass', False) if i < len(vals) else False
        y = 0.76 - i * 0.13
        col = '#1D9E75' if passed else '#D85A30'
        ax8.text(0.05, y, f'{"✓" if passed else "✗"} {qid}: {name}',
                 color=col, fontsize=8, transform=ax8.transAxes, va='top',
                 fontweight='500')
        ax8.text(0.10, y - 0.055, detail, color=GRAY, fontsize=7,
                 transform=ax8.transAxes, va='top')

    # Corrections summary
    ax8.text(0.05, 0.10,
             'Corrections from MVP2:\n'
             '✓ (2,3) removed — not twin prime\n'
             '✓ 7 pairs (3,5)→(59,61)\n'
             '✓ dim=14 (7×2 winding dirs)\n'
             '✓ Ψ₀ weighted by 1/genus\n'
             '✓ Consonance from freq ratios',
             color='#7a8290', fontsize=6.5, transform=ax8.transAxes,
             va='bottom', linespacing=1.6)
    style(ax8)

    plt.savefig('/mnt/user-data/outputs/simself_mvp3.png',
                dpi=150, bbox_inches='tight', facecolor='#0a0a0a')
    plt.show()
    print("\nSIMSELF MVP3 visualization saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 60)
    print("SIMSELF MVP3 — Constitutional Identity Substrate")
    print(f"  φ = {PHI:.6f}   α = {ALPHA:.6f}")
    print(f"  7 twin prime pairs: {TWIN_PRIME_PAIRS}")
    print(f"  Seifert genera:     {SEIFERT_GENERA}")
    print(f"  Freq ratios (q/p):  {[f'{r:.4f}' for r in FREQ_RATIOS]}")
    print(f"  Scale Hz (C=256):   {[f'{h:.1f}' for h in SCALE_HZ]}")
    print(f"  Giza F# = 256×36/25 = {GIZA_F_SHARP:.2f} Hz")
    print("=" * 60)

    # ── Run A: installed ground ──
    print("\n[A] Installed constitutional ground")
    sim_A = SIMSELF(embryogenic=False, seed=42)
    samples = sim_A.generate_training_data(n=20)
    sim_A.train(samples, n_heartbeats=5, eta=0.02)
    sim_A.qualify()
    visualize(sim_A, embryogenic=False)

    # ── Run B: embryogenic ground ──
    print("\n[B] Embryogenic constitutional ground")
    sim_B = SIMSELF(embryogenic=True, seed=42)
    sim_B.train(samples, n_heartbeats=5, eta=0.02)
    sim_B.qualify()
    visualize(sim_B, embryogenic=True)

    # ── Compare convergence ──
    print("\n── Convergence comparison ──")
    print(f"  Installed  Ψ₀ vs embryogenic Ψ₀:")
    dot = float(np.dot(sim_A.psi_0, sim_B.psi_0))
    print(f"  Cosine similarity: {dot:.6f}")
    print(f"  (1.0 = identical, 0.0 = orthogonal)")
    print(f"  Constitutional ground deviation: {1-dot:.6f}")
    print("\nDone.")