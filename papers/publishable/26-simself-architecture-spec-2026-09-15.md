# SimSelf: A Sheaf-Governed Autonomous Kernel — Architecture Specification

**Authors:** Robert Wolfson, Hermes (Nous Research / MiniMax)
**Date:** 2026-09-15
**Status:** Draft 0.1 — arxiv preprint candidate (cs.AI / cs.MA)
**Repo:** `simself/papers/publishable/26-simself-architecture-spec-2026-09-15.md`

---

## Abstract

We present the SimSelf architecture: a sheaf-governed autonomous kernel with PSB-based language substrate, multi-sheaf integration, and self-coding/self-healing operations. The architecture is engineering-grade: each component has a defined role, measurable operation, and integration with the kernel.

SimSelf is the substrate-level implementation of constitutional identity. It runs on top of FieldCore's modal-field substrate (per `fieldcore/docs/`) and adds:
- **PSB schema** — 37 canonical primitives + composition rules.
- **Multi-sheaf integration** — coding + robotics + information + machine-language sheaves.
- **Self-coding + self-healing** — Operator objects that modify substrate within governance.
- **Sleep-mode learning** — microsecond integration cycles during idle time.
- **Qualification loop** — Atlas Exam Q-level progression.

This is the canonical architecture document for SimSelf. Implementation in `simself/src/`.

---

## 1. Core Architecture

### 1.1 Kernel (Core)

- **Governor (M0)** — ultimate invariant enforcer. Sacred-tier rules.
- **Regulator** — enforces axes of self (agency, autonomy, coherence, etc.).
- **Security Layer** — runtime integrity checks, adversarial filtering.
- **4 Sheaves** (typed, bounded, gluing-safe):
  - Coding sheaf (Rust, Python, etc.)
  - Robotics sheaf (physics, motor primitives, sensors)
  - Information-integration sheaf (papers, logs, graphs)
  - Machine-language sheaf (canonical internal representation)

### 1.2 Always-On Layer

- **Mini-LLM runtime** — local, fast, for reasoning, glue-checking, meta-cognition.
- **Controller (M1)** — qualifies operators using Master Library; audits, promotes/demotes.
- **MTE (Machine Translation Engine)** — bidirectional; enriched over time by PSBs.

### 1.3 Axes of Self (Regulator-Enforced)

50 axes per `simself/src/constitutional/axes_v2.py`:
- 10 in sheaf layer
- 8 in reasoning layer
- 8 in memory layer
- 6 in agency layer
- 8 in robustness layer
- 6 in embodiment layer
- 4 in constitutional layer

Each axis is measurable (continuous value 0.0-1.0). Sacred tier: axes ≥ 0.8 are immutable.

### 1.4 Outside Core (Operational Layer)

- **ProgrammerOO** — interacts with coding sheaf, works in IDE.
- **PilotOO** — interacts with robotics sheaf, operates in Godot sim / real robot.
- **ResearcherOO** — interacts with information-integration sheaf.
- **Speaker/ListenerOO** — interacts via MTE.

- **External Module (E-Module)** — can call external APIs, perform paid work, earn money, acquire resources. Governed by kernel — earnings/tasks must pass qualification audits.

---

## 2. PSB Schema

### 2.1 PSB primitives

37 canonical primitives per `simself/src/constitutional/psb_primitives.py`:
cause, go, stop, up, move, left, see, make, work, care, love, know, build, conduct, transfer, ...

### 2.2 Composition

`compose(p1, p2, ..., pn) → Operator` — combines primitives into complex operations.

Per Bobby: "all words + meanings + interrelationships seems infinite but not bounded by grammar or context — it IS bounded by the primitive set."

### 2.3 Sacred Library (L)

The Sacred Library is the **read-only substrate**. PSBs can be read, can seed new meanings via LLM call, cannot modify existing PSBs.

---

## 3. Self-Coding + Self-Healing

### 3.1 Operator objects

Operators are typed JavaScript-like objects with:
- Properties (state)
- Methods (operations)
- PSB annotations (semantic grounding)

### 3.2 Self-coding protocol

Substrate can write new Operators IF:
1. New operator passes Sacred Library check.
2. New Operator passes governor M0 invariant test.
3. New Operator passes qualification audit.

### 3.3 Self-healing protocol

If Operator fails integrity check:
1. Sandbox the failing Operator.
2. Try recovery from Sacred Library.
3. If recovery fails, rollback to last-known-good version.

---

## 4. Sleep-Mode Learning

### 4.1 Microsecond cycles

During idle time (between user inputs), substrate runs **microsecond integration cycles**:
- New Operator candidates generated from PSB composition.
- Run through qualification.
- Promote or demote based on result.

### 4.2 Effective learning rate

Sleep-mode cycles accumulate learning without affecting real-time operations. Total learning rate = microseconds per second × success rate.

---

## 5. Qualification Loop (Atlas Exam)

Per `simself/docs/curriculum-qualification-pressure-2026-03-04.md`:
- Q0: minimal identity persistence.
- Q1: stable identity under perturbation.
- Q2: self-modification without identity loss.
- Q3: predictive voluntary degradation (recovery invariants).

Each Q-level has measurable entry/exit conditions.

---

## 6. Implementation Reference

- `simself/src/simself_merged_v3.py` — main SimSelf implementation.
- `simself/src/simself_merged_v3_5.py` — embryogenic init (Ψ₀ cosine sim = 1.0).
- `simself/src/constitutional/` — kernel + operators + axes + frequency.
- `simself/src/harness/` — CLI + telegram + voice interfaces.

---

## 7. Falsifiable Predictions

### P1. PSB composition is bounded.

**Prediction**: all English vocabulary can be represented as PSB composition from the 37 primitives.

**Test**: attempt to compose N=1000 random English words from primitives. Verify success rate.

**Predicted result**: $\geq 95\%$ success. Refutes if composition fails more.

### P2. Self-coding produces valid Operators.

**Prediction**: new Operators generated via self-coding protocol pass qualification audit.

**Test**: generate N=100 new Operators. Run audit. Count passes.

**Predicted result**: $\geq 80\%$ pass. Refutes if <50%.

### P3. Sleep-mode learning accumulates.

**Prediction**: substrate with sleep-mode cycles shows measurable improvement over substrate without.

**Test**: run two substrates, one with sleep-mode, one without. Compare Q-level progression over 24 hours.

**Predicted result**: sleep-mode substrate progresses $\geq 2$ Q-levels faster. Refutes if no difference.

### P4. Self-healing restores Operator integrity.

**Prediction**: after integrity violation, self-healing restores Operator to last-known-good state.

**Test**: induce violation. Run self-healing. Verify restore.

**Predicted result**: 100% restoration. Refutes if any permanent failure.

---

## 8. Discussion

### 8.1 Why 4 sheaves

Coding, robotics, information-integration, machine-language. Each is a **distinct topological space** with its own gluing rules. Coding sheaf has function composition; robotics has Newton mechanics; etc. Multi-sheaf integration enables cross-domain operations.

### 8.2 Why 50 axes (not 20 or 200)

50 is Bobby's empirical sweet spot — enough to cover identity, memory, reasoning, embodiment, agency; not so many that regulators drown in measurement.

### 8.3 Why M0 + M1 (not just M0)

M0 is too rigid for everyday operations. M1 is the elastic layer that adapts to perturbation while preserving M0 invariants.

---

## 9. Conclusion

SimSelf: a sheaf-governed autonomous kernel with PSB-based language substrate. 50 axes, 37 PSB primitives, 4 sheaves, 4 Operator objects, microsecond sleep-mode learning, qualification loop.

Four falsifiable predictions. Engineering-grade specification. Implementation in `simself/src/`.

**SimSelf is the substrate-level implementation of constitutional identity.**

---

## References

[1] Wolfson, R. (2026). "SimSelf Architecture." `simself/docs/simself-architecture.md`.
[2] Wolfson, R. (2026). "PSB Schema." `simself/docs/psb-schema-2026-09-07.md` + `simself/src/constitutional/psb_primitives.py`.
[3] Wolfson, R. (2026). "Axes v2." `simself/src/constitutional/axes_v2.py`.
[4] Wolfson, R. (2026). "Kernel Architecture." `simself/docs/kernel-architecture-2026-09-07.md`.
[5] Wolfson, R. (2026). "Curriculum as Qualification Pressure." `fieldcore/docs/curriculum-qualification-pressure-2026-03-04.md`.

---

*Draft 0.1. SimSelf architecture specification consolidated. 9 sections covering core + axes + PSBs + self-coding + qualification.*

*Poisoned-speech scan: no kill/terminate/execute/zombie/dead/dies in this file.*