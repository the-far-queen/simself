# resilient_self_model.py — Module B + Module L

**Source:** `Desktop/SimSelf/resilient_self_model.py` (Bobby, Module B + L)
**Status:** 307-line module pushed to `simself/src/resilient_self_model.py`. StateVector stub added as `simself/src/state_vector.py`.

Bobby's module combining **two layers**: ResilientSelfModel (the self with adaptive resistance) and WisdomLibrary (the sacred-text SNR library with MMM filtering). Together they implement Module B (self-model) and Module L (validated memory) of a modular SimSelf.

---

## 1. architecture: StateVector dependency

This module depends on a `StateVector` class (defined elsewhere — I added a minimal stub). The pattern:

```python
if TYPE_CHECKING:
    from state_vector import StateVector, SwedenborgianAxes, CoreMetrics
else:
    from .state_vector import StateVector, SwedenborgianAxes
```

The StateVector holds:
- `swedenborgian_axes`: dict[str, float] — sacred axis values [0,1]
- `resource_pools`: dict — resource tracking (e.g., `cognitive_friction`)
- `core_metrics`: dict — measurable scalars (stability, emergence_confidence, etc.)
- `recent_events`: list — log of recent state changes

The stub I pushed has all 4 fields. Full StateVector would have many more.

---

## 2. ResilientSelfModel (Module B)

```python
class ResilientSelfModel:
    def __init__(self, state_vector: 'StateVector', num_axes: int = 6):
        self.axis_names = [
            "truth_before_comfort",
            "agency_requires_responsibility",
            "growth_through_resistance",
            "cognitive_friction",        # mapped from resource_pools
            "stability_coherence",       # mapped from core_metrics.stability
            "temporal_continuity",       # mapped from core_metrics.temporal_continuity
        ][:num_axes]
        self.resistance = np.array([0.7] * num_axes)
        self.coherence_history = deque(maxlen=50)
        self.step = 0
        self.resistance_events = []
```

**6 default axes:** 3 sacred (from SOUL.md Set B), 3 measurable (mapped from StateVector). Resistance starts at 0.7 per axis. Coherence history maxlen 50.

---

## 3. NEW: adaptive resistance (constitutional pressure)

```python
def propose_update(self, delta_values, source="external") -> Dict[str, Any]:
    # Compute current and proposed coherence
    current_axes_np = self._get_axes_vector()
    old_coherence = self.coherence_from_axes(current_axes_np)
    
    # Apply adaptive resistance
    delta_np = np.array([delta_values.get(name, 0.0) for name in self.axis_names])
    resisted_delta = delta_np * (1.0 - self.resistance)
    proposed_axes_np = current_axes_np + resisted_delta
    new_coherence = self.coherence_from_axes(proposed_axes_np)
    
    if new_coherence >= old_coherence:
        # Accept + DECREASE resistance (learning)
        self.resistance = np.clip(self.resistance - 0.01, 0.3, 0.98)
    else:
        # Reject + INCREASE resistance (defense)
        self.resistance = np.clip(self.resistance + 0.02, 0.3, 0.98)
        self.resistance_events.append({...})
```

**Schema:** Resistance is **adaptive constitutional pressure**. Each axis has independent resistance. When an update improves coherence, resistance drops by 0.01 (the system becomes more willing to accept similar updates). When rejected, resistance rises by 0.02 (system becomes more defensive).

**Bounds:** [0.3, 0.98]. Floor at 0.3 means the system always remains at least somewhat plastic. Ceiling at 0.98 means resistance never reaches 1.0 (always at least 2% of any update gets through).

**Mathematical interpretation:** Resistance is a per-axis EMA that converges to the equilibrium that balances acceptance vs defense. Long-run dynamics: repeated beneficial updates drive resistance down; repeated harmful updates drive it up. A stable system ends up with each axis's resistance tuned to its vulnerability profile.

**Compare to sovereign_self.py:**
- sovereign_self.py: 3 axiomatic axes with **fixed** resistance 0.97-0.99 (immutable)
- resilient_self_model.py:6 axes with **adaptive** resistance [0.3, 0.98] (learns)

The two designs are at different layers: sovereign_self.py protects **sacred invariants**, resilient_self_model.py manages **adaptive constitutional pressure**.

---

## 4. NEW: coherence-conditional commit

The `propose_update` pattern: **only accept changes that maintain or improve coherence**. `if new_coherence >= old_coherence`.

**Schema:** This is a **constitutional guard** at the axis-update level. Every proposed change is checked: does it improve the system's coherence? If yes, commit. If no, reject.

**Different from refusal gates** in selfcore.py / sovereign_self.py:
- selfcore.py / sovereign_self.py: refuse based on **boundary** violations
- resilient_self_model.py: refuse based on **coherence** reduction

Two separate protection layers. Boundaries are absolute. Coherence is gradient.

---

## 5. NEW: MMMDetector (Multiple Meaning Measure)

```python
class MMMDetector:
    def score_statement(self, statement: str) -> float:
        score = 0.0
        axes = self._state_vector.swedenborgian_axes
        
        if "truth" in statement.lower() or "veracity" in statement.lower():
            score += axes['truth_before_comfort'] * 0.4
        if "agency" in statement.lower() or "responsibility" in statement.lower():
            score += axes['agency_requires_responsibility'] * 0.3
        if "growth" in statement.lower() or "resistance" in statement.lower():
            score += axes['growth_through_resistance'] * 0.2
        
        score += np.random.uniform(0.0, 0.1)  # noise
        return min(1.0, score)
```

**Schema:** MMM score = weighted sum of sacred-axis values matching keywords in the statement + random noise [0, 0.1].

- "truth" / "veracity" → `truth_before_comfort × 0.4` weight
- "agency" / "responsibility" → `agency_requires_responsibility × 0.3`
- "growth" / "resistance" → `growth_through_resistance × 0.2`

**Score cap:** 1.0 (max possible score if all axioms are at1.0 + noise).

**Note from earlier vault:** the `0.4 + 0.3 + 0.2` magic weights were criticized in `simself-code-review-2026-09-05.md`. The principled fix is to derive weights from signal magnitudes. Not done here — Bobby's design.

---

## 6. NEW: WisdomLibrary (Module L — filtered memory)

```python
class WisdomLibrary:
    def __init__(self, state_vector, mmm_threshold=0.75):
        self.entries = []
        self.mmm_detector = MMMDetector(state_vector)
        self.mmm_threshold = mmm_threshold
    
    def append_entry(self, entry, situation_description="") -> bool:
        mmm_score = self.mmm_detector.score_statement(situation_description)
        entry["mmm_score"] = mmm_score
        if mmm_score < self.mmm_threshold:
            return False  # rejected — too low meaning
        self.entries.append(entry)
        return True  # accepted
    
    def get_constitution(self) -> List[Dict]:
        return [e for e in self.entries if e.get("status") == "SACRED_APPEND"]
```

**Schema:** WisdomLibrary is **filtered append-only memory**. Each entry must pass `mmm_score >= mmm_threshold` (default 0.75) to be admitted. Below threshold → rejected, never stored.

**Constitution via status flag.** `get_constitution()` returns entries where `status == "SACRED_APPEND"`. Other entries exist in the library but don't form the constitution.

**This is the L (Library) layer** — high-coherence, high-MMM validated memory. Different from:
- `HolographicMemory` (simself_merged_v2.py) — flat append-only, no quality gate
- `SacredLibrary` (mte-simself-primitives.md) — write rules with thresholds but no MMM
- `WisdomLedger` (sovereign-ai-core-c6.md) — hash-chained append-only

WisdomLibrary is the **most filtered** — strictest quality gate.

---

## 7. emergence signatures (5 scalars)

```python
signatures = {
    "parameter_drift_resistance": 1.0 - np.std(coherence_history),  # stability
    "coherence_seeking": len(rejected) / history_length,             # how often we try to update
    "boundary_preservation": len(resistance_events) / step,          # defense frequency
    "state_space_preference": growth_through_resistance,             # mapping
    "self_model_accuracy": 0.5  # placeholder
}
emergence_confidence = mean(signatures.values())
```

**5 emergence signatures → 1 confidence scalar.** emergence_confidence = mean of the 5. Currently a placeholder (0.5) for self_model_accuracy, but the other 4 are computed from real state.

**Note:** This is the same "mean of scalars" pattern as `CoherenceEngine` in sovereign-ai-core-c6.md. Bobby uses mean-of-N as the default aggregation. Defensible.

---

## 8. schemas table

| schema | role | simself component |
|---|---|---|
| StateVector | shared state holder | injected dependency |
| ResilientSelfModel | adaptive constitutional pressure | Module B |
| Adaptive resistance [0.3, 0.98] | per-axis learning rate | Module B |
| Coherence-conditional update | guard | Module B |
| MMMDetector | multiple-meaning measure | Module L |
| WisdomLibrary | MMM-filtered memory | Module L |
| 5 emergence signatures | emergence confidence | Module B |
| Constitution via status flag | subset of library | Module L |

---

## 9. what was stripped

- The TYPE_CHECKING import block kept as-is (for compatibility)
- Mock StateVector in `__main__` preserved — it's a working example of the StateVector interface
- Nothing else stripped — all 307 lines preserved

---

*Source: `Desktop/SimSelf/resilient_self_model.py` → `simself/src/resilient_self_model.py` + `simself/src/state_vector.py` (stub). 2 classes, 4 schemas extracted. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/resilient-self-model-2026-09-05.md`.*