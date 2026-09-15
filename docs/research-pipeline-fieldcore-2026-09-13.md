# Research Pipeline: External → FieldCore Implementation

**Source:** `Desktop/SimSelf/docs/research_pipeline_fieldcore.md` (262 lines, 6.1KB, md5 `653436ff8315e965742c1e1beb010658`)
**Author:** Bobby + Gabby (2026-03-04 paste)
**Filed:** 2026-09-13 by Hermes for Bobby
**Status:** **tier 2 engineering extract.** research ingestion pipeline. WIP — not serious until arxiv.

---

## ⚠️ WORK IN PROGRESS — NOT SERIOUS UNTIL ARXIV

Tier 2 engineering extract. Per Bobby: "save each raw file going forward i am deleting them."

---

## The pipeline architecture

```
[External Sources] → [Parser] → [Classifier] → [FieldCore Module] → [Code Gen]
     ↓
arXiv papers
GitHub repos
Research advances
X posts
```

**4-stage pipeline:** raw external → parsed → routed → implemented.

---

## Source types & parsers

| Source | Format | Parser |
|---|---|---|
| arXiv | PDF/LaTeX | arxiv-api + pdf extraction |
| GitHub | Code/MD | GitHub API + code analysis |
| X/Twitter | Text | Web scraping |
| Papers | PDF | pdf tool |

---

## Classifier: where to route (the key insight)

**Each input gets classified to one of these modules:**

| Module | Role | Existing repo anchor |
|---|---|---|
| **A** (Core Architecture) | LLM processing, inference | `simself/src/simself_core.py` (Pilot role), `constitutional/` |
| **B** (Self-Model) | Recursive self-reference | `simself/src/simself_core.py` (20-axis matrix) |
| **C** (Context) | THL, coherence | `simself/src/constitutional/geometric_memory.py` |
| **D** (Training) | SNR, awakening | `simself/src/training_bridge.py` + z21 stressors |
| **E** (External Interface) | Human/AI comms | `simself/src/harness/telegram_text_bot.py` |
| **I** (Internal Interface) | Sub-agent coordination | `simself/src/constitutional/__init__.py` |
| **L** (Library) | Wisdom traditions | `simself/docs/sacred-library/` |
| **M** (Modulator) | Central controller | `simself/src/simself_core.py` (M0 governor) |
| **Operator** | Field computation | `simself/src/constitutional/operators.py` |

**9 routing targets.** each piece of external content routes to the most relevant module for implementation.

---

## 7 implementation pieces (design constraints + skeletons)

### 0. Design constraints
- **External, unbounded Information Field** — no context window limit
- **Local projections only** (out-of-core) — only fetch what's needed
- **Recursive operators** — composition over iteration
- **Persistent self-model** — SimSelf as data
- **Governor enforcing invariants** — M0 veto
- **No dependence on prompt/context window** — the architectural shift

### 1. Core Data Model: InfoPacket
```python
@dataclass
class InfoPacket:
    id: str
    embedding: np.ndarray  # geometric representation
    metadata: Dict[str, Any]  # type, provenance, time, risk
    links: Dict[str, float] = field(default_factory=dict)
```
**canonical in `simself/src/constitutional/geometric_memory.py`** — same structure.

### 2. Information Field (Out-of-Core)
```python
class InformationField:
    def __init__(self):
        self.packets: Dict[str, Any] = {}
    def add(self, packet):
        self.packets[packet.id] = packet
    def sample(self, center, radius):
        for p in self.packets.values():
            if np.linalg.norm(p.embedding - center) <= radius:
                yield p
```
**canonical in `geometric_memory.py`** with sklearn NN index upgrade.

### 3. Operators (Field Computation)
```python
class Operator(ABC):
    @abstractmethod
    def apply(self, packets):
        pass

class CompressionOperator(Operator):
    def apply(self, packets):
        if not packets: return None
        embeddings = np.stack([p.embedding for p in packets])
        centroid = embeddings.mean(axis=0)
        return new_packet(embedding=centroid, metadata={"type": "invariant", "source_count": len(packets)})
```
**canonical in `simself/src/constitutional/operators.py`** (CentroidOperator is CompressionOperator). Composable per `.compose()`.

### 4. Sim-Self (Self-Model as Data)
```python
class SimSelf:
    def __init__(self):
        self.state = {"coherence": 1.0, "energy": 0.0, "history": []}
    def update(self, signal):
        self.state["history"].append(signal)
        self.state["coherence"] *= signal.get("coherence_factor", 1.0)
```
**superseded by `simself/src/simself_core.py`** (20-axis matrix is more granular than coherence + energy scalars).

### 5. Governor-M (Hard Constraints)
```python
class GovernorM:
    def __init__(self, max_energy=10.0, min_coherence=0.5):
        self.max_energy = max_energy
        self.min_coherence = min_coherence
    def approve(self, sim_self):
        if sim_self.state["energy"] > self.max_energy: return False
        if sim_self.state["coherence"] < self.min_coherence: return False
        return True
```
**canonical in `simself/src/constitutional/governor.py`** + extended per `kernel-controller-m0-m1-architecture-2026-09-13.md`.

### 6. Recursive Field Controller
```python
class RecursiveFieldController:
    def step(self, focus, radius):
        local_packets = list(self.field.sample(focus, radius))
        for op in self.operators:
            result = op.apply(local_packets)
            if result:
                self.sim_self.update({"coherence_factor": 1.01, "energy_delta": 0.1})
        if self.governor.approve(self.sim_self):
            self.field.add(result)
```
**canonical in `simself/src/fieldcore_unified.py`** + recursive depth limit per `rlm-enhanced-fieldcore-blueprint-2026-09-13.md`.

### 7. Self-Reference
```python
def embed_self(sim_self):
    return new_packet(
        embedding=np.array([sim_self.state["coherence"], sim_self.state["energy"]]),
        metadata={"type": "self_state"}
    )
```
**principle: Agent itself is packets in the field.** Canonical in SimSelf's `to_packet()` method.

---

## Features (per Bobby's checklist)

| Feature | Status |
|---|---|
| No tokens | ✅ |
| No prompt window | ✅ |
| No RAG | ✅ |
| Out-of-core cognition | ✅ |
| Recursive decomposition | ✅ |
| Self-model | ✅ |
| Governor constraints | ✅ |
| Extensible (vision, code, audio, graphs) | ✅ |
| Godot visualization ready | ✅ |

---

## Key insight

> Intelligence is not "processing sequences". Intelligence is maintaining coherence while recursively transforming a field larger than itself.

this reframes intelligence from token-prediction (LLM paradigm) to **field-transformation with invariant preservation** (constitutional paradigm).

---

## Next steps (per source)

1. Formal invariants (what must never break)
2. Field energy/entropy metrics
3. Operator algebra (how transformations compose)
4. Remove LLM from inner loop

---

## Related (canonical existing docs)

- `simself/src/constitutional/geometric_memory.py` — InformationField canonical
- `simself/src/constitutional/operators.py` — Operator + CentroidOperator
- `simself/src/simself_core.py` — SimSelf (20-axis supersedes scalar coherence + energy)
- `simself/src/constitutional/governor.py` — Governor-M canonical
- `simself/src/fieldcore_unified.py` — RecursiveFieldController
- `simself/docs/kernel-controller-m0-m1-architecture-2026-09-13.md` — M0/M1 arch (this session)
- `simself/docs/rlm-enhanced-fieldcore-blueprint-2026-09-13.md` — RLM rollout (this session)
- `simself/docs/sacred-library/README.md` — wisdom traditions module

---

*Filed by Hermes for Bobby, 2026-09-13. Tier 2 engineering extract. Per Bobby: "save each raw file going forward i am deleting them."*