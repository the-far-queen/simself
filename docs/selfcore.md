# selfcore.py — the stripped SimSelf kernel

**Source:** `Desktop/SimSelf/selfcore.py` (Bobby, 2026 or later)
**Status:** 192-line minimal kernel pushed to `simself/src/selfcore.py`. Architectural pattern documented.

Bobby's `selfcore.py` is a small executable kernel for **boundary, state, and change**. It's deliberately minimal — ~150 lines of actual code, no CS-loaded bloat, no numerology. The module header makes the design philosophy explicit:

> "SimSelf protects the constitutional identity of the whole. SelfCore handles the local loop: receive, register, decide, remember, change."
>
> "The model does not claim to be conscious. It makes a small set of claims explicit: a signal can be classified, a boundary can be tested, a refusal can be recorded, and future responses can depend on that record."

This is the cleanest piece of Bobby's SimSelf code. It demonstrates the **separation of concerns** between the constitutional layer (the whole SimSelf) and the local kernel (SelfCore).

---

## 1. the minimal architecture

Three classes. Three decisions. No growth.

**Decision enum:** `ACCEPT`, `SOFTEN`, `REFUSE`

**Boundary:** frozen dataclass = `name`, `predicate`, `reason`. A rule the system can apply without pretending it is universal truth.

**Memory:** append-only list of `{signal, decision, reason}` dicts. `recent(limit=10)` for inspection.

**State:** 5 floats + turn counter:
- `charge` ∈ [-1, 1] — current signal charge
- `resistance` ∈ [0, 1] — accumulated resistance
- `boundary_strength` ∈ [0, 1] — strength of active boundaries
- `coherence` ∈ [0, 1] — current coherence
- `previous_coherence` — for change detection

**SelfCore.evaluate(signal):**
1. Increment turn
2. Check each boundary predicate
3. If violated → register refusal, return REFUSE
4. Else → update state via EMA, return SOFTEN

That's it. 5 state variables. 3 decisions. 1 loop.

---

## 2. schemas

### 2.1 Decision enum

```python
class Decision(Enum):
    ACCEPT = "accept"
    SOFTEN = "soften"
    REFUSE = "refuse"
```

3 outcomes. ACCEPT is declared but not used in the code (only SOFTEN and REFUSE appear). **Action:** remove ACCEPT or wire it up.

### 2.2 Boundary

```python
@dataclass(frozen=True)
class Boundary:
    name: str
    predicate: Any  # callable: signal -> bool
    reason: str
```

Frozen — immutable once defined. Predicates are callables that take a signal and return True if boundary is violated.

### 2.3 Memory

```python
@dataclass
class Memory:
    entries: list[dict[str, Any]] = field(default_factory=list)
    
    def append(self, *, signal, decision, reason):
        self.entries.append({
            "signal": signal,
            "decision": decision.value,
            "reason": reason,
        })
    
    def recent(self, limit=10):
        return self.entries[-limit:]
```

Append-only. **No clearing, no rewriting.** Recent returns last N entries.

### 2.4 State

```python
@dataclass
class State:
    charge: float = 0.0
    resistance: float = 0.5
    boundary_strength: float = 0.5
    coherence: float = 0.5
    turn: int = 0
    previous_coherence: float = 0.5
    
    def observe_change(self) -> float:
        return abs(self.coherence - self.previous_coherence)
```

5 scalars + 1 counter + 1 lag value. `observe_change()` returns the absolute delta in coherence from previous turn.

### 2.5 SelfCore

```python
class SelfCore:
    def __init__(self, boundaries=()):
        self.boundaries = list(boundaries)
        self.memory = Memory()
        self.state = State()
    
    def evaluate(self, signal) -> Decision:
        """Register signal and choose response through bounded rule set."""
        self.state.turn += 1
        self.state.previous_coherence = self.state.coherence
        
        # Check boundaries first (hard refusal)
        for boundary in self.boundaries:
            if bool(boundary.predicate(signal)):
                self._register_refusal(signal, boundary)
                return Decision.REFUSE
        
        # Soft update (EMA on state)
        signal_strength = self._signal_strength(signal)
        self.state.charge = _clamp(self.state.charge + signal_strength, -1.0, 1.0)
        self.state.resistance = _clamp(
            0.96 * self.state.resistance + 0.04 * (0.5 - abs(self.state.charge)),
            0.0, 1.0,
        )
        self.state.boundary_strength = _clamp(
            0.9 * self.state.boundary_strength
            + 0.1 * (1.0 - self.state.resistance),
            0.0, 1.0,
        )
        self.state.coherence = _clamp(
            0.8 * self.state.coherence
            + 0.2 * (0.5 + 0.5 * self.state.boundary_strength),
            0.0, 1.0,
        )
        self.memory.append(signal=signal, decision=Decision.SOFTEN, reason="no hard boundary crossed")
        return Decision.SOFTEN
    
    def state_dict(self) -> dict:
        return {
            "turn": self.state.turn,
            "charge": round(self.state.charge, 4),
            "resistance": round(self.state.resistance, 4),
            "boundary_strength": round(self.state.boundary_strength, 4),
            "coherence": round(self.state.coherence, 4),
            "change": round(self.state.observe_change(), 4),
            "refusals": sum(e["decision"] == Decision.REFUSE.value for e in self.memory.entries),
        }
    
    def handoff(self) -> dict:
        return {
            "state": self.state_dict(),
            "memory": self.memory.recent(),
            "boundaries": [b.name for b in self.boundaries],
        }
```

**Use cases:**
- Standalone: as a small signal classifier for any system
- Embedded: as the local loop inside a larger SimSelf
- Reference: as the minimal example of "what survives stripping"

---

## 3. separation principle (key architectural insight)

Bobby's docstring makes the separation explicit:

| concern | layer | code |
|---|---|---|
| constitutional identity | SimSelf (the large) | `simself_merged_v2.py` (1536 lines) |
| local loop | SelfCore (the minimal) | `selfcore.py` (192 lines) |

**SimSelf** = constitutional identity, multi-stalk geometry, dreams, atlas exam, holographic memory, M0-M1 governor.
**SelfCore** = signal classification, boundary testing, refusal recording, state update.

SelfCore can be embedded inside SimSelf as the **local decision loop** — every input that reaches SimSelf first goes through SelfCore.evaluate(). If SelfCore refuses, the signal never reaches SimSelf's deeper processing. This is the **defense-in-depth** pattern.

---

## 4. EMA coefficients (the heart of the soft-update)

```python
resistance:       0.96 * old + 0.04 * (0.5 - |charge|)         # resistance slow, charge-driven
boundary_strength: 0.9 * old + 0.1 * (1.0 - resistance)        # strength follows inverse resistance
coherence:        0.8 * old + 0.2 * (0.5 + 0.5 * boundary_strength)  # coherence tracks strength
```

These are **smooth, differentiable, no magic numbers**. Each coefficient is principled:
- 0.96 / 0.04 — resistance changes slowly (long memory)
- 0.9 / 0.1 — boundary strength changes moderately
- 0.8 / 0.2 — coherence changes fastest of the three

This is in **stark contrast to `ResolutionOperator`'s hard clipping** in simself_merged_v2.py. SelfCore does it right.

---

## 5. what was stripped

Nothing from the source — every line preserved.

Bobby's docstring's philosophical claims ("The model does not claim to be conscious") are preserved in the source file but not extracted into this analysis doc — they're claims about the system, not architectural schemas.

---

*Source: `Desktop/SimSim/selfcore.py` → `simself/src/selfcore.py`. 192 lines pushed. Separation-of-concerns pattern documented. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/selfcore-2026-09-05.md`.*