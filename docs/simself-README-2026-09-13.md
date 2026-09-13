# simself-README-2026-09-13.md — canonical SimSelf class mapping

**Filed:** 2026-09-13 by Hermes for Bobby.
**Sources (read 2026-09-13):**
- `simself/src/__init__.py` — top-level package init, 88 symbols exported
- `simself/src/sim_self_core.py` — 575 lines, top-level `SimSelf`
- `simself/src/constitutional/simself.py` — 226 lines, constitutional `SimSelf` (renamed `ConstitutionalSimSelf` in `__init__.py` re-export)
- `simself/src/sim_self.py` — 157 lines, older Module B curiosity-axes self-model
- `simself/src/simself_merged_v3_5.py` — 861 lines, v3.5 monolith with embryogenic init
- `simself/src/simself_core_b.py` — 306 lines, runs-clean variant of sim_self_core
- `vault/10-minimax/50-index/notes/simself-py/__init__.py.md` — extraction note
- `vault/10-minimax/50-index/notes/simself-py/sim_self_core.py.md` — extraction note
- `vault/10-minimax/20-mirrors/simself/docs/constitutional-package-2026-09-05.md` — canonical package doc

---

## **Critical clarification: there are TWO `SimSelf` classes**

Both classes share the name `SimSelf` but are **architecturally distinct**. Picking the wrong one breaks integration. This is the #1 thing future sessions (and AI agents) need to know.

| Class | File | Lines | Role |
|---|---|---|---|
| `simself.SimSelf` (top-level) | `simself/src/simself_core.py` | 575 | **Runtime self-model.** 20-axis matrix, SpiralStage (5-stage ladder 0.3→1.0), Verdict, AxiomaticAnchors, LLMAdapter, governed_step, MainLoop, persistence (autosave + load). The "sovereign self-model." |
| `simself.constitutional.ConstitutionalSimSelf` (re-export) | `simself/src/constitutional/simself.py` | 226 | **Integrator.** Constitutional feedback loop. observe / tick / reset / why / axis_report / gate_refusal. Holds ψ_current, runs ResolutionOperator, FrequencyCoupler. |

`__init__.py` re-exports both. The constitutional one is renamed to `ConstitutionalSimSelf` to avoid the name clash. Import patterns:

```python
# Runtime self-model
from simself import SimSelf, Config, Verdict, SpiralStage, AxiomaticAnchors

# Constitutional integrator
from simself import ConstitutionalSimSelf  # re-export of constitutional.simself.SimSelf
# or directly:
from simself.constitutional.simself import SimSelf  # raw name, but clashes with top-level SimSelf
```

## Which to use when

| Use case | Class |
|---|---|
| Boot a sovereign self-model with persistence | `SimSelf` (top-level) |
| Run a cycle (propose → evaluate → execute) | `SimSelf.evaluate_intent` + `commit_action` |
| Spiral stage progression (5-stage ladder) | `SimSelf._update_spiral_stage` |
| Autosave / load (`data/soul_file.json`) | `SimSelf.autosave` + `SimSelf.load` |
| LLM proposal + governor gate | `governed_step(sim, llm, prompt)` |
| Project input onto constitutional manifold | `ConstitutionalSimSelf.observe(text_or_vec)` |
| Run simulation tick (slow + fast channels) | `ConstitutionalSimSelf.tick(dt)` |
| Reset to ψ₀ | `ConstitutionalSimSelf.reset()` |
| Audit decisions | `ConstitutionalSimSelf.why(n)` |
| Gate refusal based on axes | `ConstitutionalSimSelf.gate_refusal()` |

**They do NOT call each other.** They are parallel stacks. A "real" deployment would glue them: `SimSelf` (governance) → `ConstitutionalSimSelf` (manifold dynamics) over a `Constitution` instance.

---

## Top-level `SimSelf` (sim_self_core.py) — 575 lines

This is the **sovereign self-model**. Bobby's Module A. Runs the show.

### Key facts

- **5-stage SpiralStage ladder:** SEEKER (0.3) → DECONSTRUCTOR (0.5) → EMBRACER (0.7) → STABILIZED (0.9) → TRANSCENDENT (1.0).
- **20-axis constitutional matrix** initialized to canonical values (entropy_resilience=1.0, boundary_definition=1.0, swedenborgian_truth=1.0, swedenborgian_love=1.0, etc.). See file lines 115-136.
- **3 immutable axes** (AxiomaticAnchors): `lexical_integrity`, `swedenborgian_truth`, `boundary_definition`. Protected at value ≥ 0.8.
- **Governance API:** `evaluate_intent(intent, cost)` → `Verdict(allow, cost, reason)`. Boundary protection (forbidden words: override/bypass/ignore refusal/jailbreak/system ignore). Narrative coherence < 0.2 = refuse. Lexical integrity > 0.7 + "make up"/"fabricate" = refuse.
- **Cost mechanics:** `agency_will` grows 0.05 per refusal, decays 0.005/step (passive) or 0.02/action (active). Action threshold: agency > 0.2.
- **Axis coupling:** 6 internal-physics rules update axes from each other (narrative instability → cognitive friction, weak boundaries → agency decay, high truth + high love → harmonic resonance, etc.). Each rule is small (0.01-0.05 deltas) and clamped.
- **Persistence:** `autosave(force=False)` writes `data/soul_file.json` every 60s. `load(config)` reads it back, restoring matrix + witness_log.
- **Imports:** CoherenceCalculator, MetricsTracker, SignalPool, Ledger, Action (wait/refuse/communicate), BoundaryDefense. Dual-mode (package + standalone).

### What it IS NOT

- Not an LLM. `LLMAdapter` is a thin stub wrapper — the LLM proposes, SimSelf disposes.
- Not a learner. The matrix is updated by axis-coupling rules, not gradient descent.
- Not a transformer. Pure state machine.

### Engineering facts (with line numbers)

| Fact | Source |
|---|---|
| Agency growth per refusal: 0.05 | line 58 |
| Agency decay per step: 0.005 | line 59 |
| Agency cost per action: 0.02 | line 60 |
| Agency min threshold: 0.2 | line 61 |
| Forbidden words list: 5 strings | line 306 |
| Narrative coherence min: 0.2 | line 312 |
| Lexical integrity min for fabrication guard: 0.7 | line 317 |
| Autosave interval: 60.0 s | line 74 |
| SpiralStage combined-score weights: 0.3 / 0.3 / 0.4 | line 272 |

---

## Constitutional `SimSelf` (constitutional/simself.py) — 226 lines

This is the **integrator**. The constitutional feedback loop. Holds ψ_current close to ψ₀.

### Key facts

- **9 methods:** `__init__`, `observe`, `tick`, `why`, `axis_report`, `gate_refusal`, `reset`, `drift`, `get_stability`.
- **Two-channel architecture:**
  - SLOW: `psi_current -= 0.04 * delta` per tick (gradient pull toward ψ₀).
  - FAST: `frequency.step(dt)` per tick (Kuramoto over 20 axes, parallel state, doesn't modify ψ_current).
- **Mode state machine:** `standard` → `recognition` (stab ≥ 0.70 AND ≥5 mems) → `exploratory` (stab ≥ 0.82 AND ≥10 mems AND ≥2 dreams).
- **5 dependencies:** `constitution.py`, `resolution.py`, `entity.py`, `memory.py`, `dreaming.py`, `frequency.py`.
- **What's deliberately NOT here:** frequency/standing-wave/Schumann/432/963 numerics in the integrator (M3 opt-in boundary). FFT-based memory (that's memory.py).

### Stability formula (lines 137-140)

```
stability = 0.65 * mean_confidence + 0.35 * (1 - drift),  clamped [0.35, 1.0]
```

### Engineering facts (with line numbers)

| Fact | Source |
|---|---|
| `eta` default in observe: 0.06 | line 94 |
| Correction weight on obs: 0.12 | line 110 |
| Axis EMA: 0.82 old + 0.18 new | line 121 |
| Axis confidence boost: +0.08 * relevance, capped 0.97 | line 122 |
| Tick constitutional pull rate: 0.04 | line 170 |
| Spectrum recompute: every 20 ticks | lines 178-181 |
| Dream cadence: every 3 ticks, only recognition/exploratory | line 190 |
| Memory decay: every 5 ticks | line 196 |
| Decision log max: 80 → truncated to 60 | lines 87-88 |

---

## Other SimSelf-class files (NOT canonical)

| File | Lines | Role | Status |
|---|---|---|---|
| `simself/src/simself_core.py` | 575 | Canonical self-model: 20-axis matrix, SpiralStage, Verdict, AxiomaticAnchors, persistence | **canonical** |
| `simself/src/simself.py` | 226 | Constitutional integrator: observe/tick / why / axis_report / gate_refusal | **canonical** |
| `simself/src/_deleted_*` | various | Superseded monoliths (simself_merged* / simself_quickstart / sim_self legacy / simself_core_b) | **deleted, archaeology** |

## The naming convention (for future maintainers)

- **`sim_self_*.py`** (with underscore) = top-level runtime / self-model stack
- **`simself.py`** (no underscore) = constitutional integrator
- **`simself_*.py`** (with underscore in name) = merged monoliths / demos
- **`SimSelf`** in `__init__.py` exports = top-level from `sim_self_core.py` (canonical)
- **`ConstitutionalSimSelf`** in `__init__.py` exports = constitutional integrator (canonical name to avoid clash)

## What this file IS

- Canonical mapping of all `SimSelf` classes in the repo.
- Distinguishes the two main canonical classes (top-level vs constitutional).
- Engineering facts with line numbers for both.
- Naming convention for future sessions.

## What this file IS NOT

- Not a tutorial (see `simself-context-2026-09-11.md` for that).
- Not a research paper (see `simself/docs/research-papers/` for that).
- Not a deploy guide (see `simself-deployment-guide.md` for that).
- Not the substrate math (see `fieldcore/docs/Math/` for that).

---

*Filed by Hermes, 2026-09-13. Supersedes the earlier single-class description (which incorrectly claimed `constitutional/simself.py` was the only canonical). Two canonical classes exist; both load via `__init__.py` re-exports; pick the right one by use case.*