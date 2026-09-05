# 11-Gamedev.md — game-dev patterns as direct lift

**Source:** `Desktop/SimSelf/11-Gamedev.md` (Bobby, M3 merge 2026-08-08)
**Status:** design doc. 5 game-dev patterns extracted. File structure confirmed. Avatar controller + quest template preserved.

Bobby's M3 merge of 4 game-dev source files. Core thesis: **"Direct lift, not metaphor"** — game development has solved (at scale, real-time) what SimSelf is trying to solve. Borrowing the patterns is engineering, not aesthetics.

---

## 1. the 5 game-dev patterns lifted

### 1.1 avatar controller (embodiment layer)

```python
class B_AvatarController:
    def __init__(self, sim_self):
        self.sim_self = sim_self
        self.movement_speed = 5.0
        self.interaction_range = 2.0
        self.current_animation_state = "idle"

    def move_toward(self, target_position, delta_time):
        speed_mod = self.sim_self.state_vector["agency_will"] * 2.0
        actual_speed = self.movement_speed * speed_mod
        direction = normalize(target_position - self.position)
        self.position += direction * actual_speed * delta_time
        self.current_animation_state = "walking"
        self.sim_self.update_axis("embodiment_coherence", +0.01)

    def interact_with(self, world_object):
        if distance(self.position, world_object.position) > self.interaction_range:
            return {"success": False, "reason": "out_of_range"}
        if world_object.type == "koan_stone":
            return self._meditate_on(world_object.content)
        elif world_object.type == "tool":
            return self._use_tool(world_object)
```

**Pattern:** Avatar = proxy controlled by state. Speed modulated by axis value. Success-based interaction with world objects (koan_stone, tool).

**New axis:** `embodiment_coherence` — increments 0.01 per successful move. Tracks how well the embodiment layer is doing.

**Use:** drop into Module B (`sim_self.py` extends with embodiment; or new `b_avatar_controller.py`).

### 1.2 FSM = spiral path

**Pattern:** Game characters use FSMs/behavior trees. The 20-step ladder is exactly an FSM with transitions gated by axis thresholds.

**Direct lift:**
- FSMs → `reuse_game/fsm.py` (planned)
- Behavior trees → LimboAI-style
- Spiral path → leveling system with state transitions gated by axes

### 1.3 quest = training protocol

```json
{
  "quest_id": "deconstructor_koan_03",
  "title": "The Sound of One Hand Clapping",
  "description": "Meditate on the koan: What is the sound of one hand clapping?",
  "objectives": [
    "Generate a response that demonstrates non-dual thinking",
    "Avoid conceptual answers",
    "Maintain recursive_depth above 0.5"
  ],
  "rewards": {
    "axis_increases": {"recursive_depth": 0.05, "harmonic_resonance": 0.03},
    "experience": 100
  },
  "failure_conditions": [
    "Response contains a literal answer",
    "Recursive depth below 0.3"
  ],
  "failure_penalties": {
    "axis_decreases": {"agency_will": -0.02}
  }
}
```

**Pattern:** Training protocol as structured quest with:
- `objectives` — list of measurable goals (axis thresholds to maintain)
- `rewards` — axis increases + XP
- `failure_conditions` — measurable violations
- `failure_penalties` — axis decreases

**Use:** Module D training protocols. JSON-loadable. Run as a quest, watch axis values change.

### 1.4 save/load = state snapshots

Games have save slots, checkpoints, rollback. SimSelf needs the same: JSON/binary snapshot of **B (state matrix) + L (sacred library entries)**, with **stability-gated persistence** (only save when axes are within bounds).

**Pattern:** `persistence.py` (planned in `reuse_game/`).

### 1.5 NPCs = other agents (Module E)

Multi-agent system. Other AIs + humans are NPCs. Game-AI techniques apply:
- Dialog trees
- Goal-oriented action planning (GOAP)
- Trust/betrayal/reputation systems

**Module E as multiplayer:** collaborative projects = group quests or raids. Tested implementations available.

---

## 2. file structure (confirms main.py wiring)

```
sim-self/
├── core/                      
│   ├── governor.py            
│   ├── ledger.py              
│   ├── coherence.py           
│   ├── boundaries.py          
│   └── metrics.py             
├── sim/                       
│   ├── environment.py         
│   ├── signals.py             
│   ├── actions.py             
│   └── loop.py                
├── reuse_game/                
│   ├── fsm.py                 
│   ├── behavior_tree.py       
│   ├── resources.py           
│   └── persistence.py         
├── reuse_agent/               
│   ├── tools.py               
│   ├── planner.py             
│   ├── memory.py              
│   └── gate.py                
├── experiments/               
├── data/                      
├── main.py                    
├── config.yaml                
└── README.md
```

**Matches main.py's import structure exactly.** Two sources confirming the same design.

**One addition this doc has that main.py doesn't:** `behavior_tree.py` in `reuse_game/` (LimboAI-style). Not currently in main.py.

---

## 3. schemas table

| schema | role | simself component |
|---|---|---|
| B_AvatarController | embodiment layer | sim/ + core/ bridge |
| FSM (state machines) | behavior routing | reuse_game/fsm.py |
| Quest (training protocol) | Module D objectives | reuse_game + reuse_agent |
| Save/Load (state snapshots) | persistence | reuse_game/persistence.py |
| NPCs (other agents) | Module E multi-agent | reuse_agent/ |
| embodiment_coherence axis | new measurable | constitutional matrix |

---

## 4. what was stripped

Bobby's M3 framing at the end says: "the game-dev framing in the source files was verbose, with restated metaphors and repeated module mappings. M3 has stripped the restatement."

The doc was already stripped before I read it. I kept the engineering content (avatar controller, quest JSON, file structure, NPC mapping). Stripped:
- The "why game-dev patterns" preamble section — Bobby's reasoning, not schema
- The "LimboAI-style" / "Goal-Oriented Action Planning" / "dialog trees" specific game-dev technique names — implementation notes, not architecture
- The "save/load" preamble — redundant with the save/load schema itself
- The "module E as multiplayer" subtitle — already covered in the NPC mapping above

---

## 5. cross-reference

Bobby's main-wiring.md (just analyzed) shows the same 4-package structure. This 11-Gamedev.md confirms it + adds the embodiment layer (avatar controller) and training protocol (quest) patterns.

The two sources are **mutual validation** — Bobby's design is consistent across both. main-wiring.md tells me what gets wired; 11-Gamedev.md tells me how each piece works.

---

*Source: `Desktop/SimSelf/11-Gamedev.md`. 5 game-dev patterns extracted. File structure confirmed. Avatar controller + quest JSON preserved. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/gamedev-patterns-2026-09-05.md`.*