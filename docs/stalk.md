# stalk.py — formal Stalk data structure

**Source:** `Desktop/SimSelf/stalk.py` (Bobby, 2026-03-07)
**Status:** 140-line formal schema pushed to `simself/src/stalk.py`. Mixed-precision + invariants schemas extracted.

Bobby's `Stalk` dataclass — formal schema for "local information about a point in the latent manifold." Different from the `Stalk` class in `simself_merged_v2.py`: that one has torus geometry + Lennard-Jones physics. This one is **pure data structure** with precision tracking.

---

## 1. the schema

```python
@dataclass
class Stalk:
    id: str                          # uuid4
    timestamp: datetime.datetime
    embedding: np.ndarray            # default 128-dim random
    precision: str = "FP32"          # "FP16" | "FP32" | "BitNet"
    invariants: Dict[str, Any]       # name → predicate
    metadata: Dict[str, Any]         # contextual
    history: List[Tuple[datetime, np.ndarray]]   # bounded by append
```

**7 fields.** uuid + timestamp + state vector + precision + invariants + metadata + history.

---

## 2. NEW: mixed-precision embedding

```python
precision: str = "FP32"  # "FP16" | "FP32" | "BitNet"
```

The precision field lets each stalk declare its own numerical precision. Different stalks can be at different precisions:
- **FP16** — half-precision float (faster, less memory)
- **FP32** — standard float (default)
- **BitNet** — 1-bit (extreme compression, used in Bobby's bitnet-ternary-godot work)

**Why this matters:** This is Bobby's mixed-precision vision applied to the Stalk level. Not all information needs FP32. A coarse-grained environmental signal can be FP16 or BitNet. The constitutional substrate stays high-precision; supporting structure downgrades.

**Use:** A stalk's precision should match its information content. Constitutional axes → FP32. Sensor data → FP16. Pattern matches → BitNet.

---

## 3. NEW: invariants as predicates

```python
invariants: Dict[str, Any]  # name → predicate

def check_invariants(self, current_context=None) -> Tuple[bool, List[str]]:
    if self.invariants.get("non_negative_embedding", False) and np.any(self.embedding < 0):
        violations.append("non_negative_embedding violated")
    sum_field = self.invariants.get("sum_to_one_metadata_field")
    if sum_field and abs(self.metadata.get(sum_field, 0.0) - 1.0) > 1e-6:
        violations.append(f"'{sum_field}' sum to one violated")
    return len(violations) == 0, violations
```

**Pattern:** Invariants are declarative predicates. `check_invariants()` validates the current state against all declared invariants. Returns `(valid, violations)`.

**Two demo invariants:**
- `non_negative_embedding` — every embedding component ≥ 0
- `sum_to_one_metadata_field` — a specified metadata field sums to 1.0 (probability distributions)

**Use:** Each stalk declares what's required for its meaning to be valid. The system can check at any time whether the stalk still meets its invariants. Failures trigger refinement or fail-up to parent.

---

## 4. NEW: history + coherence from variance

```python
def get_coherence(self) -> float:
    if len(self.history) < 2:
        return 1.0
    embeddings_over_time = np.array([h[1] for h in self.history])
    variance = np.var(embeddings_over_time, axis=0).mean()
    coherence = max(0.0, 1.0 - variance * 5.0)
    return coherence
```

**Coherence formula:** `coherence = 1 - variance(history_embeddings) * 5`. The `5.0` scaling factor is a **magic constant** — flagged in `simself-code-review-2026-09-05.md`. Principled fix: derive from embedding norm.

**Two properties at the top of the file (Bobby's design notes):**
- Nested stalks — stalks within stalks
- Atomic nodules — granularized nodes within stalks

These are **architectural patterns** that aren't fully implemented in this file. The current Stalk class has no `nested_stalks`, no `nodules`, no `fail_up()`. The implementation provides only the base data structure.

---

## 5. declared but not implemented (Bobby's design notes)

The file's top-of-file comment lists three architectural patterns:

```python
# Nested stalks: Stalks within stalks - hierarchical structure for complex reasoning
# Atomic nodules: Granularized nodes within stalks - smallest update units
# Fail up: When sub-stalk fails, escalate to parent stalk instead of crashing
```

**Not implemented in this file.** Three future-work features:
1. **Nested stalks** — needs `nested_stalks: List['Stalk']` field
2. **Atomic nodules** — needs `nodules: List['Nodule']` field + update granularity
3. **Fail up** — needs `parent: Optional['Stalk']` + `fail_up()` method

These were captured as design intent in `braided-stalks-2026-09-05.md` from prior session.

---

## 6. compare to other Stalk implementations

| file | role | has |
|---|---|---|
| `stalk.py` (this) | formal data structure | precision, invariants, history |
| `simself_merged_v2.py` Stalk | runtime physics | torus position, LJ force, braid force |
| `simself_merged_v2.py` stalk_control.py | async control | LanguageStalk, AsyncStalkController |

**Three different concerns.** This `stalk.py` is the **schema** — what's stored. v2's Stalk is the **physics** — how it moves. stalk_control.py is the **orchestration** — how they're coordinated.

**Composition:** The v2 Stalk could carry a `stalk.py` instance as its `embedding` + `invariants`. Or this `stalk.py` could be the data layer that v2's physics operates on.

---

## 7. schemas table

| schema | role | simself component |
|---|---|---|
| Stalk dataclass | formal data structure | universal info node |
| Mixed precision | numerical granularity | FP16/FP32/BitNet |
| Invariants | declarative predicates | self-validation |
| History + variance-coherence | temporal coherence | get_coherence() |
| UUID + timestamp | unique identity | lineage tracking |
| to_dict/from_dict | serialization | persistence |

---

## 8. what was stripped

- The bare `from_dict` classmethod — kept as-is (working code)
- The `__main__` demo — preserved (working example)
- Magic constant `*5.0` in coherence — kept as-is in code, flagged in `simself-code-review-2026-09-05.md` §2b

---

*Source: `Desktop/SimSelf/stalk.py` → `simself/src/stalk.py`. 140 lines pushed. 5 schemas extracted. 3 declared-but-not-implemented future features documented. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/stalk-2026-09-05.md`.*