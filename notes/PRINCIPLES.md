# PRINCIPLES — adopted from poteto/brainmaxxing (MIT)

**source:** poteto/brainmaxxing/brain/principles.md + poteto/noodle/brain/principles.md
**date:** 2026-10-06
**license:** MIT (Lauren Tan)
**reason:** lauren's principles are the canonical 2026 agent-engineering principles. simself adopts them unchanged.

These principles govern how agents in this project operate. Every commit, every commit message, every skill, every architectural decision is checked against this list.

## Core

- **foundational-thinking** — start from the simplest unit that exhibits the behavior. don't reach for abstractions until forced to.
- **redesign-from-first-principles** — when something feels wrong, ask what it's trying to do. don't patch around the symptom.
- **subtract-before-you-add** — if a fix requires more code, you're probably adding debt. delete first.
- **outcome-oriented-execution** — measure by what's produced, not by what's attempted.
- **experience-first** — if it doesn't show up at the boundary (user/agent/skill), it doesn't exist.
- **exhaust-the-design-space** — when designing, consider 2-3 alternatives before picking. list assumptions.

## Architecture

- **boundary-discipline** — clear contracts at module boundaries. no implicit dependencies. no shared mutable state across boundaries.
- **make-operations-idempotent** — running twice = running once. re-running save/load/tick is safe.
- **migrate-callers-then-delete-legacy-apis** — never delete a thing that's still being used. move callers first, then remove.
- **serialize-shared-state-mutations** — when state is shared, the writes are sequenced. use locks or single-writer patterns.

## Verification

- **prove-it-works** — claims must be backed by a runnable test or a measured observation.
- **fix-root-causes** — when something breaks, fix the cause not the symptom. if you keep hitting the same kind of bug, the architecture is wrong.

## Delegation

- **cost-aware-delegation** — know the cost of every model call, every I/O, every wall-clock operation. delegate to the cheapest capable substrate.
- **guard-the-context-window** — every token in context costs attention. keep the window clean.
- **never-block-on-the-human** — if you're waiting, you're wasting. log and continue.

## Meta

- **encode-lessons-in-structure** — when something is learned, write it to a skill or a principle file, not a chat transcript.

---

## how this maps to simself

| principle | simself implementation |
|---|---|
| foundational-thinking | constitutional axes start as 2 (identity + ethics) + 6 (sacred) + 12 (resilient) |
| redesign-from-first-principles | fieldcore top-down from manifolds → stalks → gradient flow |
| subtract-before-you-add | legacy/simself_v6_2_unified.py is deprecated, not deleted (migrate-callers-then-delete) |
| outcome-oriented-execution | every docs/notes/papers must be a schema, plan, or test (per PROJECT-ARC.md) |
| experience-first | README.md, AGENTS.md, SKILL.md are first-class — what an agent experiences at the boundary |
| exhaust-the-design-space | atlas_exam.py publishes 5 items; each is an alternative verification of cogency |
| boundary-discipline | src/constitutional/simself.py + src/constitutional/ground.py + src/harness/gate.py — 3 modules, 3 boundaries |
| make-operations-idempotent | sim.save() / sim.load() / sim.tick() / sim.zero() are idempotent |
| migrate-callers-then-delete-legacy-apis | legacy/ has deprecation markers; callers must move first |
| serialize-shared-state-mutations | MVCC persistence (per PROJECT-ARC.md) — multi-version consistency for identity |
| prove-it-works | F1..F5, M1..M5, G1..G5, R1..R5, W1..W5 — every schema has 5 gate tests |
| fix-root-causes | bob's "you do not understand" = stop, redesign, do not patch |
| cost-aware-delegation | M0 governor = 1-bit; M1 = stochastic. deterministic gate owns the architecture |
| guard-the-context-window | constitutional state snapshot = state_snapshot() for LLM ingestion (per docs/simself-merged-v2.md) |
| never-block-on-the-human | M1 → M0 negotiation via gate_packet — agent calls, governor gates |
| encode-lessons-in-structure | .agents/skills/<name>/SKILL.md — every lesson becomes a skill file |

---

*verified by hermes (minimax-m3). raw source: `C:\Users\HP\AppData\Local\hermes\work_repos\poteto-skill-template\brainmaxxing\brain\principles.md` + `noodle/brain/principles.md`*
