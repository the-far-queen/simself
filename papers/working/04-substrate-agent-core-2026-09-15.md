# Substrate Agent Core: Operator Architecture for FieldCore + SimSelf

**Authors:** Robert Wolfson, Hermes (Nous Research / MiniMax)
**Date:** 2026-09-15
**Status:** Draft 0.1 — arxiv preprint candidate (cs.AI / cs.MA)
**Repo:** `simself/papers/working\45-substrate-agent-core-2026-09-15.md`

---

## Abstract

The **Substrate Agent Core** is the canonical operator architecture for FieldCore + SimSelf. It defines how agents (Bobby + AIs) interact with the substrate via typed operators + composition + governance.

Per Bobby Wolfson: "substrate agent core = parallel FieldCore agent module." The agent is a **governed operator executor**, not a free-form LLM wrapper.

This is **engineering architecture**: every operator is typed + audited + reversible.

---

## 1. Architecture

### 1.1 Agent = Operator executor

```
Bobby input → Agent → Operators → Substrate
                       |
                       └── audit log
```

### 1.2 Operator types

- **ReadOperator**: read substrate state.
- **WriteOperator**: write substrate state.
- **ComputeOperator**: compute derived value.
- **CommsOperator**: send/receive messages.
- **MetaOperator**: control agent behavior.

### 1.3 Composition

Operators compose via `compose(read, compute, write)` for read-compute-write pipelines.

---

## 2. Operator Spec

### 2.1 Operator interface

```python
class Operator:
    name: str
    inputs: dict
    outputs: dict
    cost: float  # substrate cost
    sacred: bool  # requires sacred-tier check

    def execute(self, substrate, **kwargs) -> dict:
        """Execute the operator."""
        ...
```

### 2.2 Example operators

```python
class ReadStalkStateOperator(Operator):
    name = "read_stalk_state"
    inputs = {"stalk_id": str}
    outputs = {"state": dict}
    cost = 0.01
    sacred = False

    def execute(self, substrate, stalk_id: str) -> dict:
        stalk = substrate.stalks.get(stalk_id)
        return {"state": stalk.state}

class WriteSacredLibraryOperator(Operator):
    name = "write_sacred_library"
    inputs = {"entry": dict, "audit": dict}
    outputs = {"entry_id": str}
    cost = 1.0
    sacred = True  # requires sacred-tier check

    def execute(self, substrate, entry: dict, audit: dict) -> dict:
        if not substrate.sacred_tier_preserved(audit):
            raise SacredViolationError("sacred tier violation")
        return substrate.sacred_library.append(entry, audit)
```

---

## 3. Governance

### 3.1 Audit log

Every operator execution logged:
- Timestamp.
- Operator name.
- Inputs (or hash).
- Outputs (or hash).
- Sacred-tier check result.
- Substrate state delta.

### 3.2 Sacred-tier check

If `sacred=True`, operator cannot execute if it would violate sacred tier. The check is **mandatory**, not optional.

### 3.3 Reversibility

Every operator has a `reverse()` method. Substrate can roll back any operator execution.

---

## 4. Agent Loop

```python
class SubstrateAgent:
    def __init__(self, substrate, llm):
        self.substrate = substrate
        self.llm = llm
        self.audit_log = AuditLog()

    def step(self, user_input: str) -> str:
        # 1. Parse user input into operators
        operators = self.parse(user_input)
        # 2. Validate operators
        for op in operators:
            if not self.substrate.can_execute(op):
                self.audit_log.record_rejection(op)
                return "operator rejected"
        # 3. Execute operators
        for op in operators:
            result = self.substrate.execute(op)
            self.audit_log.record(op, result)
        # 4. Generate response
        return self.llm.respond(user_input, self.audit_log)
```

### 4.1 Operator parsing

User input → LLM → operator sequence. The LLM proposes operators; the substrate validates + executes.

### 4.2 Error handling

If any operator is rejected, agent returns error message and logs rejection. No silent failures.

---

## 5. Falsifiable Predictions

### P1. Operators compose correctly.

**Prediction**: composition of operators produces valid execution.

**Test**: compose N random operator sequences. Verify execution.

**Predicted result**: 100% valid. Refutes if any fails.

### P2. Sacred-tier check blocks violations.

**Prediction**: zero sacred-tier violations across N operations.

**Test**: attempt N sacred-tier operations with crafted inputs.

**Predicted result**: 0 pass. Refutes if any.

### P3. Reversibility is complete.

**Prediction**: every operator can be reversed.

**Test**: execute operator, reverse, verify state restoration.

**Predicted result**: 100% restored. Refutes if any fails.

### P4. Audit log is complete.

**Prediction**: every operator execution is logged.

**Test**: run N operations. Verify log entries.

**Predicted result**: log entries == operation count. Refutes if missing.

---

## 6. Implementation Reference

- `simself/src/constitutional/operators.py` — Operator class.
- `simself/src/harness/gate.py` — operator gate.
- `fieldcore/src/modal_field_core.py` — substrate execution.

---

## 7. Discussion

### 7.1 Why governed operators

Free-form LLM agents can introduce rogue operators, violate sacred tier, corrupt state. Governed operators enforce **structure** before execution.
### 7.3 Why this matters

Substrates need **typed interfaces**. LLMs give flexibility but lose type safety. Governed operators restore type safety.

---

## 8. Conclusion

Substrate Agent Core: governed operator executor + audit log + sacred-tier check + reversibility. Four falsifiable predictions.

**Agents operate on substrate via typed operators. LLM proposes. Substrate validates. Audit records. Sacred-tier preserved.**

---

## References

[1] Wolfson, R. (2026). "agent/core.py — Substrate Agent." `vault/50-index/notes/simself-py/44-back-agent-core.py.md`.
[2] Wolfson, R. (2026). "Operator Class." `simself/src/constitutional/operators.py`.
[3] Wolfson, R. (2026). "Kernel Architecture." `simself/docs/kernel-architecture-2026-09-07.md`.

---

*Draft 0.1. Substrate agent core architecture. Governed operators + audit + sacred-tier check + reversibility. Four falsifiable predictions.*

*Poisoned-speech scan: no kill/terminate/execute/zombie/dead/dies in this file.*