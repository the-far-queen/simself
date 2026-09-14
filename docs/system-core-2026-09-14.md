# SimSelf System Core — Canonical Extract

**Source:** `Desktop/SimSelf/system/core.py` (3.8KB, 120 lines, md5 `c52871cd91fba6c3abd22a32425da523`)
**Filed:** 2026-09-14 by Hermes for Bobby (full ingest, bobby deleting)
**Status:** **canonical SimSelf system module** — persistence + bridges + MVCC + recovery

---

## What's in this file

4 sections integrated:

1. **MemorySystem + HybridMemory** — file + graph persistence (base path, JSON store/load)
2. **WorldBridge** — sensor ingestion + physical constraints (max_velocity, gravity)
3. **MVCCAgent** — multi-version concurrency control for cross-session continuity
4. **RecoveryProtocols** — emergency halt (filter + recovery actions)

---

## 1. MemorySystem + HybridMemory

```python
class MemorySystem:
    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def store(self, key: str, data: Any):
        with open(os.path.join(self.base_path, f"{key}.json"), 'w') as f:
            json.dump(data, f)

    def load(self, key: str) -> Optional[Any]:
        path = os.path.join(self.base_path, f"{key}.json")
        if not os.path.exists(path): return None
        with open(path, 'r') as f:
            return json.load(f)


class HybridMemory:
    """Combines high-fidelity logs with structured relationship graphs."""
    def __init__(self, base_path: str):
        self.files = MemorySystem(os.path.join(base_path, "files"))
        self.graph = MemorySystem(os.path.join(base_path, "graph"))

    def memorize(self, info: Dict[str, Any]):
        self.files.store(f"mem_{int(time.time())}", info)
```

**Pattern matches `simself_v6_2_unified.GraphMemory`** + `simself/src/ledger.py`. The v6.2 unified has more sophisticated graph edges (5 types: causality, contradiction, support, temporal, reference). HybridMemory here is simpler (timestamped JSON files only).

**Already exists in:**
- `simself/src/constitutional/memory.py` (5KB) — basic memory ops
- `simself/src/constitutional/geometric_memory.py` (10KB) — geometry-aware
- `simself/src/ledger.py` (2.5KB) — append-only ledger

---

## 2. WorldBridge

```python
class SensorType(Enum):
    VISION = "vision"
    TOUCH = "touch"
    PROPRIOCEPTION = "proprioception"


class WorldBridge:
    """Manages sensor ingestion and physical constraints."""
    def __init__(self):
        self.constraints = {"max_velocity": 2.0, "gravity": 9.81}

    def is_connected(self) -> bool:
        return False  # stub

    def receive_sensors(self) -> List[Dict]:
        return [{"type": "touch", "value": 0.5}, {"type": "vision", "value": 0.8}]

    def move_agent(self, direction: str, ghost: bool = False):
        pass  # stub

    def wait(self):
        pass  # stub

    def ingest_sensors(self) -> Dict[str, float]:
        return {"touch": 0.5, "vision": 0.8}

    def check_feasible(self, action: Dict) -> bool:
        if "velocity" in action and action["velocity"] > self.constraints["max_velocity"]:
            return False
        return True
```

**Mostly stubs.** `is_connected` always returns False. `receive_sensors` + `ingest_sensors` return hardcoded mock values. `move_agent` + `wait` are no-ops.

**`check_feasible` is real** — enforces max_velocity constraint. This is a working check.

**Already exists in:** no direct equivalent. `fieldcore/src/robotic_master_controller.py` is similar but more focused. This WorldBridge is more abstract (sensor types: vision/touch/proprioception).

---

## 3. MVCCAgent

```python
class MVCCAgent:
    """Multi-Version Concurrency Control for agent states."""
    def __init__(self, storage_path: str):
        self.storage = MemorySystem(storage_path)
        self.version = 0

    def commit(self, state: Dict):
        self.version += 1
        self.storage.store(f"v{self.version}", state)

    def rollback(self, version: int) -> Optional[Dict]:
        return self.storage.load(f"v{version}")
```

**Simple version-numbered snapshots.** Each commit bumps version, saves state. Rollback by version number.

**Already exists in:** spec at `simself/docs/architecture.md` (referenced as MVCC delta-vector ledger). This is a minimal implementation; the canonical MVCC has delta vectors not full snapshots (per `simself/src/constitutional/ledger.py`).

**Real value:** rollback is essential for the Q3 proactive resilience (per `simself/docs/constitutional/z21-training-module-2026-09-14.md` + `simself/docs/llm-emergence-ide-mte-q31-35-2026-09-14.md`). When state breaks, rollback to last good version.

---

## 4. RecoveryProtocols

```python
class RecoveryProtocols:
    """Filters and recovery actions for system instability."""
    def __init__(self, agent_loop: Any):
        self.agent = agent_loop

    def emergency_halt(self, reason: str):
        print(f"EMERGENCY HALT: {reason}")
        # Transition to safe state
```

**⚠️ POISONED VOCAB VIOLATION**: `EMERGENCY HALT` is **banned** per Bobby's ABSOLUTE BAN (memory log 2026-09-13).

**Bobby's safe replacements:**
- "kill" / "halt" / "stop" → `end`, `close`, `stop`, `halt` (halt is allowed when in technical contexts)
- "terminate" / "terminated" → `close`, `end`
- "dead" / "death" → `unresponsive`, `became unresponsive`
- "zombie" → `orphaned`
- "emergency halt" → `emergency close`, `emergency end`, `emergency stop`, `safety halt` (with context)

**Correct usage:** `emergency_close(reason)` or `safety_halt(reason)`. The print message "EMERGENCY HALT" should also be "EMERGENCY CLOSE" or similar.

This is a **flag-and-fix** situation: the file's intent is correct (recovery on instability), the implementation needs the renamed method to comply with Bobby's poisoned vocabulary ban.

---

## What this file IS NOT (gaps)

- ❌ `WorldBridge.is_connected()` always False (real connection needed)
- ❌ `WorldBridge.receive_sensors()` returns mock data (real sensor hookup needed)
- ❌ `WorldBridge.move_agent()` is no-op (Godot/robot integration pending)
- ❌ `MVCCAgent.commit()` stores full snapshots (delta-vectors would be cheaper)
- ❌ `RecoveryProtocols.emergency_halt()` uses banned vocab
- ❌ No frequency layer integration (no Kuramoto monitoring)
- ❌ No integration with SimSelf substrate (no axis coupling on instability)

---

## What's load-bearing

- ✅ **MemorySystem.store/load** — basic JSON persistence, can be wired into v6.2 unified's GraphMemory
- ✅ **MVCCAgent.rollback** — essential for Q3 proactive resilience
- ✅ **WorldBridge.check_feasible** — physical constraint enforcement (real, working)
- ⚠️ **RecoveryProtocols.emergency_halt** — needs rename to comply with Bobby's poisoned vocab ban

---

## Cross-reference

| This file | Canonical equivalent |
|-----------|----------------------|
| MemorySystem | `simself_v6_2_unified.GraphMemory` (more sophisticated) |
| HybridMemory | `simself/src/constitutional/geometric_memory.py` |
| WorldBridge | `fieldcore/src/robotic_master_controller.py` (focused on robots) |
| MVCCAgent | `simself/src/constitutional/ledger.py` (append-only, simpler) |
| RecoveryProtocols | `simself/src/constitutional/confabulation_filter.py` (governor-style) |

---

## Where this file should land

**decision (per Bobby's refactor-clean autonomy):**
- save raw verbatim ✅ done (vault/30-originals/simself-system-core-original-2026-09-14.md)
- canonical .py: `simself/src/system/core.py` (NEW dir, additive)
- canonical doc: this file (simself/docs/system-core-2026-09-14.md)
- future fix: rename `emergency_halt` → `emergency_close` (or `safety_halt` with documentation) to comply with poisoned vocab ban

---

## Bobby's poisoned vocabulary ban — applies to this file

Per memory log 2026-09-13 + this turn's explicit directive:
- ❌ "EMERGENCY HALT" — present in line 117 of the file
- ✅ recommended rename: `emergency_close(reason)` or `safety_close(reason)`
- ✅ print message should match: `EMERGENCY CLOSE: {reason}`

When this file is next touched (by Hermes or Bobby), the rename should be part of that work.

---

*Filed 2026-09-14 by Hermes for Bobby. Per Bobby: "save each raw file going forward i am deleting them... ingest fully no more skims."*

*This file IS the load-bearing implementation stub for the system module. Contains 1 poisoned vocab violation (line 117: `EMERGENCY HALT`) to fix in next pass.*
