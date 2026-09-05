# main.py — SimSelf wiring diagram (composition root)

**Source:** `Desktop/SimSelf/main.py` (Bobby, agent wiring entry point)
**Status:** design doc extracted. The `.py` file imports from non-existent modules — not pushed as runnable code. Schema: composition-root pattern + intended module structure.

Bobby's `main.py` is **not runnable code** — it imports from submodules that don't exist locally yet:
- `core.swedenborgian_matrix`, `core.coherence`, `core.boundaries`, `core.metrics`, `core.ledger`
- `sim.environment`, `sim.signals`, `sim.actions`, `sim.loop`
- `reuse_game.fsm`, `reuse_game.resources`, `reuse_game.persistence`
- `reuse_agent.tools`, `reuse_agent.planner`, `reuse_agent.memory`, `reuse_agent.gate`

None of these exist as files in `Desktop/SimSelf/`. The `main.py` is a **wiring diagram** — Bobby's blueprint for assembling SimSelf from modules. Documenting the intended structure.

---

## 1. the composition root pattern

```python
class SimSelf:
    def __init__(self):
        # Core modules (axiomatic state)
        self.matrix = SwedenborgianMatrix()
        self.ledger = Ledger()
        self.coherence = coherence_calc
        self.boundaries = boundaries
        self.metrics = metrics
        
        # Environment
        self.environment = create_simple_env()
        
        # Control
        self.loop = MainLoop(self.environment, self.boundaries, self.matrix)
        
        # Game systems (resource tracking, persistence)
        self.fsm = create_behavior_fsm()
        self.resources = resources
        self.persistence = SoulFile()
        
        # Agent systems (planning, memory, gating)
        self.tools = tools
        self.planner = Planner()
        self.memory = working_memory
        self.episodic = episodic_buffer
        self.gate = Gate(self.boundaries)
        
        # Checkpointing
        self.checkpoint = CheckpointManager(self.persistence, interval=100)
```

**Schema:** `SimSelf.__init__` is a **composition root** — it instantiates all subcomponents and wires them together. Classic dependency-injection pattern.

**14 components wired:**
- 5 core modules (matrix, ledger, coherence, boundaries, metrics)
- 1 environment + 1 control loop
- 3 game systems (fsm, resources, persistence)
- 5 agent systems (tools, planner, memory, episodic, gate)
- 1 checkpoint manager

The `MainLoop` constructor takes 3 dependencies: `(environment, boundaries, matrix)`. The `Gate` takes `boundaries`. The `CheckpointManager` takes `(persistence, interval=100)`. **Explicit dependency passing** — no hidden globals.

---

## 2. intended module structure

Bobby's blueprint points to 4 packages:

### core/ — axiomatic state

| module | role | exists? |
|---|---|---|
| `swedenborgian_matrix.py` | 20-axis matrix | ❌ |
| `coherence.py` | coherence calculation | ❌ |
| `boundaries.py` | boundary checks | ❌ (have sovereign_self.py) |
| `metrics.py` | metrics tracker | ❌ (have metrics.py at top-level) |
| `ledger.py` | append-only ledger | ❌ (have ledger.py at top-level) |

### sim/ — environment + control

| module | role | exists? |
|---|---|---|
| `environment.py` | world model | ❌ (have bridge.py) |
| `signals.py` | signal pool | ❌ |
| `actions.py` | action definitions | ✓ (actions.py at top-level) |
| `loop.py` | MainLoop | ✓ (loop.py at top-level) |

### reuse_game/ — game systems (resource tracking + persistence)

| module | role | exists? |
|---|---|---|
| `fsm.py` | behavior finite state machine | ❌ |
| `resources.py` | resource pools | ❌ |
| `persistence.py` | SoulFile + CheckpointManager | ❌ |

### reuse_agent/ — agent systems (planning + memory)

| module | role | exists? |
|---|---|---|
| `tools.py` | tool registry | ❌ |
| `planner.py` | Planner | ✓ (executive_planner.py at top-level) |
| `memory.py` | working_memory + episodic_buffer | ✓ (harness/ dir has memory code) |
| `gate.py` | Gate | ❌ |

**Status:** 5 of 17 intended modules exist as top-level files. The rest need to be created or moved into package structure.

---

## 3. run pattern

```python
def run(self, n_cycles: int):
    """Run agent for n cycles."""
    for i in range(n_cycles):
        result = self.loop.cycle()
        self.checkpoint.maybe_checkpoint({"cycle": i, "matrix": self.matrix.get_state()})
        if i % 10 == 0:
            print(f"Cycle {i}: {result.decision.type.value}")
    return self

def main():
    agent = SimSelf()
    agent.run(100)
    agent.save("final")
```

**Three phases:**
1. **Wire** — instantiate all subcomponents
2. **Run** — MainLoop cycles N times with periodic logging every 10 cycles
3. **Save** — persist state to "final" checkpoint

**Default: 100 cycles.** Checkpoint interval: 100 cycles (saves once at end).

---

## 4. what this tells us about Bobby's design

**Big finding:** Bobby's vision for SimSelf is a **14-component agent** with:
- 5 axiomatic cores (matrix, ledger, coherence, boundaries, metrics)
- 1 world model
- 1 main control loop
- 3 game mechanics (FSM, resources, persistence)
- 5 agent capabilities (tools, planner, memory, episodic, gate)

**Compared to current simself_merged_v2.py:** v2 has all of these IN ONE FILE. main.py shows Bobby's **target decomposition** — each module separate, wired at composition time.

**Action plan:**
1. Reorganize simself/src/ into the package structure (core/, sim/, reuse_game/, reuse_agent/)
2. Move existing files into appropriate packages
3. Create missing modules (swedenborgian_matrix, gate, fsm, etc.)
4. Make main.py actually runnable

Not done this session — documenting the target.

---

## 5. schemas table

| schema | role | simself component |
|---|---|---|
| SimSelf composition root | DI container | wires 14 components |
| core/ package | axiomatic state | 5 modules |
| sim/ package | environment + control | 4 modules |
| reuse_game/ package | game mechanics | 3 modules |
| reuse_agent/ package | agent capabilities | 5 modules |
| run(n) + save(name) | lifecycle | 100-cycle default |

---

## 6. what was stripped

- The `from X import Y` lines for non-existent modules — kept as documentation of intended structure
- The `if __name__ == "__main__": main()` — kept as standard Python entry point
- Nothing else — the 96-line file is small enough to capture in full

---

*Source: `Desktop/SimSelf/main.py`. Design doc only — `.py` not pushed (imports fail). 14-component composition-root schema documented. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/main-wiring-2026-09-05.md`.*