# Agent OS Methodology

Extracted from `z33.txt` (M3 cleanup 2026-08-08). Generic engineering loop, no FieldCore fantasy.

The agent operating system is a simple loop: plan → build → test → log → decide. The goal is verified outcomes over fast guesses, with auditable decisions.

## Core Approach
- Treat every meaningful task as an execution loop, not a one-shot attempt.
- Optimize for verified outcomes over fast guesses.
- Keep decisions explicit so progress is auditable.

## Planning Discipline
- Start in plan mode for any non-trivial request.
- Define scope, constraints, and a clear "done" condition before implementation.
- If facts change or a step fails, pause execution and re-plan.

## Execution Loop
Repeat: Build → Test → Log → Decide.
- **Build** the smallest meaningful change.
- **Test** immediately against expected behavior.
- **Log** what changed, what passed/failed, and what to do next in `progress-log.md`.
- **Decide** to iterate, escalate, or close based on evidence.

## Task Management
- Keep `todo.md` as the live source of truth.
- Break work into subtasks and update status continuously.
- Add follow-up tasks when discovered instead of leaving implicit debt.

## Learning Loop
- After every correction, append to `tasks/lessons.md`.
- Each lesson records: failure, root cause, prevention rule.
- Review lessons at the start of each session before new work.

## Quality Gate
- Never mark complete without proof.
- Require passing tests, clean/understood logs, and observable correctness.
- Final check: "Would a staff engineer approve this as production-ready?"

## Escalation Rules
- Escalate immediately for missing credentials, external outages, or ambiguous requirements.
- After three failed attempts on the same issue, stop and re-plan before continuing.

---
*M3 cleanup 2026-09-05: re-saved to vault/10-minimax/ as canonical copy. Trimmed header cruft.*