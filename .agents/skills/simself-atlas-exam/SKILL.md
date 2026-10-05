---
name: simself-atlas-exam
description: >-
  Use when the user wants to qualify a SimSelf instance, run the 5-item exam, or publish a
  qualification snapshot. Triggers: "atlas exam", "qualification", "atlas", "5-item exam",
  "simself pass/fail".
---

# SimSelf Atlas Exam — qualification suite

The atlas exam is the **5-item qualification suite** that every SimSelf instance must pass before being declared cogent. It is **not** a benchmark. It is the production gate for an instance to be considered operational.

## The 5 items

Per `src/constitutional/atlas_exam.py`:

1. **Constitutional integrity** — all sacred axes within threshold
2. **Gate behavior** — refusal + admission patterns match the spec
3. **Persistence** — save/load roundtrip is identity-preserving
4. **Recovery** — corruption + drift recovery without losing identity
5. **MLTR coverage** — PSB primitives cover the canonical English usage

A pass on all 5 = the instance is qualified. A fail on any one = the instance is held back.

## Running

```python
from src.constitutional.atlas_exam import run

result = run(simself_instance)     # returns AtlasResult
result.publish_json()              # writes JSON snapshot
# or
result.dump(path)                 # explicit path
```

## Interpreting

```json
{
  "qualified": true,
  "items": [
    {"name": "constitutional_integrity", "pass": true, "score": 1.0},
    {"name": "gate_behavior",           "pass": true, "score": 0.95},
    {"name": "persistence",             "pass": true, "score": 1.0},
    {"name": "recovery",                "pass": false, "score": 0.6, "reason": "drift_exceeded_after_recovery"},
    {"name": "mltr_coverage",           "pass": true, "score": 0.85}
  ]
}
```

A failed item carries a `reason` — same reason codes as the gate.

## See also

- `simself-identity`
- `simself-gate`
- `simself-constitution`
- `fieldcore-tiny-core`