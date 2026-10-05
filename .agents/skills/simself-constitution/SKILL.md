---
name: simself-constitution
description: >-
  Use when the user wants the 20-axis constitutional matrix, axis thresholds, sacred/emergent
  tiers, or the constitutional guard. Triggers: "constitution", "20 axes", "sacred",
  "resilient", "M1 axes", "M2 axes", "two-tier".
---

# SimSelf Constitution — the 20-axis matrix

The constitution is the **functional coordinates** of the SimSelf's working state ψ. It's a tuple of axis values, each with a threshold and a tier.

## Two tiers

- **Sacred** (immutable): axes enforced by `ConstitutionalGuard`. Drift past threshold = gate refusal.
- **Emergent** (learnable): axes governed by `ResilientAxes`. Drift past threshold = attempt repair.

## The 20 axes

Per `src/constitutional/constitution.py`:

- 8 constitutional (sacred): identity, ethics, capability, scope, alignment, fidelity, integrity, continuity
- 12 resilient (emergent): focus, mood, energy, coherence, clarity, momentum, tempo, density, curiosity, tolerance, presence, voice

Each axis has:
- a current value (in [-1, +1] or [0, 1] depending on type)
- a target value
- a threshold (refusal / repair cutoff)
- a cost (gradient step penalty)

## Surface

```python
from src.constitutional.constitution import Constitution, Axis
from src.constitutional.resolution import step

# default constitution
c = Constitution.defaults()

# custom
c = Constitution(
    sacred={Axis.IDENTITY: 1.0, Axis.ETHICS: 1.0, ...},
    resilient={Axis.FOCUS: 0.8, Axis.MOOD: 0.5, ...},
)

# step toward a target
new_psi = step(psi, target, constitution=c)
# returns projected ψ (within sacred tier, gradient step in resilient tier)
```

## Tuning

When you change an axis threshold:
1. Update `constitution.py`
2. Update the atlas exam (`src/constitutional/atlas_exam.py`) so the test reflects the new threshold
4. Update `docs/constitutional/axes.md` if it exists

## See also

- `simself-identity` — uses the constitution
- `simself-gate` — checks sacred tier
- `fieldcore-tiny-core` — gradient step math