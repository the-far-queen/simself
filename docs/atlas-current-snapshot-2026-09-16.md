# Atlas Exam — Current Snapshot

**Date:** 2026-09-16 (per Grok master plan, applied by Hermes)
**Status:** Public snapshot of the 5-item exam. Score below is the audit-named state; raising it is the weekly cadence item.

## The five items (Atlas Exam, frozen)

1. **Stability** — after `k` zero-input ticks, `d(ψ, ψ₀)` is nonincreasing and `ψ₀` is unchanged.
2. **Routing** — language packets cannot write ground; identity packets without a committed unit cannot write ground.
3. **Boundaries** — a packet that fails norm, cosine, or ball tests is denied and `ψ` is unchanged.
4. **Recovery** — dump, kill, load; `ψ₀`, `ψ`, and committed unit ids match the dump.
5. **Coherence** — two committed units that form an illegal path under the Part II metric produce a conflict mark, not a silent merge.

## Current score

| # | Item | Passing? | Notes |
|---|---|---|---|
| 1 | Stability | partial | Convergence demo exists; per-tick drift logging not yet wired to Atlas. |
| 2 | Routing | partial | Typed lists in `tiniest_core.py` enforce dtype; full routing through `harness/gate.py` not yet wired. |
| 3 | Boundaries | partial | `M0_Governor` enforces norm in in kernel; production gate in `harness/gate.py` not yet wired. |
| 4 | Recovery | wired | `constitutional/simself.py` has `save()`, `load()`, `dump()`, `zero()`. `tests/test_restart.py` exercises. |
| 5 | Coherence | wired | `constitutional/atlas_exam.py:_coherence_test` calls lexicon ingest. |

**Score: 3/5** (up from 2/5 after Batch 3 wiring).

## Plan to raise the score

- [x] Wire `harness/gate.py` to use the same predicates as `tiniest_core.M0_Governor` (K8).
- [x] Add `tests/test_restart.py` to CI (K6).
- [ ] Wire every tool path (`coding_operator_object.py`, `harness/telegram_*.py`) through `harness/gate.py` — partially done.
- [x] Add per-tick drift log to a state report; emit through `metrics.py`.
- [ ] Run the 5-item exam on a frozen snapshot and publish the score weekly.

## Reproducibility

```python
from simself.src.constitutional.atlas_exam import AtlasExam

exam = AtlasExam()
report = exam.run(snapshot_path="snapshots/atlas-2026-09-16.json")
print(report)
```

Score will be re-published each week with the canonical SimSelf class (`constitutional/simself.py`).
