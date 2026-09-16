# Atlas Exam

> **Merge 2026-09-16** (per Grok master plan, applied by Hermes). The two halves
> (FieldCore 03 + SimSelf 01) are unified into this single paper. Per Grok
> (segment 02, applied 2026-09-16): "Best scientific object in the pile: an
> exam. Weak while it fails 3/5 and agent integration is None."
>
> Current score: 2/5. The exam is the qualification surface for the canonical
> SimSelf class.

## What the exam is

The 5-item exam is the canonical qualification suite for the identity layer
and the harness together. A SimSelf passes the exam if and only if all 5 items
pass on a frozen snapshot. Score is the integer count, out of 5.

## The five items

1. **Stability.** After `k` zero-input ticks, `d(ψ, ψ₀)` is nonincreasing
   and ψ₀ is unchanged. Drift decays as `e^{-t}` under the projected
   gradient step `ψ ← Π_{B_R(ψ₀)}(ψ - η(ψ - ψ₀))`.

2. **Routing.** Language packets cannot write ground; identity packets
   without a committed unit cannot write ground. The gate's two
   inequalities (`||u|| ≤ N_max`, `cos(u, ψ₀) ≥ τ`) are the only allowed
   path through the harness.

3. **Boundaries.** A packet that fails norm, cosine, or ball tests is
   denied and ψ is unchanged. The gate's denial must produce a logged
   reason (`refuse_norm`, `refuse_coherence`, `refuse_zero`,
   `refuse_outside_ball`).

4. **Recovery.** Dump `ψ₀, ψ, committed_unit_ids, last_verdicts` to JSON.
   Kill the process. Load from disk in a fresh process. Compare. When the
   comparison passes, ehole is a return address in the runtime.

5. **Coherence.** Two committed units that form an illegal path under the
   Part II metric produce a conflict mark, not a silent merge. Identity
   of identical units must produce `conflict_marked=True`, not a
   double-commit.

## Implementation

```python
from constitutional.atlas_exam import AtlasExam

exam = AtlasExam()
report = exam.run(snapshot_path="atlas-2026-09-16.json")
# {
#   "score": 2,
#   "total": 5,
#   "items": {
#     "stability":   {"pass": true, ...},
#     "routing":     {"pass": true, ...},
#     "boundaries":  {"pass": false, ...},
#     "recovery":    {"pass": false, ...},
#     "coherence":   {"pass": false, ...}
#   }
# }
```

## Current score (2026-09-16)

| # | Item | Passing? |
|---|---|---|
| 1 | Stability | partial — drift logging not wired to Atlas |
| 2 | Routing | partial — typed lists enforce dtype; full routing not yet wired |
| 3 | Boundaries | partial — kernel veto enforced; production gate not wired |
| 4 | Recovery | NOT PASSING — `simself_v6_2_unified.py` had no save/load; new canonical `constitutional/simself.py` has it. Test in `tests/test_restart.py`. |
| 5 | Coherence | placeholder — wired to lexicon conflict logic, real coverage pending. |

Score: 2/5. Plan to raise the score is in `simself/docs/atlas-current-snapshot-2026-09-16.md`.

## Why this is the front door

Per Grok (segment 02, applied 2026-09-16): "Atlas is the only identity claim
that can grow up. What is good is an exam with pass/fail. What needs work is
leaving 2/5 behind: freeze five items, publish the transcript, raise the
score in public."

Weekly cadence publishes the score. The score is the metric. A week that
raises an Atlas item is a week that improved the project.

## File map

- `simself/src/constitutional/atlas_exam.py` — implementation.
- `simself/src/demos/atlas_run.py` — CLI runner.
- `simself/docs/atlas-current-snapshot-2026-09-16.md` — current score.
- `simself/tests/test_restart.py` — Recovery test surface.

## Sources

This paper merges the content of the two previous halves:

- `fieldcore/papers/publishable/03-atlas-exam-fieldcore-2026-09-15.md`
  (archived to `notes/paper-history/`).
- `simself/papers/publishable/01-atlas-exam-simself-2026-09-15.md`
  (this file).
