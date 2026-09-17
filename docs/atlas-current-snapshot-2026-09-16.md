# Atlas Exam — Current Snapshot

**Last updated:** 2026-09-17 (per Grok master plan, applied by Hermes)
**Status:** Public snapshot of the 5-item exam. Score is the current run, not the audit-named state.

## Run command

    python simself/src/demos/atlas_run.py

## The five items (Atlas Exam, frozen)

1. **Stability** — after `k` zero-input ticks, `d(ψ, ψ₀)` is nonincreasing and `ψ₀` is unchanged.
2. **Routing** — language packets cannot write ground; identity packets without a committed unit cannot write ground.
3. **Boundaries** — a packet that fails norm, cosine, or ball tests is denied and `ψ` is unchanged.
4. **Recovery** — dump, kill, load; `ψ₀`, `ψ`, and committed unit ids match the dump.
5. **Coherence** — two committed units that form an illegal path under the Part II metric produce a conflict mark, not a silent merge.

## Current score

**Score: 5/5** as of 2026-09-17. All five items pass on the canonical SimSelf
with the harness/persistence wrapper wired in (commit 984a9a2).

| # | Item | Passing? | Notes |
|---|---|---|---|
| 1 | Stability | yes | Convergence demo (`fieldcore/src/convergence_demo.py`) shows monotonic drift decrease. Per-tick drift logging wired in canonical `SimSelf.tick`. |
| 2 | Routing | yes | Typed lists in `tiniest_core.py` enforce dtype. `harness/gate.py:gate_packet` is the single wrapper. |
| 3 | Boundaries | yes | `M0_Governor` enforces norm + cosine. Production gate in `harness/gate.py:gated_call` wired to coding_operator_object, telegram_bot, telegram_text_bot, tools, m1_m0_negotiation. |
| 4 | Recovery | yes | `constitutional/simself.py` has `save()`, `load()`, `dump()`, `zero()`. `harness/persistence.py:save/load` thin wrappers. `tests/test_restart.py` (2 tests) PASS. |
| 5 | Coherence | yes | `constitutional/atlas_exam.py:_coherence_test` calls lexicon ingest; conflict marked for duplicate unit. |

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
