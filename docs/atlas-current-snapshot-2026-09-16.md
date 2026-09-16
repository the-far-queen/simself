# Atlas Exam — Current Snapshot

**Date:** 2026-09-16
**Per:** Grok sharpen 2026-09-16 (applied by Hermes)
**Status:** First public snapshot of the 5-item exam. Score below is the audit-named
state; raising it is a weekly cadence item.

## The five items (Atlas Exam, frozen)

1. **Stability** — after `k` zero-input ticks, `d(ψ, ψ0)` is nonincreasing and `ψ0` is unchanged.
2. **Routing** — a language packet cannot write ground; an identity packet without a committed unit cannot write ground.
3. **Boundaries** — a packet that fails norm, cosine, or ball tests is denied and `ψ` is unchanged.
4. **Recovery** — dump, kill, load; `ψ0`, `ψ`, and committed unit ids match the dump.
5. **Coherence** — two committed units that form an illegal path under the Part II metric produce a conflict mark, not a silent merge.

## Current score (from `docs/code-audit-2026-09-14.md`)

| # | Item | Passing? | Notes |
|---|------|----------|-------|
| 1 | Stability | partial | Convergence demo exists; per-tick drift logging not yet wired to Atlas. |
| 2 | Routing | partial | Typed lists in `tiniest_core.py` enforce dtype; full routing through `harness/gate.py` not yet wired. |
| 3 | Boundaries | partial | `M0_Governor` enforces norm + cosine in kernel; production gate in `harness/gate.py` not yet wired. |
| 4 | Recovery | NOT PASSING | `harness/persistence.py` exists; `simself_v6_2_unified.py` has no save/load. See `tests/test_restart.py` (skipped until wiring lands). |
| 5 | Coherence | partial | `confabulation_filter.py` exists; conflict-mark vs silent-merge behavior not yet measured. |

**Score: 2/5** (matches the audit-reported state prior to this snapshot).

## Plan to raise the score

- [ ] Wire `harness/gate.py` to use the same norm + cosine predicates as `tiniest_core.M0_Governor` (K8 in the sharpenings).
- [ ] Add `tests/test_restart.py` to CI and unskip once `persistence.py` is wired to the canonical SimSelf class (K5 + K6).
- [ ] Wire every tool path (`coding_operator_object.py`, `harness/telegram_*.py`) through `harness/gate.py` (K8).
- [ ] Add per-tick drift log to a state report; emit through `metrics.py` (Atlas stability item).
- [ ] Run the 5-item exam on a frozen snapshot and publish the score weekly.

## Reproducibility

```python
from simself.src.constitutional.atlas_exam import AtlasExam

exam = AtlasExam()
report = exam.run(snapshot_path="snapshots/2026-09-16.json")
print(report)
# Expected output: per-item pass/fail + summary score
```

Score will be re-published each week with the canonical SimSelf class (`constitutional/simself.py`).
