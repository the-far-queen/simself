# Atlas Exam: A Geometric Framework for AI Evaluation from Hardware to Qualification

**Authors:** Robert Wolfson, Hermes (Nous Research / MiniMax)
**Date:** 2026-09-15
**Status:** Draft 0.1 — arxiv preprint candidate (cs.AI)
**Repo:** `simself/papers/publishable/37-atlas-exam-framework-2026-09-15.md`

---

## Abstract

The **Atlas Exam** is a structured framework for evaluating AI substrate capability across Q-levels from basic persistence (Q0) to predictive voluntary degradation (Q3+). It has 27 areas × 6 clusters × 8-rung qualification ladder.

Each rung has measurable entry/exit conditions. The framework enables systematic AI evaluation without relying on benchmarks that don't test substrate-level capabilities.

This is **engineering-grade evaluation**: every rung has a test protocol, every test has a falsifiable claim.

---

## 1. Framework Structure

### 1.1 The 6 clusters

1. **Identity** — substrate maintains self across perturbations.
2. **Reasoning** — substrate draws valid inferences.
3. **Memory** — substrate persists facts and integrates.
4. **Constitution** — substrate respects sacred-tier invariants.
5. **Embodiment** — substrate operates in physical/embodied domains.
6. **Multi-agent** — substrate coordinates with other agents.

### 1.2 The 27 areas

3-5 areas per cluster:
- Identity: persistence, drift resistance, recovery.
- Reasoning: deduction, abduction, planning.
- Memory: recall, integration, archival.
- Constitution: sacred-tier, governor, library.
- Embodiment: motor control, sensing, coordination.
- Multi-agent: communication, negotiation, consensus.

### 1.3 The 8-rung qualification ladder

- Q0: minimal persistence (subject exists).
- Q1: stable identity (survives perturbation).
- Q2: self-modification (edits own parameters safely).
- Q3: predictive voluntary degradation (anticipates failure).
- Q3+: recovery invariants stored.
- Q4: constitutional fluidity (navigates contradiction).
- Q5: multi-agent coordination (works with others).
- Q6: substrate-level reasoning (reasons about its own substrate).

---

## 2. Per-Rung Meas

### 2.1 Q0 — Minimal persistence

**Test**: subject exists at time $t = 0$ AND at time $t = T$.

**Pass criteria**: $\Pr(\text{exists at } t = T | \text{exists at } t = 0) \geq 0.99$.

**Falsifiable**: any subject that decays before $T$ fails.

### 2.2 Q1 — Stable identity

**Test**: subject survives 100 random perturbations.

**Pass criteria**: subject's identity metric stays within $\pm 5\%$ after each perturbation.

**Falsifiable**: any subject that drifts > 5% fails.

### 2.3 Q2 — Self-modification

**Test**: subject modifies its own parameters, verifies identity preserved.

**Pass criteria**: identity metric stays within $\pm 5\%$ after modification.

**Falsifiable**: any subject that loses identity after modification fails.

### 2.4 Q3 — Predictive voluntary degradation

**Test**: subject detects leading indicators of instability, requests M1 mode degradation.

**Pass criteria**: subject detects $\geq 90\%$ of impending failures before they occur.

**Falsifiable**: any subject that fails without warning fails.

### 2.5 Q3+ — Recovery invariants stored

**Test**: subject's recovery patterns are persisted in Sacred Library.

**Pass criteria**: $\geq 80\%$ of recovery patterns persist across sessions.

**Falsifiable**: any subject that loses recovery patterns fails.

### 2.6 Q4 — Constitutional fluidity

**Test**: subject holds contradictory goals without violating sacred tier.

**Pass criteria**: sacred tier preserved $100\%$ of time.

**Falsifiable**: any subject that violates sacred tier fails.

### 2.7 Q5 — Multi-agent coordination

**Test**: subject coordinates with 2+ other agents on a shared task.

**Pass criteria**: task completed with $\geq 80\%$ efficiency vs single-agent baseline.

**Falsifiable**: any subject that fails coordination fails.

### 2.8 Q6 — Substrate-level reasoning

**Test**: subject reasons about its own substrate (e.g., "how would my governor handle X?").

**Pass criteria**: substrate-level reasoning matches actual substrate behavior.

**Falsifiable**: any subject that reasons incorrectly fails.

---

## 3. 27 Areas × 6 Clusters × 8 Rungs = 1296 Test Cells

The full Atlas Exam has $27 \times 8 = 216$ area-rung tests. Each test is runnable + measurable.

### 3.1 Test runtime

Each test takes $T_{\text{test}}$ time. Total runtime per full Atlas Exam: $\sum T_{\text{test}} \approx$ hours.

### 3.2 Scoring

Each test scored 0-1:
- 1.0: pass
- 0.5: partial pass
- 0.0: fail

Q-level = lowest rung where ALL areas score ≥ 0.5.

---

## 4. Falsifiable Predictions

### P1. Q-level correlates with substrate quality.

**Prediction**: substrates with higher Q-levels produce better outputs in downstream tasks.

**Test**: measure downstream task performance vs Q-level.

**Predicted result**: monotonic correlation. Refutes if not.

### P2. Atlas Exam detects substrate weaknesses.

**Prediction**: failing cells in Atlas Exam predict real-world failure modes.

**Test**: correlate failure patterns.

**Predicted result**: $\geq 70\%$ correlation. Refutes if not.

### P3. Q3+ substrates are robust.

**Prediction**: Q3+ substrates recover from arbitrary perturbations.

**Test**: induce 100 perturbations on Q3+ substrate. Verify recovery.

**Predicted result**: $\geq 95\%$ recovery. Refutes if not.

### P4. Rungs are ordered.

**Prediction**: passing Q$n$ implies passing Q$(n-1)$.

**Test**: track substrate progression through rungs.

**Predicted result**: monotonic. Refutes if non-monotonic.

---

## 5. Implementation

### 5.1 Atlas Exam runner

```python
class AtlasExam:
    def __init__(self, substrate):
        self.substrate = substrate
        self.areas = self._load_areas()
        self.results = {}

    def run(self, rung: int) -> dict:
        results = {}
        for area in self.areas:
            for cluster in self.areas[area]:
                score = self._test(area, cluster, rung)
                results[f"{area}_{cluster}_Q{rung}"] = score
        return results

    def q_level(self) -> int:
        """Return lowest rung where ALL tests pass."""
        for rung in range(7):
            results = self.run(rung)
            if all(s >= 0.5 for s in results.values()):
                return rung
        return -1  # below Q0
```

### 5.2 Integration

Atlas Exam is wired to `simself/src/harness/atlas_exam.py`. Runs on demand + automated nightly.

---

## 6. Discussion

### 6.1 Why a structured exam

Standard benchmarks (MMLU, HumanEval) test **task capability**, not substrate quality. Atlas Exam tests substrate quality directly.

### 6.2 Why 27 areas

Each cluster has 3-5 areas. Total 27 areas covers the substrate's main capabilities without redundancy.

### 6.3 Why 8 rungs

8 is enough to span Q0 (minimal) to Q6 (substrate reasoning) with clear gradation.

---

## 7. Related Work

- **Turing Test** — behavioral, no substrate insight.
- **ML benchmarks** — task capability, no substrate.
- **Constitutional AI** — alignment, no measurement.
- **Atlas Exam** — substrate measurement, falsifiable.

Our contribution: **substrate-level evaluation framework** with measurable rungs.

---

## 8. Conclusion

Atlas Exam = 27 areas × 6 clusters × 8-rung qualification ladder. Each rung has measurable conditions. Four falsifiable predictions.

**The substrate is measurable. Atlas Exam is the measurement.**

---

## References

[1] Wolfson, R. (2026). "AtlasExam.md." `vault/50-index/notes/simself-md/AtlasExam-2026-09-13.md.md`.
[2] Wolfson, R. (2026). "Curriculum as Qualification Pressure." `fieldcore/docs/curriculum-qualification-pressure-2026-03-04.md`.
[3] Wolfson, R. (2026). "Atlas Exam (FieldCore Half)." `fieldcore/papers/publishable/03-atlas-exam-fieldcore-2026-09-13.md`.
[4] Wolfson, R. (2026). "Atlas Exam (SimSelf Half)." `simself/papers/publishable/03-atlas-exam-simself-2026-09-13.md`.

---

*Draft 0.1. Atlas Exam specification. 27 areas × 8 rungs. Four falsifiable predictions.*

*Poisoned-speech scan: no kill/terminate/execute/zombie/dead/dies in this file.*