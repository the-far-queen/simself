# Curriculum as Qualification Pressure

Control-theoretic refinement of M1/M0 architecture and Q-levels.

**Source:** `C:\Users\Admin\Desktop\SimSelf\docs\curriculum_qualification_pressure.md` (2755 bytes, md5 75fcb5fdf3d9d39f054ae76d7de23eb3, saved 2026-03-04)
**Verdict:** CANONICAL — Tier 1 control architecture spec. M0/M1/Q-level primitives align with `kernel-architecture-2026-09-07.md` and `simself_merged_v3.py`.
**Status:** Pushed to simself repo at canonical path.

---

## Core Insight Redefined

> "Curriculum is redefined as qualification pressure, not instruction."

**M1/M0 split = dual-timescale control decomposition:**

| Loop | Speed | Function |
|------|-------|----------|
| **M1 (Controller)** | Fast | elasticity, gain scheduling, mode switching, PLL-style re-lock |
| **M0 (Governor)** | Slow | boundary envelopes, admissible relaxations, invariant protection, post-hoc certification via L |

---

## Meta-Sheaf Interpretation

Multi-layer consistency structure ensuring local adaptations don't violate global invariants.

**Pre-crunching** = error absorption before invariant contact.

---

## M1 Resilience Modes (Formalized)

### Low-Noise Mode
- ε widening
- relaxed semantic matching
- higher tolerance for ambiguity
- objective: reacquire lock

### Semantic-Noise Mode
- clarification protocol
- intent re-projection
- handshake renegotiation
- objective: reconcile intent ↔ physics

---

## Governor Boundary Learning Pipeline

1. **Temporary relaxation** — rule-based, mode-conditioned, time-bounded
2. **Outcome logging** — success / near-miss / failure + context
3. **Idle-cycle review** — outside real-time control
4. **Sacred Library (L) update** — new invariant margins, recovery envelopes, re-certification
5. **M0 redeployment** — versioned, auditable, rollback-capable

---

## Q-Levels Corrected

| Level | Pilot (B) | Controller (M1) | Governor (M0) |
|-------|-----------|-----------------|--------------|
| Q3+ | anticipates instability | pre-emptive mode shift | pre-authorized envelopes |

**Q3+ = Predictive, voluntary degradation prior to invariant contact** (not "autonomous recovery")

---

## The Real Breakthrough

> L stores recovery invariants, not task skills.

- Task policies are brittle
- Recovery patterns are portable
- Invariants generalize across embodiment and domain

Updating with recovery traces (not successes) → robustness, transfer, long-horizon stability.

---

## Q3 Curriculum = Qualification Stress Design

A battery of anticipatory failure scenarios where pilot (B) must:
1. Detect leading indicators via W
2. Predict loss of stability before violation
3. Request M1 mode degradation early
4. Remain within M0 envelopes without emergency override
5. Do this reliably, not once

---

## Phase Transition

**Reactive resilience** → "recover after damage"
**Predictive resilience** → "degrade before damage"

---

## Next Steps (Choose One)

1. Formalize leading indicators for Q3
2. Design a Q3 stress harness
3. Specify M1 mode-degradation taxonomy

---

*Canonical ingestion: 2026-09-15. Pushed to `simself/docs/curriculum-qualification-pressure-2026-03-04.md`. Original preserved at `vault/30-originals/curriculum-qualification-pressure-original-2026-03-04.md` (bit-identical, md5 75fcb5fdf3d9d39f054ae76d7de23eb3).*