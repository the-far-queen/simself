# QoFE — Qualification of FieldCore Experts

**Source:** `Desktop/SimSelf/docs/qofe_qualification_experts.md` (172 lines, 3.5KB, md5 `94af26aea16778cb8bd0f0335843a4c5`)
**Author:** Bobby (2026-03-04)
**Filed:** 2026-09-13 by Hermes for Bobby
**Status:** **tier 2 engineering extract.** post-training audit protocol. WIP — not serious until arxiv.

---

## ⚠️ WORK IN PROGRESS — NOT SERIOUS UNTIL ARXIV

Tier 2 engineering extract. Per Bobby: "save each raw file going forward i am deleting them."

---

## Definition (exact)

> An expert (E_i) is **Qualified** iff its induced geometry produces **stable, bounded, convergent collapse** over a certified region of state space under specified constraint regimes.

**Qualification = property of geometry, not performance.**

this IS the Bobby point: don't benchmark the LLM (performance = stochastic). benchmark the geometry (qualification = deterministic).

---

## Certification formula

```
[(E_i, Ω_k, C_k)] → Qualified
```

Where:
- Ω_k ⊂ M = certified state region
- C_k = constraint regime (ring config, penalties, priors)

Experts may be qualified in **multiple disjoint regions**.

---

## Audit axes (4 invariant checks)

### A. Descent Validity
collapse actually descends:
```
⟨∇F_i(h), Δh⟩ < 0  ∀ h ∈ Ω_k
```
**Failure → Disqualified** (local ascent, oscillation)

### B. Basin Stability
collapse terminates in basin, not drift:
```
|∇F_i(h_t)| → 0 within T_max
```
with bounded curvature, no limit cycles.

### C. Metric Conditioning
metric must be invertible and well-conditioned:
```
κ(g_i(h)) < κ_max
```
ill-conditioned = fake diversity, brittle collapse, numerical instability.

### D. Constraint Compatibility
ring/hard constraints not violated during descent:
```
∀c ∈ C_k: c(h_t) ≤ ε
```
violations = **hard fails**, not penalties.

---

## Probe construction

qualification uses **stress probes**, not training data:

1. basin center samples
2. basin boundary perturbations
3. constraint-adjacent states
4. adversarial curvature spikes

```
H_qual = {h_1, ..., h_Q}
```

shared across experts.

---

## Qualification rollout (deterministic)

for each h_0 ∈ H_qual:
```
h_{t+1} = h_t - α · g_i^{-1}(h_t) · ∇F_i(h_t)
```

track:
- energy monotonicity
- curvature bounds
- constraint margins
- termination time

**No stochasticity. No sampling.** — this is Bobby's point exactly.

---

## Pass/fail criteria

| check | condition |
|---|---|
| descent | ≥99% monotone decrease |
| stability | ≥99% converge within T_max |
| conditioning | κ(g) < κ_max everywhere |
| constraints | 0 hard violations |
| variance | low outcome variance across probes |

anything else → **Unqualified**.

---

## Output artifact: Qualification record

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

**Immutable until re-audit.**

---

## Runtime use

at inference:
1. router proposes expert
2. governor checks:
   - is h_0 ∈ Ω_k?
   - constraints compatible?
3. if **no qualified expert** → fallback expert / slower global collapse / refusal

**Routing never overrides qualification.**

---

## What QoFE prevents

- silent expert failure
- degenerate "expert collapse"
- geometry drift after fine-tuning
- fake specialization
- constraint-breaking reasoning

**This is why MoE systems usually fail** — they never certify geometry.

---

## Relationship to training

- **Training:** creates geometry
- **QoFE:** certifies geometry

**Must never be mixed.**

---

## Stack position

1. Mixed-precision geometry shaping
2. Geometric diversity enforcement
3. **QoFE (expert certification)**

**Optional next:** Online re-qualification triggers (when geometry drifts under continual learning)

---

## Related (canonical existing docs)

- `simself/docs/atlas-exam-2026-09-13.md` — qualification framework (30 tests, 0/1 scoring)
- `simself/docs/write-rules-conflict-resolution-2026-09-13.md` — write authority + conflict resolution
- `simself/docs/kernel-controller-m0-m1-architecture-2026-09-13.md` — M0/M1 architecture
- `simself/docs/rep-synthesis-2026-09-13.md` — REP 6-stage + B-Matrix state schema
- `fieldcore/src/tiniest-core/tiniest_core.py` — tiniest working kernel
- `fieldcore/docs/research-papers/paper3-atlas-exam.md` — Atlas Exam spec (strongest paper per Bobby)

---

*Filed by Hermes for Bobby, 2026-09-13. Tier 2 engineering extract. Per Bobby: "save each raw file going forward i am deleting them." Vault mirror preserved.*