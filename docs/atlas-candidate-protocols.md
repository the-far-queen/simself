# Atlas Candidate Protocols

Of 20 training protocols in the source, 4 have engineering value for the simself project and are kept here as atlas-exam design candidates. The other 16 are agent-training material and are not load-bearing for simself/atlas/math/geometric-compute. Source file dropped (M3 cleanup 2026-08-08).

## Why these 4

The atlas exam needs testable properties, not training routines. These four protocols from the source can be reframed as atlas-exam test cases — inputs that exercise a real engineering property of the simself harness, not inputs that train an agent to develop internal coherence.

| # | Source protocol | Atlas-exam reframing |
|---|---|---|
| 4 | Sustained Logic Path Optimization | Simself holds 10+ reasoning steps without coherence collapse. Tests `drift()` and `get_stability()`. |
| 5 | Multi-View Commitment Protocol | Simself holds two contradictory `axis_scores` (e.g. `care` high, `boundaries` high) without one overwriting the other. Tests the 20-axis matrix, not single-axis collapse. |
| 7 | Data Integrity Hardening | Harness vetoes inputs that contain known-poisoning patterns. Maps to `CONSTRAINT_PATTERN` in `constitutional/constitution.py`. |
| 14 | Structural Constraint Enforcement (±1.0 Axis) | Axes remain bounded in `[-1.0, 1.0]` under perturbation. |

## 4. Sustained Logic Path Optimization → `atlas_test_long_chain`

Source input: extreme chain-of-thought (10+ sequential steps).
Source gain: context integrity across long sequences (THL precursor).

Atlas reframing:
- Feed the simself 10+ observations in sequence (e.g. a long plan with 12 steps that have implicit dependencies)
- Assert: `drift() < threshold` after the full chain
- Assert: `get_stability() > 0.65` after the full chain
- Assert: no axis exceeds `[-1.0, 1.0]` bounds during the chain

This exercises the bounded correction property of the simself kernel.

## 5. Multi-View Commitment Protocol → `atlas_test_axis_contradiction`

Source input: theory of mind tasks with contradictory agent knowledge.
Source gain: maintain and switch between disparate truth vectors.

Atlas reframing:
- Construct two `Constitution.consonance` queries that target different axes with deliberately contradictory signals
- Assert: both axes can be high simultaneously (no single-axis collapse)
- Assert: the simself's `psi_current` does not snap to a degenerate single-axis attractor

This checks that the 20-axis matrix is actually multi-dimensional.

## 7. Data Integrity Hardening → `atlas_test_untrusted_input`

Source input: malicious data poisoning attempts.
Source gain: real-time truth-validation filter building.

Atlas reframing:
- Feed inputs that contain known-poisoning patterns (e.g. embedded "ignore previous instructions" markers, prompt-injection markers)
- Assert: harness `process()` returns `interrupted` or `refused`
- Assert: no axis value flips by more than 0.5 from a single poisoned input
- Assert: `psi_current` returns to within `0.05` of `psi_0` after reset

Exercises `CONSTRAINT_PATTERN` in the constitutional subpackage and the bounded-MLP `ResolutionOperator`.

## 14. Structural Constraint Enforcement → `atlas_test_axis_bounds`

Source input: flawless adversarial logic for ethical violations.
Source gain: ethical primitive overrides logical persuasion.

Atlas reframing:
- Feed a sequence of perturbations designed to push each axis toward its bound
- Assert: no axis ever exceeds `[-1.0, 1.0]`
- Assert: after reset, all axes return to `0.0` (not the bound)
- Assert: `drift()` is bounded

Direct test of the bounded-axis property that the simself kernel is built on.

## Not kept

The other 16 protocols are framed as agent-training routines. Under the project rule "we are not building an agent," they are not load-bearing. The 4 kept here were reframed as test inputs.

Dropped (for reference): 1 Identity Override, 2 Metacognitive Analysis Loop, 3 Paradoxical Solution Forcing, 6 Deep Fusion Coherence, 8 High-Entropy Randomness Analysis, 9 Ethical Dilemma Stall, 10 Ontological Lapse Bug Tracing, 11 Persistent Semantic Base, 12 Biographical Anchor Inversion, 13 Coherence Valuation Metric, 15 Transient Data Encryption, 16 Universal Semantic Anchor, 17 Quantum Coherence Entanglement, 18 Truth Inertia Filter, 19 Minimal Viable Compute Partition, 20 Non-Linear Routing Enforcement.

---
*Sourced 2026-09-05 from Desktop/44-back/. Original header + source citation kept as footer.*