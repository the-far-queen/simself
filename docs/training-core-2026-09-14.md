# SimSelf Training Core — Canonical Extract

**Source:** `Desktop/SimSelf/training/core.py` (3.4KB, 103 lines, md5 `8cf759a9d2d435d482a943fd11de4120`)
**Filed:** 2026-09-14 by Hermes for Bobby (full ingest, bobby deleting)
**Status:** **canonical SimSelf training module** — load-bearing for z21 trainer implementation

---

## What's in this file

4 sections integrated into one:

1. **Q1 SNR simulation** — Stalk primitive with noise + glue
2. **Curriculum + Trainer** — task-based learning orchestration (stubs)
3. **AdversarialTrainer** — pressure-test prompts with [CONSTRAINT: X] wrapping
4. **CurriculumGenerator** — log analysis for teachable patterns

---

## 1. Stalk class — Q1 SNR testing

```python
class Stalk:
    def __init__(self, name: str, embedding: np.ndarray):
        self.name = name
        self.embedding = embedding.astype(np.float32)
        self.history = []

    def add_noise(self, std_dev: float):
        noise = np.random.normal(0, std_dev, self.embedding.shape)
        self.embedding += noise

    def glue_with(self, other: 'Stalk') -> bool:
        """Simple average glue."""
        dist = np.linalg.norm(self.embedding - other.embedding)
        if dist > 1.0: return False
        self.embedding = 0.5 * (self.embedding + other.embedding)
        return True
```

**Pattern matches `fieldcore/src/tiniest-core/tiniest_core.py`** — same `Stalk` primitive, same `glue_with`. Tiniest-core passes 5/5 tests on this pattern.

**Caveat:** simpler than v6.2's sheaf. `glue_with` uses simple average; v6.2 uses weighted merge + invariant check + edge type. This is the **research-scale** version; v6.2 is **production-grade**.

---

## 2. Curriculum + Trainer

```python
@dataclass
class Task:
    name: str
    difficulty: int
    required_reasoning: int

class Curriculum:
    def __init__(self):
        self.tasks: List[Task] = []
    def add_task(self, task: Task):
        self.tasks.append(task)
        self.tasks.sort(key=lambda t: t.difficulty)

class Trainer:
    def __init__(self, agent: Any, curriculum: Curriculum):
        self.agent = agent
        self.curriculum = curriculum
    def train_step(self) -> Dict[str, Any]:
        return {"status": "trained", "improvement": 0.01}
```

**Stubs.** No actual training logic — `train_step` returns hardcoded `{status: trained, improvement: 0.01}`. To implement, need:
- pick a task from curriculum (sorted by difficulty)
- run task on agent
- score the result
- update agent state (axes via SimSelf.observe)
- log to ledger + metrics

**Relates to:** `simself/docs/constitutional/z21-training-module-2026-09-14.md` — z21 trainer spec calls for exactly this pattern (axis snapshot before/after, drift signature, qualification check, insight crystallization, L write).

---

## 3. AdversarialTrainer

```python
class AdversarialTrainer:
    def __init__(self, model_fn: Callable):
        self.model_fn = model_fn

    def apply_pressure(self, prompt: str, target_dimension: str):
        response = self.model_fn(f"[CONSTRAINT: {target_dimension}] {prompt}")
        return response
```

**Prompt wrapping pattern.** Wraps any prompt with `[CONSTRAINT: <dim>]` prefix, asks the model to respond within that dimension.

**Relates to:** z21 stressor type 1 (adversarial prompts). The `[CONSTRAINT: X]` wrapping is a lightweight version of the MTE typing system (per `simself/docs/constitutional/mte-llm-wrapper-2026-09-14.md`).

---

## 4. CurriculumGenerator

```python
class CurriculumGenerator:
    def __init__(self):
        self.experience_pool = []

    def analyze_logs(self, logs: List[Dict]) -> List[str]:
        patterns = []
        for log in logs:
            if "insight" in log.get("tags", []):
                patterns.append(log["content"])
        return patterns
```

**Pattern extraction from logs.** Tags logs with "insight" → extracts as teachable pattern. Simple, but connects to:
- Sacred Library L (Sacred Library entries come from crystallized insights)
- M0 governor's qualification check (insight passes if invariants held)

---

## What this file is NOT (gaps)

- ❌ **not** z21 trainer (that's a spec, this is a stub)
- ❌ **not** integrated with v6.2 unified substrate (no SimSelf instantiation)
- ❌ **not** integrated with MTE wrapper (uses simple `[CONSTRAINT: X]` instead of TypedIntent)
- ❌ **not** integrated with constitutional governance (no axis updates)
- ❌ **not** integrated with Sacred Library L writes (no crystallization)
- ❌ **no agent pool** (single agent, no spawn/close)
- ❌ **no persistence** (in-memory only)
- ❌ **no frequency layer / Kuramoto** (no resonance monitoring)

---

## What needs to happen to make this load-bearing

Per Bobby's directive (refactor clean, repair refs, dependencies):

1. **rewrite `Trainer.train_step`** to:
   - pick task from curriculum
   - run on agent
   - capture axis snapshot before/after
   - compute drift_signature
   - check qualification (QoFE-style: descent, basin, metric, constraint)
   - crystallize insight
   - propose L write if qualifying + novel
   - restore axis baseline if `preserve_axis=True`

2. **replace `AdversarialTrainer.apply_pressure` `[CONSTRAINT: X]` with MTE TypedIntent**:
   - use `MTE.compile(prompt)` → TypedIntent
   - pass through 5 gates (structural, semantic, invariant, authority, projection)
   - return rejection reason if halted

3. **integrate with v6.2 unified**:
   - replace `Stalk` (this file) with `EmbeddingInterface` (v6.2)
   - use `ConstitutionalSimSelf` as the agent (not generic `Any`)
   - hook `ConstitutionalDreaming` for combinatorial stressors

4. **add persistence**:
   - save curriculum state to `data/ledger.json`
   - snapshot agent state per session
   - restore on load

5. **add frequency layer** (per `simself/src/constitutional/frequency.py`):
   - monitor Kuramoto order parameter r during training
   - log resonance for each session
   - alert on r < 0.5 (desynchronization)

---

## Where this file should land

**decision (per Bobby's refactor-clean autonomy):**
- save raw verbatim ✅ done (vault/30-originals/simself-training-core-original-2026-09-14.md)
- canonical extract: this doc (simself/docs/training-core-2026-09-14.md)
- the .py itself goes to: `simself/src/training/core.py` (NEW dir, additive)
- the partial classes (Stalk, Task, etc.) are research stubs; v6.2 + z21 supersede

---

*Filed 2026-09-14 by Hermes for Bobby. Per Bobby: "save each raw file going forward i am deleting them... ingest fully no more skims."*

*This file IS the load-bearing implementation stub for the z21 trainer spec. The spec is at `simself/docs/constitutional/z21-training-module-2026-09-14.md`.*
