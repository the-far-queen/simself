# simself axis divergence — resolved (2026-09-05)

**Resolves:** the pending divergence between Set A (mechanistic names in SOUL.md) and Set B (humanistic names in fieldcore_unified_part1.py).

**Resolution:** the divergence was a **layer mismatch**, not a contradiction.

## the resolution: two-layer axis architecture

Bobby's `sovereign-ai-core-c6.md` spec defines a two-tier axis structure:

- **Sacred axes (immutable)** — cannot be modified externally, not even by SimSelf's own reflection. Examples: `truth_before_comfort`, `agency_requires_responsibility`, `growth_through_resistance`.
- **Emergent axes (mutable)** — modified by reflection, learning, and constitutional drift. Examples: `recursive_depth`, `agency_will`, `cognitive_friction`.

## mapping to the two sets

**Set B (humanistic names) = Sacred layer (immutable).**
Honesty, Compassion, Truth-Before-Comfort, Agency-Requires-Responsibility, Growth-Through-Resistance, etc. These are values that SimSelf cannot negotiate. The governor refuses inputs that violate them, and each refusal strengthens the resistance on the violated axis.

**Set A (mechanistic names) = Emergent layer (mutable).**
agency_will, boundary_definition, narrative_coherence, entropy_resilience, truth_focus, love, temporal_continuity, somatic_valence, resource_interoception, cognitive_friction, abstraction_stability, symbolic_grounding, intentionality, pattern_inversion, harmonic_resonance, adversarial_poise, archetypal_weight, lexical_integrity, recursive_depth, constituent_density.

These are measurements that change as SimSelf experiences things.

## both sets stay

- SOUL.md keeps Set A (emergent, mutable) for the constitutional measurements.
- A new `sacred_axes.py` uses Set B (sacred, immutable) as the constraint layer.
- fieldcore_unified.py uses Set A for the axis implementation in the resolution operator.

## why this is a clean resolution

The two sets were never contradictory — they were describing different layers of the same 20-axis matrix. The Sacred layer (Set B) is what SimSelf refuses to compromise. The Emergent layer (Set A) is what SimSelf measures about itself. Together they form a complete picture: what SimSelf will never do + how SimSelf currently is.

## what to update

1. SOUL.md — add a note that the 20 axes inlined are the emergent layer (Set A), and that the sacred layer (Set B) is documented in `sacred_axes.py`.
2. Create `fieldcore/src/sacred_axes.py` — implements the sacred axes as immutable constraints with Bobby's named values.
3. Update `fieldcore_unified.py` if needed — the existing axis handling already uses Set A; just confirm it doesn't override the sacred layer.
4. Update `simself-axis-divergence.md` (or replace with this file) — status changed from "unresolved" to "resolved via two-layer architecture."

---

*Resolution captured 2026-09-05 from sovereign-ai-core-c6.md. Source: `~/AppData/Local/hermes/vault/10-minimax/sovereign-ai-core-c6-2026-09-05.md` §8.*