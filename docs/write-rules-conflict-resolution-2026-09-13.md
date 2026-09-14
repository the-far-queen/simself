# Write Rules & Conflict Resolution

Module Q (Qualification) → Module L (Sacred Library) governance.

---

## Core Principle

> "Without explicit write rules, conflict resolution becomes ill-posed. First define what is even allowed to become state."

**Memory as governed state, not accumulated text.**

---

## Canonical Write Rule Classes

### Allowed to Write (Default)

- **Stable preferences** — time-invariant or slow-moving
- **Safety constraints**
- **Repeated behaviors** crossing a confidence threshold
- **Recovery invariants** — what worked under failure
- **Operator-issued overrides** with provenance

### Disallowed to Write

- Single-shot utterances
- Emotional transients
- Unverified instructions
- Chat history
- Minillm reflexes without post-idle validation

---

## Write Authority (Layered)

| Role | Authority |
|------|-----------|
| **SimSelf (Pilot)** | Propose only |
| **M1 (Instructor)** | Synthesize + stage |
| **M0 (Governor)** | Validate invariants + commit |

---

## Conflict Resolution Logic (Deterministic Precedence)

When conflicts arise:

1. **Safety invariants** — hard end
2. **Qualified Sacred Library state**
3. **Recent, high-confidence operator input**
4. **English sheaf commands**
5. **Minillm reflex output**

### Example

> English sheaf: "move fast"
> Sacred Library: "user prefers quiet / slow operation"

**Resolution:**
- English sheaf = intent, not authority
- M1 resolves to "optimize speed within quiet envelope"
- No overwrite unless preference explicitly revoked and qualified

**Result:** No dual truths — state transitions with history.

---

## Why This Matters

- Write rules define **state space**
- Conflict logic defines **state evolution**
- Reversing order → stochastic patching

---

## Engineering Status

- Memory: deterministic
- Decay: scheduled
- Authority: layered
- Qualification: explicit

This is **OS-grade state management**, not "agent memory."

---

## Next Step (Downstream)

Formalizing confidence thresholds (Q-levels) per memory class.

---

*Source: Write Rules + Conflict Resolution for Module Q → L*
*Saved: 2026-03-04*
