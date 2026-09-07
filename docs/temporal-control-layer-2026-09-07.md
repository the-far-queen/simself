# Temporal Control Layer (TCL)

**Source:** `Desktop/SimSelf/temporal layer.txt` (1,254 lines, 45 KB)
**Extracted:** 2026-09-07
**Module scope:** signal-driven temporal gating for the SimSelf/FieldCore system. Decides WHEN expensive modules update, not WHAT they do.

Bobby's framing (per §32): this is a **stub for the coding novel sys** — the actual codingOperator consumes repos, extracts code, ingests in small bites, gets better at coding, eventually produces ASI via recursive self-improvement.

---

## What this is

The TCL is the "when" system. It gates updates to expensive modules (reasoning, memory consolidation, self-model updates, boundary checks) based on **signal quality, not time.**

**Bobby's load-bearing insight (per Bobby's clarification):**
> "remember mult ai build and as it gets better it scans better understands what it needs better its asi"

The codingOperator (when fully built) is a **recursive self-improvement loop** that uses the TCL to decide when to do expensive updates. The loop closes when the meta-learning produces better scanners.

---

## The TCL architecture

```
SignalMetrics:
  ├── entropy (state entropy)
  ├── novelty (state change since previous)
  ├── gradient_variance (training signal)
  ├── task_boundary (boolean: task complete or level changed)
  ├── sim_state_change (boolean: world state changed)
  ├── agent_uncertainty (variance in action predictions)
  ├── temporal_coherence (stability of recent signals)
  └── compute_budget_remaining (fraction of compute left)

UpdateType (enum):
  ├── CONSOLIDATION (memory write)
  ├── REASONING (expensive inference)
  ├── SELF_MODEL (B module update)
  ├── BOUNDARY_CHECK (D module defense)
  ├── ACTION (cheap cached policy)
  └── NO_UPDATE (skip expensive ops)
```

### TemporalController

```python
class TemporalController:
    def __init__(self, mode: str = "heuristic", update_threshold: float = 0.7):
        self.mode = mode  # "heuristic", "rl", "supervised"
        self.update_threshold = update_threshold
        self.step_count = 0
        self.signal_history: List[SignalMetrics] = []
        self.update_decisions: List[Dict] = []
        self.performance_history: List[Dict] = []

    def evaluate_signals(self, current_state, previous_state, environment, agent_state) -> SignalMetrics:
        # calculate 8 signal metrics from available data
        ...

    def should_trigger(self, signal_metrics, requested_update) -> Tuple[bool, float]:
        # main decision function: trigger this update type?
        # returns (trigger, confidence)
        ...

    def _heuristic_decision(self, metrics, update_type) -> Tuple[bool, float]:
        # weighted combination of signal metrics
        # task_boundary has weight 0.8 (strong signal)
        # temporal_coherence has weight -0.2 (negative = don't update if coherent)
        ...
```

### Heuristic weights (v0, learnable in v1+)

```python
weights = {
    'entropy': 0.2,
    'novelty': 0.3,
    'gradient_variance': 0.15,
    'task_boundary': 0.8,        # Strong signal — task complete = trigger update
    'sim_state_change': 0.4,
    'agent_uncertainty': 0.25,
    'temporal_coherence': -0.2,  # Negative: don't update if signals are stable
    'compute_budget': 0.1
}
```

### Policy modes (extensible)

- `heuristic` — weighted combination of signal metrics (v0)
- `rl` — reinforcement-learned policy (v1+)
- `supervised` — supervised-learned policy (v1+)

The mode determines which `_decision` method runs. Hooks in place to swap policies.

---

## The integration pattern

The TCL integrates with the main loop non-invasively:

```python
# main loop
while running:
    state = environment.step()
    signals = tcl.evaluate_signals(state, prev_state, env, agent)
    
    # Cheap actions always trigger
    if tcl.should_trigger(signals, UpdateType.ACTION):
        action = agent.act(state)
    
    # Expensive updates gated by signal quality
    if tcl.should_trigger(signals, UpdateType.REASONING):
        result = agent.reason(action)  # expensive LLM call
    
    if tcl.should_trigger(signals, UpdateType.CONSOLIDATION):
        memory.write(state, result)  # memory consolidation
    
    if tcl.should_trigger(signals, UpdateType.SELF_MODEL):
        agent.update_self_model()  # the B module update
    
    if tcl.should_trigger(signals, UpdateType.BOUNDARY_CHECK):
        governor.check(agent, action)  # the D module defense
```

**the integration is non-invasive** — the modules don't know about TCL. They just expose update triggers. TCL decides which to fire.

---

## Why this matters

1. **cheap vs expensive gate.** Most AI systems waste compute on routine updates. TCL only fires expensive updates when signals warrant it.

2. **cooldown prevents thrashing.** The TCL won't trigger the same update type twice in rapid succession (cooldown period).

3. **negative temporal_coherence weight.** When signals are stable (high coherence), don't update. When signals are noisy (low coherence), update.

4. **policy learnable.** v0 is heuristic weights; v1+ can swap to RL or supervised policy with the same interface.

5. **fits the recursive self-improvement loop.** When the codingOperator improves its scanning, the TCL's signals change. The policy learns from the change. The loop closes.

---

## Maps to existing project files

| concept | existing file |
|---|---|
| Policy modes (heuristic/rl/supervised) | `simself/docs/snr-validation-2026-09-07.md` (the SNR method is a heuristic policy for curation) |
| signal_metrics → Trigger | `kernel-architecture-2026-09-07.md` (the Governor M0 is the 1-bit gate; TCL is the signal-driven layer above it) |
| Cooldown periods | `emergence-blueprint-2026-09-07.md` Pillar 1 (ResilientAxes — hysteresis on sacred tier) |
| Performance history | `state-report-schema-2026-09-07.md` (event log with axis_impact) |
| task_boundary signal | godot sim integration (per §30) — task boundary = level changed, goal complete |
| codingOperator ingestion | §32 Bobby's clarification: scans repos + extracts + ingests daily/hourly |

---

## What this resolves in the missing-pieces project

- **#11 Mini-LLM runtime** — TCL is the runtime governor for when Mini-LLM is invoked. Cheap paths don't pay the LLM cost.
- **#3 Sacred-tier runtime check** — BOUNDARY_CHECK update type runs the ConstitutionalGuard. Sacred axes are bit-1 to deny.
- **NEW: WHEN to do expensive ops** — the load-bearing question this layer answers.
- **NEW: Recursive self-improvement loop safety** — cooldown + signal-driven gates prevent runaway self-modification.

---

## Open architecture questions resolved

45. **recursive self-improvement loop architecture** — has a concrete pattern now: signal-driven gating + cooldown + heuristic policy + learnable upgrade path
46. **WHEN to do expensive ops** — TCL = the answer
47. **Cooldown pattern** — generic, reusable across update types

---

## What I should NOT do

- Don't try to build the full RL policy now. v0 heuristic is sufficient.
- Don't try to integrate godot sim signals yet. Stub the task_boundary signal first.
- Don't add complex features to TCL before testing the v0 heuristic.
- Don't skip the cooldown logic — it's the safety mechanism for runaway self-modification.

---

## Implementation priorities (when Bobby says go)

1. **Copy temporal_control.py to simself/src/** — the v0 implementation
2. **Wire to coding_operator_object.py** as the temporal gating layer
3. **Add godot sim integration** for task_boundary + sim_state_change signals
4. **Add metrics emission** — log every decision for later RL training
5. **v1 RL policy** — only after v0 heuristic is tested in production

---

*Mirror: `~/AppData/Local/hermes/vault/10-minimax/20-mirrors/simself/docs/temporal-control-layer-2026-09-07.md`*
*Original: `Desktop/SimSelf/temporal layer.txt` — preserved in `30-originals/`*
