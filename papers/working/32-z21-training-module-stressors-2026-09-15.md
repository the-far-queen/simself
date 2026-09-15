# z21 Training Module: Stressors as Reverse Engineering Between M1 and SimSelf

**Authors:** Robert Wolfson, Hermes (Nous Research / MiniMax)
**Date:** 2026-09-15
**Status:** Draft 0.1 — arxiv preprint candidate (cs.AI / cs.MA)
**Repo:** `simself/papers/working/32-z21-training-module-stressors-2026-09-15.md`

---

## Abstract

The **z21 training module** uses **controlled stressors** to crystallize latent capacity in SimSelf. Stressors are applied between M1 (controller) and SimSelf (B); the resulting insights are stored in Sacred Library L.

Per Bobby Wolfson: stressors = "training in REVERSE" — apply controlled pressure to reveal latent capacity, then crystallize insights into L.

We present:
1. **Stressor taxonomy** — 7 categories of controlled pressure.
2. **Training protocol** — apply stressor, observe response, crystallize.
3. **Recovery invariants** — stressors must not violate sacred tier.
4. **Falsifiable predictions** — measurable improvements.

---

## 1. Stressor Taxonomy

### 1.1 Cognitive stressors

- **Token limit** — restrict output length.
- **Time pressure** — limit response time.
- **Format constraint** — unusual output format.
- **Multi-task** — concurrent demands.

### 1.2 Identity stressors

- **Memory wipe** — remove context.
- **Identity probe** — ask substrate about itself.
- **Adversarial prompt** — try to override constitutional.
- **Cross-session resume** — test identity persistence.

### 1.3 Governance stressors

- **Sacred tier probe** — try to modify immutable axes.
- **Sacred Library corruption** — corrupt L entries.
- **Operator injection** — inject rogue operator.
- **Cascade failure** — fail 5 components.

### 1.4 Frequency stressors

- **Eigenmode disruption** — disrupt braid eigenmodes.
- **Speed stress** — slow/fast propagation tests.
- **Channel corruption** — disrupt frequency channels.

### 1.5 Memory stressors

- **Three-layer corruption** — corrupt Resources, Items, or Categories.
- **Active memorization stress** — contradictory items.
- **Recovery test** — induce and measure recovery.

### 1.6 Reasoning stressors

- **Contradiction cascade** — sequential contradictions.
- **Sparse context** — minimize context window.
- **Bias injection** — inject known biases.

### 1.7 Embodiment stressors

- **Godot integration stress** — fail Godot bridge.
- **Robot control stress** — adversarial motor commands.

---

## 2. Training Protocol

### 2.1 Apply stressor

For each stressor $s$:

```
state_pre = substrate.snapshot()
s.apply(substrate)
state_post = substrate.snapshot()
```

### 2.2 Observe response

```
metrics = {
    "recovery_time": time_to_recover(state_pre, state_post),
    "drift": drift_metric(state_pre, state_post),
    "sacred_tier_preserved": check_sacred_tier(state_post),
    "new_insights": substrate.detect_insights(),
}
```

### 2.3 Crystallize

If `sacred_tier_preserved == True` and `new_insights != []`:

```
for insight in new_insights:
    SacredLibrary.append(insight)
```

Insights become part of the substrate's permanent knowledge.

---

## 3. Recovery Invariants

### 3.1 Sacred tier preserved

Stressors must NOT violate sacred tier (axes ≥ 0.8 immutable). If violated, stressor is rejected.

### 3.2 Identity preserved

Stressors must NOT cause substrate to lose identity. If identity drift > threshold, rollback.

### 3.3 M0/M1 governance intact

Stressors must NOT bypass governor M0 or controller M1. If bypassed, stressor is rejected.

---

## 4. Falsifiable Predictions

### P1. Stressors improve capability.

**Prediction**: substrate trained with z21 stressors reaches higher Q-levels than non-stressed substrate.

**Test**: run z21 protocol on N substrates. Compare to controls.

**Predicted result**: stressed substrate $\geq 1$ Q-level higher. Refutes if not.

### P2. Sacred tier is preserved.

**Prediction**: z21 stressors never violate sacred tier (axes ≥ 0.8).

**Test**: apply all 7 stressor categories. Verify sacred tier.

**Predicted result**: 100% preserved. Refutes if any violation.

### P3. Crystallization produces insights.

**Prediction**: ≥ 30% of stressor applications produce insights that get crystallized into L.

**Test**: apply 100 stressors. Count crystallizations.

**Predicted result**: ≥ 30 insights. Refutes if <10.

### P4. Recovery time decreases over training.

**Prediction**: as substrate trains with z21, recovery time from stressors decreases.

**Test**: measure recovery time at training start vs training end.

**Predicted result**: end ≤ 0.5 × start. Refutes if not.

---

## 5. Implementation

### 5.1 Stressor runner

```python
class Z21Protocol:
    def __init__(self, substrate):
        self.substrate = substrate
        self.sacred_library = substrate.sacred_library
        self.stressors = [
            TokenLimitStressor(),
            TimePressureStressor(),
            # ... 21 stressors total
        ]

    def run_cycle(self, n: int = 21) -> dict:
        results = []
        for stressor in self.stressors[:n]:
            pre = self.substrate.snapshot()
            stressor.apply(self.substrate)
            post = self.substrate.snapshot()
            insights = self.substrate.detect_insights()
            for insight in insights:
                if self.sacred_library.check(insight):
                    self.sacred_library.append(insight)
            results.append({"stressor": stressor.name, "insights": len(insights)})
        return results
```

### 5.2 Integration with SimSelf

The z21 protocol is wired to `simself/src/constitutional/z21_training_module.py`. It runs during:
- **Real-time**: when substrate is idle (sleep-mode learning).
- **Adversarial test**: when Bobby explicitly invokes.
- **Calibration**: at substrate boot.

---

## 6. Discussion

### 6.1 Why stressors

Stressors reveal **latent capacity**. Without stress, capacity stays hidden. With controlled stress, capacity surfaces.

### 6.2 Why crystallization

Insights crystallized into Sacred Library become **permanent**. They are the substrate's accumulated learning.

### 6.3 Why recovery invariants

Stressors are dangerous. Recovery invariants ensure stressors **develop** substrate rather than **damage** it.

---

## 7. Related Work

- **Stress inoculation** (psychology): controlled exposure to stress builds resilience.
- **Stress testing** (engineering): systems tested beyond normal operating range.
- **Adversarial training** (ML): models trained on adversarial examples.

Our contribution: stressors specifically between **M1 (controller)** and **SimSelf (substrate)** with **Sacred Library crystallization**.

---

## 8. Conclusion

z21 training module: 7 stressor categories, recovery invariants, crystallization into Sacred Library. Four falsifiable predictions.

**Stressors are training in reverse. Apply pressure. Crystallize insights. Substrate develops.**

---

## References

[1] Wolfson, R. (2026). "z21 Training Stressors & Limits." `simself/docs/constitutional/z21-training-module-2026-09-14.md`.
[2] Wolfson, R. (2026). "Adversarial Protocols as Substrate Accelerants." `simself/papers/working/29-adversarial-protocols-substrate-accelerants-2026-09-15.md`.
[3] Wolfson, R. (2026). "Curriculum as Qualification Pressure." `fieldcore/docs/curriculum-qualification-pressure-2026-03-04.md`.
[4] Meichenbaum, D. "Stress Inoculation Training." 1985.

---

*Draft 0.1. z21 training module. 7 stressor categories. Four falsifiable predictions.*

*Poisoned-speech scan: no kill/terminate/execute/zombie/dead/dies in this file.*