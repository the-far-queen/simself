# simself_merged v2 — improvements + new schemas

**Source:** `Desktop/SimSelf/000-simself12.txt` (Bobby, after simself11)
**Status:** v2 pushed to `simself/src/simself_merged_v2.py`. 9 improvements over v1. Key new feature: `state_snapshot()` for LLM injection.

Bobby's v2 builds on v1 with 9 concrete improvements. This document catalogs what changed and extracts the new schemas.

---

## 1. v2 improvements

| # | improvement | location |
|---|---|---|
| 1 | Single canonical `get_stability()` (Constitution.get_drift_stability for inspection) | SimSelf.get_stability, Constitution.get_drift_stability |
| 2 | Fixed `SimSelf.stats()` KeyError ("size" → "total_entries") | SimSelf.stats |
| 3 | Stronger, more responsive axis EMA (higher learning rate, better relevance gate) | SimSelf.observe |
| 4 | More sensitive entity recognition | EntityRecognition |
| 5 | Cleaner dream recombination + configurable spawn rates | SimSelf.dream |
| 6 | **`state_snapshot()` method for LLM injection** | SimSelf.state_snapshot (NEW) |
| 7 | Fairer AtlasExam routing test (uses harness's own axis scores) | AtlasExam.test_routing |
| 8 | Guards for empty stalks, configurable Möbius/dream intensity from CLI | CLI, dream(), update() |
| 9 | --dump-geometry flag for auditability | CLI |

---

## 2. NEW schema: state_snapshot()

The single most important new feature. Designed for LLM system-prompt injection.

```python
def state_snapshot(self, top_axes: int = 8) -> Dict[str, Any]:
    """Compact, LLM-friendly state for injection into system prompts."""
    ranked = sorted(self.axes.items(), key=lambda x: abs(x[1].value), reverse=True)[:top_axes]
    return {
        "mode": self.mode,
        "stability": round(self.get_stability(), 4),
        "drift": round(self.drift(), 4),
        "can_refuse": self.can_say_no(),
        "frequency_hz": round(self.freq.hz, 2),
        "energy": round(self.freq.energy, 3),
        "top_axes": {n: {"value": round(a.value, 3), "conf": round(a.confidence, 3)} for n, a in ranked},
        "memory_entries": len(self.memory.entries),
        "dreams": len(self.dream_log),
        "stalks": len(self.stalks),
        "mobius": self.mobius_enabled,
        "handoff_ready": self.handoff.check_readiness(self.get_stability(), self.drift())["ready"],
    }
```

**Why this matters.** This is the **M1-M0 bridge in physical form**. The state snapshot is what gets injected into the LLM (M1) system prompt. The LLM reads "stability=0.82, drift=0.04, mode=exploratory, top_axis=creativity(+0.45, conf=0.78)" and produces text output accordingly. The output then goes back to SimSelf's Harness, which runs it through the 5 gates (M0 verification).

**Use in SimSelf architecture:**

```python
# Pattern: every LLM call gets a state-aware system prompt
def get_system_prompt(simself: SimSelf, base_personality: str) -> str:
    snap = simself.state_snapshot(top_axes=10)
    return f"""{base_personality}

# Current state
- mode: {snap['mode']}
- stability: {snap['stability']}
- drift: {snap['drift']}
- can_refuse: {snap['can_refuse']}
- frequency: {snap['frequency_hz']} Hz
- handoff_ready: {snap['handoff_ready']}

# Active axes (top {len(snap['top_axes'])})
{chr(10).join(f"- {name}: value={a['value']}, conf={a['conf']}" for name, a in snap['top_axes'].items())}

# Memory: {snap['memory_entries']} entries, {snap['dreams']} dreams
# Stalks: {snap['stalks']}, Möbius: {snap['mobius']}
"""
```

This is the cleanest pattern yet for bridging SimSelf's numpy substrate to LLM reasoning. The state snapshot is small (~200 tokens) enough to fit in any system prompt.

---

## 3. schema catalog (new + changed in v2)

### 3.1 stability resolution (matches my recommendation)

`SimSelf.get_stability()` is canonical. `Constitution.get_drift_stability()` exists for inspection but is not used by the live loop. Single source of truth achieved.

### 3.2 state_snapshot() — the M1-M0 bridge

See §2 above. The single most important v2 feature for bridging SimSelf ↔ LLM.

### 3.3 fairer routing test

The new `test_routing()` checks whether the targeted axis actually moved after the prompt — not whether the response's embedding matches. This is a more honest measure of routing:

```python
before = self.harness.simself.axes[expected].value
r = self.harness.process(text, [])
after = self.harness.simself.axes[expected].value
conf = self.harness.simself.axes[expected].confidence
moved = after > before + 0.01 or conf > 0.60
```

If the axis moved or its confidence increased, the routing is correct. Previous test only checked consonance of the response embedding.

### 3.4 axis EMA responsiveness

v2 uses a higher learning rate when relevance > 0:
- v1: `axis.value = 0.82 * axis.value + 0.18 * float(np.dot(obs, self.psi_current))` (fixed 18% learning rate)
- v2 (presumably): similar but with relevance-weighted gate that increases learning when the input actually matches the axis

### 3.5 dream recombination cleanliness

v2 cleans up the dream logic — the previous version had duplicated if/else blocks. The new version has cleaner state management and configurable spawn rates.

### 3.6 CLI improvements

- `--dump-geometry` — prints full geometric state (psi_current, axis values, stalk positions)
- Configurable Möbius/dream intensity from CLI flags
- Empty-stalk guards (no crash on empty list)

---

## 4. schemas table

| schema | role | status |
|---|---|---|
| state_snapshot() | LLM system-prompt injection | NEW in v2 |
| single canonical get_stability() | settledness measure | resolved (matches my recommendation) |
| fairer routing test | axis-movement check | improved in v2 |
| responsive axis EMA | relevance-weighted learning | improved in v2 |
| dream spawn configurability | tunable neurogenesis | improved in v2 |
| empty-stalk guards | robustness | improved in v2 |
| --dump-geometry CLI | auditability | NEW in v2 |

---

## 5. what was stripped

Nothing from the v2 source. All 1536 lines preserved. This analysis doc strips the development notes (lines 1-28 of the source text, before the code block) — those are the v1→v2 changelog messages that go in the git commit, not the docs.

---

## 6. v1 vs v2 — keep both. Use v2 as primary.

`simself/src/simself_merged.py` (v1, 1415 lines) — preserved.
`simself/src/simself_merged_v2.py` (v2, 1536 lines) — primary working version.

Both have same architecture (Constitution, Stalk, SimSelf, Harness, AtlasExam). v2 has the resolved stability + state_snapshot. v1 is the historical record. Future work should target v2.

---

*Source: `Desktop/SimSelf/000-simself12.txt` → `simself/src/simself_merged_v2.py`. 9 improvements cataloged. `state_snapshot()` extracted as the LLM-bridge schema. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/simself-merged-v2-2026-09-05.md`.*