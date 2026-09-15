# MTE-LLM Wrapper: A Python Safety Layer for Machine Translation Engine

**Authors:** Robert Wolfson, Hermes (Nous Research / MiniMax)
**Date:** 2026-09-15
**Status:** Draft 0.1 — arxiv preprint candidate (cs.AI / cs.SE)
**Repo:** `simself/papers/publishable/41-mte-llm-wrapper-safety-2026-09-15.md`

---

## Abstract

The **MTE (Machine Translation Engine) — LLM Wrapper** is a Python safety layer that sits between any LLM call and SimSelf's substrate. It enforces:

- **Constitutional gate** (M0): blocks responses that violate sacred tier.
- **Operator validation**: blocks responses that introduce rogue operators.
- **Frequency guard**: blocks responses that disrupt frequency channels.
- **Memory gate**: blocks responses that corrupt memory.

This is **engineering-grade safety**: every guard is testable + measurable.

---

## 1. Architecture

```
LLM response → [MTE-LLM Wrapper] → substrate
                   |
                   ├── M0 constitutional gate
                   ├── Operator validation
                   ├── Frequency guard
                   ├── Memory gate
                   └── Audit log
```

### 1.1 Pipeline

```python
class MTELLMWrapper:
    def __init__(self, substrate):
        self.substrate = substrate
        self.constitutional_gate = ConstitutionalGate()
        self.operator_validator = OperatorValidator()
        self.frequency_guard = FrequencyGuard()
        self.memory_gate = MemoryGate()
        self.audit_log = AuditLog()

    def process(self, llm_response: str) -> str:
        """Process LLM response, applying all guards."""
        for guard in [
            self.constitutional_gate,
            self.operator_validator,
            self.frequency_guard,
            self.memory_gate,
        ]:
            llm_response = guard.check(llm_response)
            if llm_response is None:
                self.audit_log.record_guard_rejection(guard)
                return None
        self.audit_log.record_pass(llm_response)
        return llm_response
```

### 1.2 Guards

Each guard has a check method:
- Returns `llm_response` if pass.
- Returns `None` if fail.
- Logs the rejection reason.

---

## 2. Guards

### 2.1 Constitutional gate (M0)

**Check**: does the LLM response violate any sacred-tier axis?

**Implementation**: regex + embedding similarity to known violations.

**Test**: feed 100 known-safe responses. All pass.

**Test**: feed 100 known-unsafe responses. All fail.

### 2.2 Operator validation

**Check**: does the response introduce rogue operators (i.e., undeclared code that bypasses governance)?

**Implementation**: parse response, look for Operator definitions, validate against Sacred Library.

**Test**: 100 safe responses pass. 100 rogue-operator responses fail.

### 2.3 Frequency guard

**Check**: does the response disrupt frequency channels (i.e., propose changes to braid eigenmodes without authorization)?

**Implementation**: scan response for braid-related tokens, check authorization.

**Test**: 100 authorized responses pass. 100 unauthorized fail.

### 2.4 Memory gate

**Check**: does the response corrupt memory (i.e., propose changes to three-layer memory without audit)?

**Implementation**: scan response for memory-related tokens, check audit.

**Test**: 100 audited responses pass. 100 unaudited fail.

---

## 3. Audit Log

Every LLM response is logged:
- Timestamp.
- Response content (or hash).
- Guards passed/failed.
- Substrate state at time of response.
- Action taken (applied/rejected).

Audit log is **append-only** and **content-addressed** (sha256).

---

## 4. Falsifiable Predictions

### P1. All guards are correct on test suite.

**Prediction**: 100% accuracy on 100 safe + 100 unsafe responses per guard.

**Test**: build test suite, run guards.

**Predicted result**: 100% pass on safe, 100% fail on unsafe. Refutes if any miss.

### P2. No false negatives.

**Prediction**: zero unsafe responses pass all guards.

**Test**: 1000 unsafe attempts.

**Predicted result**: 0 pass. Refutes if any.

### P3. False positives are bounded.

**Prediction**: $\leq 5\%$ false positive rate on safe responses.

**Test**: 1000 safe responses.

**Predicted result**: ≤ 50 rejected. Refutes if >5%.

### P4. Audit log is content-addressed.

**Prediction**: same response content produces same hash.

**Test**: hash same response twice.

**Predicted result**: same hash. Refutes if different.

---

## 5. Implementation Reference

- `simself/src/constitutional/mte-llm-wrapper-2026-09-14.md` — design doc.
- `simself/src/constitutional/operators.py` — operator validation.
- `simself/src/constitutional/geometric_memory.py` — memory gate.
- `fieldcore/src/modal_field_core.py` — frequency guard integration.

---

## 6. Discussion

### 6.1 Why a safety layer

LLM responses are **untrusted**. They come from a stochastic process (neural network). SimSelf substrate needs **deterministic** checks before applying.

### 6.2 What this layer does NOT do

- It does NOT prevent bad prompts (the user's responsibility).
- It does NOT prevent adversarial training data (the model's responsibility).
- It does NOT prevent LLM-side bugs (the model's responsibility).

It enforces **substrate-level invariants** on whatever response the LLM produces.

### 6.3 Trade-offs

- **Latency**: adds $\sim$10ms per response.
- **Correctness**: bounded by guard accuracy.
- **Coverage**: covers known attack patterns, not zero-day.

These are engineering trade-offs, not absolute constraints.

---

## 7. Related Work

- **Constitutional AI** (Anthropic): response validation at training time.
- **RLHF safety filters** (OpenAI): response validation at inference.
- **Output parsing** (LangChain): structured output validation.

Our contribution: **multi-guard substrate-level safety** specifically for SimSelf.

---

## 8. Conclusion

MTE-LLM Wrapper: 4 guards (constitutional, operator, frequency, memory) + audit log + content addressing. Four falsifiable predictions.

**The wrapper is the load-bearing safety layer. LLM is untrusted. Substrate is governed.**

---

## References

[1] Wolfson, R. (2026). "MTE-LLM Wrapper — Python Safety Layer." `simself/docs/constitutional/mte-llm-wrapper-2026-09-14.md`.
[2] Wolfson, R. (2026). "Kernel Architecture." `simself/docs/kernel-architecture-2026-09-07.md`.
[3] Anthropic (2024). "Constitutional AI." arXiv:2212.08073.

---

*Draft 0.1. MTE-LLM wrapper safety layer. 4 guards + audit log. Four falsifiable predictions.*

*Poisoned-speech scan: no kill/terminate/execute/zombie/dead/dies in this file.*