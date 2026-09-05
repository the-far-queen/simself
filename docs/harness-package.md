# harness/ — agent patterns (gate, memory, persistence, planner, tools)

**Source:** `Desktop/SimSelf/harness/` (Bobby, agent + avatar patterns)
**Status:** 6-module package pushed to `simself/src/harness/`. Gate pattern is the canonical M0-M1 tool-use architecture.

Bobby's `harness/` subpackage — patterns borrowed from game dev + AI agent frameworks, restructured for the constitutional core. 6 focused modules totaling 780 lines. **The Gate is the canonical implementation of M0-M1 governance for external tool use.**

---

## 1. package structure

| module | lines | role |
|---|---|---|
| `__init__.py` | 18 | package header |
| `gate.py` | 211 | external tool calls through Governor |
| `persistence.py` | 166 | soul-file JSON snapshots |
| `memory.py` | 111 | bounded vector memory + cosine retrieval |
| `resources.py` | 108 | stamina/cognitive-load budget |
| `planner.py` | 83 | goal decomposition |
| `tools.py` | 83 | MCP-style tool registry |
| **total** | **780** | |

---

## 2. KEY: Gate — the canonical M0-M1 architecture

```python
class Gate:
    def __init__(self, governor, coherence_threshold=0.4):
        self.governor = governor
        self.coherence_threshold = coherence_threshold
        self.history = []
    
    def request_tool_use(self, tool, coherence_score, **kwargs):
        # 0. Hard coherence pre-check
        if coherence_score < self.coherence_threshold:
            return None  # refused before governor sees
        
        # 1. Ask Governor for decision
        raw_decision = self.governor.decide(f"USE_TOOL:{tool.__name__}", coherence_score)
        decision = self._normalize_decision(raw_decision)
        
        # 2. Apply action cost *before* execution
        self.governor.apply_action_cost(raw_decision)
        
        # 3. If REFUSE or DEFER, stop
        if decision in (DECISION_REFUSE, DECISION_DEFER):
            return None
        
        # 4. Execute only on ALLOW
        return tool(**kwargs)
```

**4-step pipeline:** coherence pre-check → governor ask → cost application → execute on ALLOW.

**The crucial insight:** apply_action_cost happens BEFORE execution. **Even deciding has cognitive cost.** This is correct: choosing (or refusing) consumes agency budget.

### 2.1 decision normalization (decoupling)

```python
def _normalize_decision(self, raw) -> str:
    if isinstance(raw, str):
        return raw.upper()
    if hasattr(raw, "allow"):        # Verdict-like (sim_self_core)
        return DECISION_ALLOW if raw.allow else DECISION_REFUSE
    if hasattr(raw, "name"):         # enum
        return str(raw.name).upper()
    return DECISION_REFUSE          # conservative fallback
```

**Schema:** The Gate accepts 3 shapes of decision (string, Verdict-like, enum) and normalizes. This **decouples the Gate from any specific module's enum design**.

**Duck-typed governor:** anything with `.decide(action, coherence) → decision` + `.apply_action_cost(decision)` works. Works with `sim_self_core.Verdict` OR `sovereign_self.Verdict`. Loose coupling.

### 2.2 the 3-decision set

```python
DECISION_REFUSE = "REFUSE"
DECISION_ALLOW = "ALLOW"
DECISION_DEFER = "DEFER"
```

Same 3 as selfcore.py (ACCEPT/SOFTEN/REFUSE translated to allow/soften/refuse). No `CONDITIONAL` here — that was sovereign_self's 4th decision. **Three-decision baseline is the simpler, more common pattern.**

---

## 3. VectorMemory (harness/memory.py)

```python
class VectorMemory:
    def __init__(self, max_size=100, vector_dim=128):
        self.memory: deque[MemoryEntry] = deque(maxlen=max_size)
    
    def add_vector(self, vector, metadata=None):
        self.memory.append(MemoryEntry(vector, time.time(), metadata))
    
    def query_similar(self, query_vector, top_k=5):
        # compute cosine similarity for all entries, sort, return top-k
```

**Pattern:** Bounded FIFO (max 100 by default), cosine similarity retrieval. Returns `(vector, similarity_score, metadata)` tuples.

**Compare to constitutional/memory.py (RelationalMemory):**
- VectorMemory: flat vector storage, cosine retrieval
- RelationalMemory: support/contradiction/temporal graph

**Two memory patterns.** Bobby's parallel implementations. The harness/ VectorMemory is the "short-term working memory" while constitutional/ RelationalMemory is the "long-term relational graph."

---

## 4. PersistenceManager (JSON snapshots)

```python
class PersistenceManager:
    def __init__(self, snapshot_dir="data/snapshots"):
        self.snapshot_dir = snapshot_dir
        os.makedirs(snapshot_dir, exist_ok=True)
    
    def save_agent_state(self, agent, filename="latest_snapshot.json"):
        agent_state = {
            "step_count": agent.step_count,
            "coherence": agent.coherence,
            "governor_state": agent.governor.get_state_summary(),
            "resources_state": agent.resources.get_status(),
            "ledger_db_path": agent.ledger.db_path,
        }
        json.dump(agent_state, f, indent=4)
```

**JSON snapshots** — human-readable, no compression. Trade-off: JSON is readable but bigger than zlib+pickle (constitutional/SoulPersistence).

**Compare to constitutional/soul_persistence:**
- harness/PersistenceManager: JSON, readable
- constitutional/SoulPersistence: zlib+pickle, compressed

Same concept (state snapshots), different formats. Pick one per use case.

---

## 5. Resources (stamina budget)

```python
class Resources:
    def __init__(self, state_vector):
        self._state_vector = state_vector
        self.max_stamina = state_vector.resource_pools['agency_budget'].get('max', 100.0)
        self.max_cognitive_load = state_vector.resource_pools['cognitive_friction'].get('max', 1.0) * 100
    
    def consume_stamina(self, amount):
        current = self._state_vector.resource_pools['agency_budget']['current']
        if current >= amount:
            self._state_vector.resource_pools['agency_budget']['current'] = max(0.0, current - amount)
            return True
        return False
    
    def regenerate_stamina(self, amount):
        current = self._state_vector.resource_pools['agency_budget']['current']
        self._state_vector.resource_pools['agency_budget']['current'] = min(self.max_stamina, current + amount)
```

**Pattern:** Direct mutation of `state_vector.resource_pools`. Returns success bool from `consume_stamina`. Bounded regeneration (caps at max).

**Coupling:** requires StateVector with `resource_pools` dict containing `agency_budget` and `cognitive_friction` entries. Same dependency as `resilient_self_model.py`.

---

## 6. Planner (goal decomposition)

```python
@dataclass
class Goal:
    description: str
    subgoals: List['Goal']
    completed: bool = False
    
    def is_leaf(self):
        return len(self.subgoals) == 0


class Planner:
    def __init__(self):
        self.current_goal: Optional[Goal] = None
        self.goal_stack: List[Goal] = []
    
    def set_goal(self, description):
        self.current_goal = Goal(description, [])
        self.goal_stack = [self.current_goal]
    
    def decompose(self, goal, decomposition_fn):
        subgoals = decomposition_fn(goal.description)
        goal.subgoals = [Goal(sg, []) for sg in subgoals]
        return goal
    
    def next_action(self) -> Optional[str]:
        # pop from stack, return next leaf goal's description
```

**Pattern:** Recursive goal decomposition with stack-based traversal. Each goal is either a leaf (action) or has subgoals.

**`decomposition_fn`** — a function that takes a description and returns a list of subgoal descriptions. Caller-supplied. Pluggable.

---

## 7. Tool + ToolRegistry

```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict
    handler: Callable
    
    def execute(self, **kwargs):
        return self.handler(**kwargs)


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        self.tools[tool.name] = tool
```

**MCP-style pattern:** Each Tool is name + description + parameters + handler. ToolRegistry maps name → Tool. Standard agent-tool architecture.

---

## 8. parallel implementations — open question

Bobby now has TWO packages with overlapping concerns:

| concern | constitutional/ | harness/ |
|---|---|---|
| memory | RelationalMemory (support/contradiction/temporal graph) | VectorMemory (cosine, FIFO) |
| persistence | SoulPersistence (zlib+pickle, zlib compressed) | PersistenceManager (JSON, readable) |
| resources | | Resources (stamina budget) |
| planning | | Planner (goal decomposition) |
| tools | | Tool + ToolRegistry |

**Recommendation:** consolidate. Pick one pattern per concern. The harness/ patterns (JSON, vector, MCP-style) are more standard and easier to debug. constitutional/ patterns (RelationalMemory, zlib+pickle) are more Bobby-flavored.

**For simself work:** canonical = harness/ patterns for external interfaces (gate, tools, persistence), constitutional/ for internal state (memory graphs, axes).

---

## 9. what was stripped

- `ledger.json` and `soul_file.json` — example data files in the directory. Not pushed (per-file commit noise).
- `__main__` blocks — preserved in each module as working demos.

---

*Source: `Desktop/SimSelf/harness/` → `simself/src/harness/`. 6 modules pushed. Gate is canonical M0-M1 architecture. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/harness-package-2026-09-05.md`.*