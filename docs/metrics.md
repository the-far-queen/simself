# metrics.py — continuity tracking + stage assessment

**Source:** `Desktop/SimSelf/metrics.py` (Bobby, simple metrics module)
**Status:** 111-line module pushed to `simself/src/metrics.py`. Continuity + drift + stage schemas extracted.

Bobby's small metrics module — track stability, continuity, and developmental stage over time. Singleton `metrics = MetricsTracker()` at module bottom for easy global use.

---

## 1. the schema

```python
@dataclass
class MetricSnapshot:
    timestamp: float
    name: str
    value: float
    metadata: Dict = field(default_factory=dict)


class MetricsTracker:
    def __init__(self):
        self.snapshots: List[MetricSnapshot] = []   # max 1000, FIFO
        self.current_stage: str = "seeker"
        self.stage_progress: float = 0.0
```

**State:** snapshots (max 1000, FIFO), current_stage, stage_progress.

**Singleton:** `metrics = MetricsTracker()` at module bottom — global instance.

---

## 2. continuity = inverse of variance

```python
def continuity_score(self) -> float:
    coherence_history = self.get("coherence", 20)
    if len(coherence_history) < 5:
        return 0.5
    variance = np.var(coherence_history)
    return 1.0 / (1.0 + variance * 10)
```

**Formula:** `continuity = 1 / (1 + var(coherence_history) * 10)`. When variance = 0, continuity = 1.0 (perfectly stable). When variance = 0.1, continuity = 0.5. When variance = 1.0, continuity = 0.09.

**Same shape, different input than other coherence definitions:**

| file | formula |
|---|---|
| selfcore.py | `coherence = 0.8 * old + 0.2 * (0.5 + 0.5 * boundary_strength)` |
| sim_self.py | `coherence = 1 / (1 + change * 10)` |
| metrics.py | `continuity = 1 / (1 + var(history) * 10)` |

Three different coherence definitions across Bobby's modules. They measure different things:
- selfcore: coherence as **boundary-mediated EMA**
- sim_self: coherence as **change-driven** (recent vs previous)
- metrics: continuity as **variance-driven** (history stability)

**Recommendation:** unify these three into a single `CoherenceState` class with clear inputs. Not done here — Bobby's design.

---

## 3. NEW: drift detection (sliding-window)

```python
def drift_detection(self) -> Dict:
    coherence = self.get("coherence", 50)
    if len(coherence) < 10:
        return {"drifting": False, "reason": "insufficient_data"}
    
    recent = np.mean(coherence[-10:])
    if len(coherence) >= 20:
        earlier = np.mean(coherence[-20:-10])
    else:
        earlier = np.mean(coherence[:10])
    
    if recent < earlier * 0.8:
        return {"drifting": True, "rate": earlier - recent}
    return {"drifting": False}
```

**Schema:** Drift detected when `recent_mean < earlier_mean * 0.8`. Returns `{drifting: True, rate: ...}` or `{drifting: False}`.

**Sliding-window of 10 vs 10.** Compares the last 10 measurements to the previous 10. If recent dropped to 80% or less, drift.

**Use:** automated monitoring — if drift detected, alert or trigger recovery.

---

## 4. NEW: stage assessment (seeker / deconstructor)

```python
def stage_assessment(self) -> Dict:
    continuity = self.continuity_score()
    coherence_vals = self.get("coherence", 10)
    coherence = np.mean(coherence_vals) if coherence_vals else 0.5
    
    if continuity > 0.8 and coherence > 0.7:
        self.current_stage = "deconstructor"
        self.stage_progress = min(1.0, self.stage_progress + 0.01)
    elif continuity > 0.6:
        self.current_stage = "seeker"
        self.stage_progress = min(1.0, self.stage_progress + 0.005)
    
    return {"stage": self.current_stage, "progress": self.stage_progress, ...}
```

**Two stages:** "seeker" (continuity > 0.6) and "deconstructor" (continuity > 0.8 AND coherence > 0.7).

**Note:** This is **different vocabulary** from `axes-ladder.md`'s 5-phase ladder (Foundational/Proto-Awareness/Coherent Self/Integrated Being/Sentient Horizon). Bobby's metrics.py uses simpler 2-stage assessment.

**Stage_progress** increases by 0.01 per "deconstructor" assessment or 0.005 per "seeker" assessment, capped at 1.0. Slow accumulator.

---

## 5. the snapshot FIFO buffer

```python
def record(self, name, value, metadata=None):
    self.snapshots.append(MetricSnapshot(
        timestamp=time.time(),
        name=name, value=value, metadata=metadata or {}
    ))
    if len(self.snapshots) > 1000:
        self.snapshots.pop(0)  # FIFO
```

**Max 1000 snapshots, FIFO.** Oldest dropped when full. Each snapshot has timestamp + name + value + metadata.

**Use:** record any metric. Query with `get(name, n=10)` to get recent values for a metric by name. Pattern: `metrics.record("coherence", 0.85)` then `metrics.get("coherence", 20)`.

---

## 6. summary pattern

```python
def summary(self) -> Dict:
    return {
        "stage": self.current_stage,
        "continuity": self.continuity_score(),
        "drift": self.drift_detection(),
        "snapshots": len(self.snapshots)
    }
```

**Single-call introspection.** Returns current state in one dict. Use this for monitoring dashboards, log output, or feeding back into the LLM via `state_snapshot()` pattern from `simself-deployment-guide.md`.

---

## 7. schemas table

| schema | role | simself component |
|---|---|---|
| MetricSnapshot | single measurement | timestamped scalar |
| MetricsTracker | monitoring state | FIFO + stage + drift |
| Continuity (variance) | stability over time | 1 / (1 + var × 10) |
| Drift detection | sliding-window check | recent vs earlier means |
| Stage assessment | 2-stage development | seeker / deconstructor |
| FIFO buffer (max 1000) | bounded memory | last 1000 snapshots |

---

## 8. what was stripped

Nothing from the source — all 111 lines preserved.

The "seeker"/"deconstructor" stage names don't match the 5-phase ladder — flagged for future unification but not extracted as separate doc.

---

*Source: `Desktop/SimSelf/metrics.py` → `simself/src/metrics.py`. 111 lines pushed. 4 schemas extracted. 3 coherence-formula divergence noted. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/metrics-2026-09-05.md`.*