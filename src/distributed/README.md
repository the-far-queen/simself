# distributed — Distributed SimSelf primitives

**Pattern:** A mini-SimSelf as a network of self-contained "stalk nodes" running on separate compute cores, gluing asynchronously via governor predicates.

## StalkNode

`simself/src/distributed/stalk_node.py`

Self-contained mini-SimSelf node. Each carries:
- A local embedding (compressed to int8 via log-scale for memory efficiency)
- A set of invariant predicates
- A recovery map (precision lift back to float32)
- An epsilon tolerance for gluing distance checks
- Gluing mechanics with governor-gated merges

### Mixed-precision bridge

The "Tesla mixed-precision" pattern: stay at int8 for normal operation, lift to float32 only when gluing or validating. Saves cycles on edge hardware.

### Usage

```python
from distributed import StalkNode, basic_governor, norm_invariant, energy_invariant

vision = StalkNode(
    local_embedding=[1.0, 2.0, 3.0],
    invariants=[norm_invariant],
    recovery_map=taylor_recovery,
    epsilon=0.05,
    name="vision",
)

arm = StalkNode(
    local_embedding=[1.1, 2.2, 3.3],
    invariants=[norm_invariant, energy_invariant],
    epsilon=0.06,
    name="arm",
)

glued = vision.glue_with(arm, basic_governor)
if glued:
    print(f"Glued: {glued.name}, ε={glued.epsilon}, valid={glued.is_valid()}")
```

## Governor

`simself/src/distributed/governor.py`

Predicates that gate whether two StalkNodes can glue. The "asynchronous attention" mechanism.

- `basic_governor(s1, s2)` — Bobby's original: epsilon match + shared invariants
- `norm_invariant`, `energy_invariant`, `balance_invariant` — common predicates

Future governors:
- `constitutional_governor` — check against constitutional axes
- `temporal_governor` — recent gluing history match
- `m0_m1_governor` — route through kernel gate (per `simself/src/harness/gate.py`)

## Origin

Extracted from Bobby's `MINI-SIMSELF.txt` (2026-09-08). Pattern is for **3-node robot embodiment** (vision + arm + hand) — distributed SimSelf without central controller.

Key insight from Bobby: failures are contained (no glue = no propagation), enforcing locality. An invalid node triggers local retry or isolation — no systemic crash.

## Files

- `simself/src/distributed/stalk_node.py` — node class + compression + recovery
- `simself/src/distributed/governor.py` — gluing predicates
- `simself/docs/mini-simself.md` — source markdown (preserved)

## Status

Shipped. Tested with 3-node robot example (vision + arm + hand). Gluing mechanics + invariants + recovery verified.