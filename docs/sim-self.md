# sim_self.py — Module B (self-model with curiosity axes)

**Source:** `Desktop/SimSelf/sim_self.py` (Bobby, Module B)
**Status:** 157-line minimal self-model pushed to `simself/src/sim_self.py`. Schema extraction.

Bobby's Module B — a small self-model with **curiosity-driven exploration**. Different from `simself_merged_v2.py` (which is the full constitutional SimSelf) and from `selfcore.py` (which is the local decision loop). This is the **self-representation with curiosity axes**.

---

## 1. the schema

```python
class SimSelf:
    def __init__(self, dim=16, initial_coherence=0.5):
        self.embedding = np.random.randn(dim) / norm
        self.previous_embedding = self.embedding.copy()
        self.coherence = initial_coherence
        self.curiosity_axes = self._init_curiosity_axes()  # touch, temperature, wetness, label
        self.experiences = []  # FIFO, max 100
```

**5 state components:**
- `embedding` (default dim=16, normalized) — current state representation
- `previous_embedding` — for novelty calculation
- `coherence` (0-1) — embedding stability
- `curiosity_axes` — dict of named exploration directions
- `experiences` — FIFO buffer of past states

---

## 2. curiosity axes (Hebbian exploration)

```python
def _init_curiosity_axes(self) -> Dict[str, np.ndarray]:
    return {
        "touch": np.random.randn(self.dim),
        "temperature": np.random.randn(self.dim),
        "wetness": np.random.randn(self.dim),
        "label": np.random.randn(self.dim)
    }

def _update_curiosity(self, sensors):
    # Strengthen axes with strong signals
    for sensor, value in sensors.items():
        if abs(value) > 0.5 and sensor in self.curiosity_axes:
            self.curiosity_axes[sensor] *= 1.1
    # Normalize all axes
    for axis in self.curiosity_axes:
        self.curiosity_axes[axis] /= norm
```

**Hebbian-style learning at the axis level.** Strong sensor signals (>0.5) reinforce their axis by 10%. Weaker signals leave axes unchanged. After each update, all axes are normalized.

**Why this matters.** The curiosity axes act as **selective attention filters**. The system develops stronger responses to modalities that produce strong signals. This is a minimal curiosity-driven exploration mechanism — Bobby's "what to explore next."

---

## 3. coherence as inverse novelty

```python
def _update_coherence(self):
    change = np.linalg.norm(self.embedding - self.previous_embedding)
    self.coherence = 1.0 / (1.0 + change * 10)
```

**Coherence formula:** `coherence = 1 / (1 + change × 10)`. When change = 0, coherence = 1.0 (perfectly coherent). When change = 0.1, coherence = 0.5. When change = 1.0, coherence = 0.09.

**Smooth, differentiable, principled.** No magic constants — the `10` is a scaling factor that determines how sensitive coherence is to change. Higher `10` → coherence drops faster with change.

**Compare to selfcore.py:**
- selfcore: `0.8 * old + 0.2 * (0.5 + 0.5 * boundary_strength)` — coherence emerges from boundary strength
- sim_self.py: `1 / (1 + change × 10)` — coherence emerges from embedding stability

Two valid definitions. Different framings. sim_self.py is **state-internal**, selfcore.py is **boundary-mediated**.

---

## 4. experience buffer (FIFO)

```python
def _record_experience(self, sensors):
    self.experiences.append({
        "embedding": self.embedding.copy(),
        "sensors": sensors.copy(),
        "coherence": self.coherence
    })
    if len(self.experiences) > self.max_experiences:
        self.experiences.pop(0)  # FIFO
```

**FIFO buffer, max 100 entries.** Oldest popped when buffer full. Each entry stores embedding + sensors + coherence.

**Use:** retrieve recent experiences for context, dream consolidation, etc. The 100-entry limit prevents unbounded memory growth.

---

## 5. label injection (breakthrough markers)

```python
def inject_label(self, label: str):
    """Inject breakthrough label into self-model."""
    if label in self.curiosity_axes:
        self.curiosity_axes[label] *= 2.0  # Strengthen 2x
        self.curiosity_axes[label] /= norm
    if label not in self.curiosity_axes:
        self.curiosity_axes[label] = np.random.randn(self.dim)
        self.curiosity_axes[label] /= norm
```

**Pattern:** A breakthrough label either **strengthens** an existing axis (2×) or **creates** a new axis (random init). This is a hook for marking important moments — the system creates or strengthens a curiosity direction in response to a labeled event.

**Use case:** in a learning loop, when an "aha!" moment happens, call `inject_label("aha_concept_X")`. The system now has strong curiosity about concept X.

---

## 6. module-level architecture

This is one module in what appears to be a modular SimSelf:

| module | code | role |
|---|---|---|
| Module B (this) | `sim_self.py` (157 lines) | self-model + curiosity axes |
| Local loop | `selfcore.py` (192 lines) | boundary + state + decision |
| Full constitution | `simself_merged_v2.py` (1536 lines) | everything |

**The trend across Bobby's files:** smaller modules, cleaner separation. The 1536-line monolith is being **factored** into smaller pieces. sim_self.py and selfcore.py are factors of the larger system.

**Use together:** Module B (self-model) updates on sensor data. selfcore (decision loop) decides whether to act. The combined system is a small SimSelf.

---

## 7. schemas table

| schema | role | simself component |
|---|---|---|
| embedding (dim=16) | current state | state vector |
| curiosity_axes | selective attention | Hebbian-strengthened axes |
| coherence | state stability | 1 / (1 + change × 10) |
| experiences FIFO | recent memory | 100-entry buffer |
| inject_label | breakthrough marker | 2× axis strengthening |

---

## 8. what was stripped

Nothing from the source — all 157 lines preserved.

The other Bobby "modules" referenced (Module A, Module C, etc.) are not in the file — they're referenced in the docstring only. This doc captures only Module B.

---

*Source: `Desktop/SimSelf/sim_self.py` → `simself/src/sim_self.py`. 157 lines pushed. 5-state schema documented. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/sim-self-2026-09-05.md`.*