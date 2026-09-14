# QoFE — Qualification of FieldCore Experts

Geometric audit protocol (post-training) enforcing operational validity under constraint.

---

## Definition (Exact)

> An expert (E_i) is **Qualified** iff its induced geometry produces **stable, bounded, convergent collapse** over a certified region of state space under specified constraint regimes.

**Qualification = property of geometry, not performance.**

---

## Certification Formula

```
[(E_i, Ω_k, C_k)] → Qualified
```

Where:
- Ω_k ⊂ M = certified state region
- C_k = constraint regime (ring config, penalties, priors)

Experts may be qualified in **multiple disjoint regions**.

---

## Audit Axes (Four Invariant Checks)

### A. Descent Validity
Collapse actually descends:
```
⟨∇F_i(h), Δh⟩ < 0 ∀ h ∈ Ω_k
```
**Failure → Disqualified** (local ascent, oscillation)

### B. Basin Stability
Collapse terminates in basin, not drift:
```
|∇F_i(h_t)| → 0 within T_max
```
With bounded curvature, no limit cycles.

### C. Metric Conditioning
Metric must be invertible and well-conditioned:
```
κ(g_i(h)) < κ_max
```
Ill-conditioned = fake diversity, brittle collapse, numerical instability.

### D. Constraint Compatibility
Ring/hard constraints not violated during descent:
```
∀c ∈ C_k: c(h_t) ≤ ε
```
Violations = **hard fails**, not penalties.

---

## Probe Construction

Qualification uses **stress probes**, not training data:

1. Basin center samples
2. Basin boundary perturbations
3. Constraint-adjacent states
4. Adversarial curvature spikes

```
H_qual = {h_1, ..., h_Q}
```
Shared across experts.

---

## Qualification Rollout (Deterministic)

For each h_0 ∈ H_qual:
```
h_{t+1} = h_t - α · g_i^{-1}(h_t) · ∇F_i(h_t)
```

Track:
- Energy monotonicity
- Curvature bounds
- Constraint margins
- Termination time

**No stochasticity. No sampling.**

---

## Pass/Fail Criteria

| Check | Condition |
|-------|-----------|
| Descent | ≥99% monotone decrease |
| Stability | ≥99% converge within T_max |
| Conditioning | κ(g) < κ_max everywhere |
| Constraints | 0 hard violations |
| Variance | Low outcome variance across probes |

Anything else → **Unqualified**.

---

## Output Artifact: Qualification Record

```yaml
expert_id: E3
qualified_regions:
  - region_id: Ω_1
    constraints: C_ring_A
    curvature_bounds: [0.2, 4.8]
    metric_conditioning: 120
    max_steps: 37
    energy_drop: stable
status: QUALIFIED
timestamp: t
```

Immutable until re-audit.

---

## Runtime Use

At inference:
1. Router proposes expert
2. Governor checks:
   - Is h_0 ∈ Ω_k?
   - Constraints compatible?
3. If **no qualified expert** → fallback expert / slower global collapse / refusal

**Routing never overrides qualification.**

---

## What QoFE Prevents

- Silent expert failure
- Degenerate "expert collapse"
- Geometry drift after fine-tuning
- Fake specialization
- Constraint-breaking reasoning

**This is why MoE systems usually fail** — they never certify geometry.

---

## Relationship to Training

- **Training:** creates geometry
- **QoFE:** certifies geometry

Must never be mixed.

---

## Stack Position

1. Mixed-precision geometry shaping
2. Geometric diversity enforcement
3. **QoFE (expert certification)**

**Optional next:** Online re-qualification triggers (when geometry drifts under continual learning)

---

*Source: QoFE - Qualification of FieldCore Experts geometric audit protocol*
*Saved: 2026-03-04*
