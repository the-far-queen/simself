---
name: simself-identity
description: >-
  Use when the user wants the canonical SimSelf kernel — constitutional guard, ψ₀ ground, M0 governor, M1 controller,
  gate_packet, save/load, dump. Triggers: "simself", "identity", "kernel", "constitutional guard", "ground".
---

# SimSelf Identity — canonical kernel

The canonical SimSelf is `src/constitutional/simself.py`. Two legacy siblings (`src/simself_core.py`, `src/simself_v6_2_unified.py`) are deprecated and live in `legacy/`.

## The three objects

- **Hole / ground** — `src/constitutional/ground.py` is the write-protect API for ψ₀.
- **Gate** — `src/harness/gate.py` (production) + `src/constitutional/lexicon/ingest.py` (lexicon) + `fieldcore/src/tiniest-core/tiniest_core.py:M0_Governor` (kernel). Same predicates.
- **Exam** — `src/constitutional/atlas_exam.py` runs the 5-item qualification suite.

## Surface

```python
from src.constitutional.simself import SimSelf
from src.constitutional.ground import ground
from src.constitutional.constitution import Constitution
from src.constitutional.resolution import step
from src.harness.gate import gate_packet, gated_call

sim = SimSelf(ground=ground, constitution=Constitution.defaults())
sim.tick(observation)        # one heartbeat
sim.save()                   # write to disk
sim.load()                   # restore
sim.dump()                   # serialize for inspection
sim.zero()                   # reset to ψ₀
```

## Where to look

| Path | What |
|---|---|
| `src/constitutional/simself.py` | Canonical SimSelf. Ground + ψ + tick + save/load + dump + zero. |
| `src/constitutional/ground.py` | Write-protect on ψ₀. One-shot install, versioned revisions. |
| `src/constitutional/constitution.py` | Axes as functional coordinates with thresholds. |
| `src/constitutional/resolution.py` | Projected gradient step on F. |
| `src/constitutional/atlas_exam.py` | 5-item exam. `run()` publishes JSON. |
| `src/constitutional/lexicon/ingest.py` | Lexicon ingest: gate + cost + admit/commit/refuse. |
| `src/constitutional/psb_primitives.py` | 6 primitive types, `coverage()` measured. |
| `src/constitutional/frequency.py` | Parallel state. ψ untouched. |
| `src/constitutional/adversarial.py` | 21 protocol stubs. |

## Anti-patterns (refused)

- Importing from `legacy/` in new code.
- Editing ψ₀ directly (use `ground.py`).
- Adding a new axis without a threshold + a cost.
- Skipping the gate for "speed."

## See also

- `simself-identity-load` skill for load/save
- `simself-gate` skill for the commit_asset check
- `fieldcore-tiny-core` skill for the math kernel