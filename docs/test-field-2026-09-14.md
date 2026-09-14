# SimSelf Tests — test_field.py (Aspirational Modular API)

**Source:** `Desktop/SimSelf/tests/test_field.py` (3.5KB, 144 lines, md5 `205c938a7a0382d478c54920e356a499`)
**Filed:** 2026-09-14 by Hermes for Bobby (full ingest, bobby deleting)
**Status:** **aspirational test suite** — shows intended modular API; tests FAIL today because target modules don't exist

---

## Critical observation

This test file imports:
```python
from field.core import InfoPacket, InformationField
from agent.core import SimSelf, Governor
```

**Neither `simself/src/field/` nor `simself/src/agent/` exists.** Neither `field.core.InfoPacket` nor `agent.core.SimSelf` is implemented in the current canonical codebase.

What this test file IS:
- **forward-looking API spec** — what Bobby's modular architecture intends
- **falsifiable interface contract** — the test names exactly what each module must expose

What this test file IS NOT:
- **NOT runnable today** — would fail at import time
- **NOT canonical** — the current canonical substrate is `simself_v6_2_unified.py` (which has its own InfoPacket via `EmbeddingInterface`, its own SimSelf, its own Governor)

---

## The 5 tests

### Test 1: `test_info_packet()` — InfoPacket creation + similarity

```python
def test_info_packet():
    packet = InfoPacket(id="test1", embedding=np.array([1.0, 0.0, 0.0]), metadata={"type": "test"})
    assert packet.id == "test1"
    assert len(packet.embedding) == 3
    similarity = packet.similarity(packet2)
    assert similarity > 0.9
```

**Expected API:** `InfoPacket` with `.id`, `.embedding`, `.metadata`, and `.similarity(other)` method.

**Already exists in:** `simself_v6_2_unified.py` → `EmbeddingInterface.encode(text) → np.ndarray` (but not InfoPacket dataclass). Also in `fieldcore/src/tiniest-core/tiniest_core.py` and `_v6_2` sketch. The full InfoPacket dataclass with `.similarity()` method needs to be imported or extracted.

### Test 2: `test_information_field()` — graph + radius query

```python
def test_information_field():
    field = InformationField(embedding_dim=8)
    p1 = InfoPacket(id="1", embedding=np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), metadata={})
    field.add(p1)
    results = field.query(np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), radius=0.5)
    assert len(results) >= 1
```

**Expected API:** `InformationField(embedding_dim=N)` with `.add(packet)`, `.query(center, radius) → list[InfoPacket]`.

**Already exists in:** `simself_v6_2_unified.py` → `GraphMemory` (similar shape: nodes + edges, retrieval by similarity + graph traversal). Could be renamed/aliased to `InformationField` with a `.query()` method.

### Test 3: `test_sim_self()` — SimSelf update + coherence + novelty

```python
def test_sim_self():
    sim = SimSelf(dim=8, initial_coherence=0.5)
    sim.update({"touch": 0.8})
    assert sim.coherence > 0
    assert len(sim.embedding) == 8
    novelty = sim.get_novelty()
    assert novelty >= 0
```

**Expected API:** `SimSelf(dim=N, initial_coherence=0.5)` with `.update(sensors: dict)`, `.coherence` (property), `.embedding` (property), `.get_novelty() → float`.

**Already exists in:** `simself_v6_2_unified.py` → `SimSelf(dim=14)` (dim hardcoded from N_SHEAVES × 2). The v6.2 `get_stability()` ≈ `coherence`, and `drift()` ≈ `novelty`. Mapping needed.

### Test 4: `test_governor()` — invariant enforcement

```python
def test_governor():
    gov = Governor(max_norm=4.0, min_coherence=0.45)
    good_state = {"coherence": 0.6, "embedding": np.array([1.0, 0.0, 0.0])}
    result = gov.check(good_state)
    assert result["allowed"] == True
    bad_state = {"coherence": 0.3, "embedding": np.array([1.0, 0.0, 0.0])}
    result = gov.check(bad_state)
    assert result["allowed"] == False
    bad_action = {"type": "delete_everything"}
    result = gov.check(good_state, bad_action)
    assert result["allowed"] == False
```

**Expected API:** `Governor(max_norm, min_coherence)` with `.check(state, action=None) → {allowed: bool, reason: str}`.

**Already exists in:** `simself_v6_2_unified.py` → `Governor` exists in `constitutional/` (legacy) with similar interface. Plus `simself/m1_m0_negotiation.py` M0 reality-layer has `enforce()` method with `(passed, violation_details)` return. The two need to be unified.

### Test 5: `test_full_loop()` — end-to-end

```python
def test_full_loop():
    field = InformationField(embedding_dim=8)
    sim = SimSelf(dim=8)
    gov = Governor()
    # ... 5 packets, sim.update, gov.check
    assert result["allowed"] == True
```

**Wires the 4 modules together.** This is the integration test that proves the modular architecture is composable.

---

## Cross-reference: matches the canonical fieldcore-v0.9 spec

Per `fieldcore/docs/fieldcore-v09-modules-11-18-2026-09-14.md` (Bobby's modular architecture spec, ingested earlier this turn):

| Module (v0.9 spec) | Class in this test | Notes |
|--------------------|---------------------|-------|
| Module 11: PSBs | (no test) | primitives |
| Module 12: Language | (no test) | MTE |
| Module 13: Reasoning | (no test) | reasoning operator |
| Module 14: Learning | (no test) | training |
| Module 15: Ingestion | (no test) | knowledge extraction |
| Module 16: Tool use | (no test) | n8n |
| Module 17: Multi-self | `InformationField` + `SimSelf` (basic) | nodes + self-model |
| Module 18: Governor | `Governor` | invariant enforcement |

**Tests 1-5 cover Module 17 (multi-self with field) + Module 18 (governor).** Tests for Modules 11-16 are missing.

---

## What's needed to make this runnable

1. **Create `simself/src/field/__init__.py` + `core.py`** with `InfoPacket` + `InformationField` classes
2. **Create `simself/src/agent/__init__.py` + `core.py`** with `SimSelf` + `Governor` classes
3. **Either:**
   - (a) **port from v6.2 unified** — extract `GraphMemory` → `field.core.InformationField`, extract `SimSelf` from v6.2 → `agent.core.SimSelf`
   - (b) **port from tiniest_core.py** — the tiniest-core has the same shape (5/5 tests pass on it)
   - (c) **write from scratch** — using the test as the spec

Per Bobby's directive (continue ingesting, not recreate wheel, not run fc yet): option (a) or (b) is canonical.

---

## Why this file is load-bearing

- **5 tests** that define the modular architecture API
- **falsifiable** — each test runs in <1s, gives pass/fail
- **composable** — test 5 (full loop) proves the modules work together
- **forward-looking** — when implemented, gives simself a clean test suite for regression detection

**without this file, simself has no automated test coverage** (only `constitutional/test_frequency_layer.py` is a test, and it's not run via pytest).

---

## Where this file should land

**decision (per Bobby's refactor-clean autonomy):**
- save raw verbatim ✅ done (vault/30-originals/simself-test-field-original-2026-09-14.md)
- canonical .py: `simself/tests/test_field.py` (NEW dir, additive, mirrors source path)
- canonical doc: this file (simself/docs/test-field-2026-09-14.md)
- implementation pending — module stubs need to be created

---

*Filed 2026-09-14 by Hermes for Bobby. Per Bobby: "save each raw file going forward i am deleting them... ingest fully no more skims."*

*This file IS the aspirational test suite for the modular architecture. Tests currently fail (modules don't exist). The contract is clear.*
