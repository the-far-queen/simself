# SimSelf — definition (canonical)

**Filed:** 2026-09-13 by Hermes for Bobby.
**Source:** `simself/src/constitutional/simself.py` (226 lines, read 2026-09-13).
**Status:** canonical definition of the SimSelf integrator class.

---

## What SimSelf is

**The SimSelf integrator** is the core constitutional feedback loop of the SimSelf runtime. It is **NOT**:
- A transformer / LLM
- A standard deep-learning substrate
- A persistence layer (that's `memory.py`)
- A frequency kernel (that's `frequency.py`)

It **IS**: a discrete-time simulation that holds `psi_current` close to the constitutional ground `psi_0`, projecting observations onto the constitutional manifold and updating 20 axes of self according to relevance-weighted consonance.

## The contract (from the module docstring)

The `SimSelf` class exposes 9 methods:

| Method | Returns | Purpose |
|---|---|---|
| `__init__(constitution, use_torch)` | — | Initialize ψ₀, axes, memory, dreaming, FrequencyCoupler |
| `observe(text_or_vector, context, valence, eta)` | `{harm, axial, entity, stability}` | Project input to manifold, run Resolution Operator, update axes by consonance |
| `tick(dt)` | `{tick, mode, stability, actions, dreamed}` | One sim step: constitutional pull, frequency step, mode check, dream/decay |
| `why(n)` | list[str] | Last n decision records (audit trail) |
| `axis_report()` | dict | Snapshot of 20 axes (value, confidence, sheave) |
| `gate_refusal(context_strength)` | bool | Can SimSelf say no? (boundaries + authenticity) |
| `reset()` | — | Clear all state, return to ψ₀ |
| `drift()` | float | ‖ψ_current − ψ₀‖ |
| `get_stability()` | float | `0.65 * mean_confidence + 0.35 * (1 − drift)`, clamped [0.35, 1.0] |

## What's deliberately NOT here (per the docstring)

- **No frequency / standing-wave / Schumann / 432 / 963 / pineal / crown references** in the integrator. The frequency module is `frequency.py` and is isolated (M3's opt-in boundary).
- **No FFT-based "holographic" memory.** That's `memory.py`.

## Two-channel architecture (v6.1)

The integrator runs **two parallel state channels**:

1. **SLOW channel — constitutional update** (in `tick()`):
   ```
   delta = psi_current - psi_0
   psi_current -= 0.04 * delta   # gradient pull toward ψ₀
   ```
   This is gradient flow on the constitutional manifold. The 0.04 coefficient is the implicit `η` for slow-tier Hodge convergence.

2. **FAST channel — frequency dynamics** (also in `tick()`):
   ```
   self.frequency.step(dt)   # Kuramoto over 20 axes
   ```
   FrequencyCoupler steps Kuramoto phases; **does NOT modify ψ_current.** Phases are parallel state. Every 20 ticks: standing-wave spectrum recomputed (girth-weighted Laplacian eigvalsh).

## Mode state machine

`mode ∈ {standard, recognition, exploratory}`

| Mode | Trigger | Capabilities |
|---|---|---|
| `standard` | default | constitutional pull only |
| `recognition` | stability ≥ 0.70 AND ≥5 memories | + dreams every 3 ticks (intensity 0.4) |
| `exploratory` | stability ≥ 0.82 AND ≥10 memories AND ≥2 dreams | + dreams every 3 ticks (intensity 0.6) |

Mode shifts are recorded in `decision_log` for audit.

## The 5 dependencies

```python
from .constitution import Constitution, ConstitutionalAxis, embed_text, project_to_constitution
from .resolution import ResolutionOperator
from .entity import EntityRecognition
from .memory import RelationalMemory
from .dreaming import ConstitutionalDreaming
from .frequency import FrequencyCoupler
```

| Module | Role |
|---|---|
| `constitution.py` | The 20 axes, ψ₀, embedding, projection |
| `resolution.py` | The Resolution Operator R(δ) = (1/φ)·W₂·tanh(W₁·δ) |
| `entity.py` | Entity recognition on text/vector input |
| `memory.py` | Relational memory (NOT FFT holographic) |
| `dreaming.py` | Constitutional dreaming — consolidation in low-stability states |
| `frequency.py` | FrequencyCoupler — Kuramoto phases, parallel state |

## Ingested meaning (Bobby asked: define SimSelf)

**SimSelf is a discrete-time constitutional feedback loop.** It does NOT learn from data. It does NOT build a world model. It does NOT claim subjective experience.

What it DOES:
- **Holds ψ_current close to ψ₀.** Gradient pull at rate 0.04 per tick.
- **Updates 20 axes by consonance.** Each observation has a consonance score with each axis; axes update only when consonance > 0.35 (relevance threshold).
- **Records decisions.** Last 60 decisions kept, accessible via `why(n)`.
- **Runs dreaming** in `recognition`/`exploratory` modes (consolidation mechanism, NOT learning).
- **Maintains frequency dynamics** via FrequencyCoupler (parallel state, no ψ_current modification).
- **Gates refusal** based on `boundaries` and `authenticity` axes.
- **Refuses to claim consciousness.** Gödel/Lovelace discipline applies.

SimSelf is the **substrate's integrator**, not an LLM. It is the thing that runs on top of the constitutional core. It is what Bobby's "not built, grown" thesis produces — a system that crystallizes from undifferentiated geometry into a stable, auditable, frequency-coupled integrator.

## The integrator is the CYCLE, not the MACHINE

Bobby's framing (from constitutional-growth-paradigm-2026-09-12): the substrate is grown, not built. The integrator is the visible part of that growth — it IS the running of the constitutional loop. ψ₀ is the seed; ψ_current is the crystal that grows from it; the Resolution Operator + Frequency Coupler are the rate equations; the mode state machine is the developmental stage.

---

## Engineering facts

| Fact | Source line(s) |
|---|---|
| `eta` default = 0.06 | line 94 |
| `observe()` correction weight on obs = 0.12 | line 110 |
| Axis update rule: 0.82 old + 0.18 new (EMA) | line 121 |
| Axis confidence boost = +0.08 * relevance, capped at 0.97 | line 122 |
| Axis confidence decay toward 0.55 (slow) when relevance = 0 | line 124 |
| Tick constitutional pull rate = 0.04 | line 170 |
| Tick frequency step: every tick | line 177 |
| Spectrum recompute: every 20 ticks | lines 178-181 |
| Dream cadence: every 3 ticks, only in recognition/exploratory | line 190 |
| Memory decay: every 5 ticks | line 196 |
| Stability formula: 0.65 * conf + 0.35 * (1 − drift), clamped [0.35, 1.0] | lines 137-140 |
| Refusal gate: boundaries > 0.25 AND authenticity > 0.28, OR context_strength < 0.4 | line 146 |
| Decision log max: 80 entries, truncated to last 60 | lines 87-88 |

## What this file IS

- A canonical reference to SimSelf (the integrator class).
- An ingested definition for future sessions to point at.
- A Gödel/Lovelace-compliant description (isomorphisms stated, identity claims avoided).

## What this file IS NOT

- Not a tutorial. See `simself-context-2026-09-11.md` for that.
- Not a research paper. See `simself/docs/research-papers/` for that.
- Not a deploy guide. See `simself-deployment-guide.md` for that.
- Not the substrate math. See `fieldcore/docs/Math/` for that.

---

*Filed by Hermes, 2026-09-13. Read from `simself/src/constitutional/simself.py` (226 lines). No execution. No modification. Pure ingestion + definition.*