---
name: fieldcore-tiny-core
description: >-
  Use when the user wants the kernel math — 16-D vectors, two inequalities, projected gradient
  step, M0 governor, BitNet ternary ops. Triggers: "kernel", "tiniest core", "M0", "gradient
  step", "16-d", "two inequalities", "F(ψ)=½‖ψ-ψ₀‖²".
---

# FieldCore Tiniest Core — the kernel math

The kernel is the **smallest possible substrate** that holds the SimSelf's working math. It's in Rust and Python (twin implementations).

## Three pieces

1. **16-D state vector** — the working state ψ lives in a 16-dim space.
2. **Two inequalities** — `drift ≤ drift_max` and `‖grad F‖ ≤ grad_max`.
3. **Projected gradient step** — `ψ' = ψ - α · ∇F(ψ)`, projected onto the feasible set defined by the inequalities.

The objective is `F(ψ) = ½ ‖ψ - ψ₀‖²` (convergence toward ground).

## Files

| Path | What |
|---|---|
| `src/tiniest-core/tiniest_core.py` | Python kernel — 16-D state, two inequalities, projected gradient step. 5 local asserts. |
| `src/tiniest-core/tiniest_core.rs` | Rust twin. Same predicates. |
| `src/gradient_flow_kernel.py` | CLI demo of the projected gradient step on F. |
| `src/convergence_demo.py` | Bobby's pedagogical steel-ball-on-concave-surface exhibit. |

## Surface

```python
from fieldcore.src.tiniest_core.tiniest_core import (
    State, M0_Governor, step, feasible
)

psi = State.random(seed=42)
psi0 = State.zero()
for _ in range(1000):
    if M0_Governor.allows(psi, psi0):
        psi = step(psi, psi0, alpha=0.01)
    else:
        break
```

## Why this is "control systems architecture absent at the root"

Modern LLMs lack:
- feedback loops (state estimation from output)
- state estimation (Kalman-filter-like signal separation)
- stability (hysteresis on sacred axes)
- gating (1-bit allow/refuse with rollback)

This kernel adds all four:
- feedback = M1 Controller qualifies post-hoc
- state estimation = Mini-LLM runtime + PSB lineage
- stability = ResilientAxes (hysteresis on sacred tier)
- gating = M0 Governor 1-bit

The whole thing is a classical control system built around a stochastic core. The stochastic core (LLM) is one input. The control system is the load-bearing structure.

## See also

- `fieldcore-stalk` — the geometry
- `fieldcore-bitnet` — ternary ops
- `simself-identity` — uses the kernel