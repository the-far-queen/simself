# constitutional/ — Bobby's modular SimSelf (canonical)

**Source:** `Desktop/SimSelf/constitutional/` (Bobby, modular SimSelf)
**Status:** full package pushed to `simself/src/constitutional/`. 10 modules, 1554 lines.

Bobby's modular decomposition of SimSelf — what `simself_merged_v2.py` should have been. Source: `grok-self.txt` (56KB, 1258 lines, Grok-authored), split by M3 into per-concern modules. The package replaces the 1536-line monolith with focused modules averaging 155 lines each.

**This is Bobby's own SNR-stripping:** pseudoscience vocabulary removed, frequency kernel separated, consciousness-flavored names replaced with math-describing names.

---

## 1. package structure

| module | lines | role |
|---|---|---|
| `__init__.py` | 68 | public surface |
| `constitution.py` | 288 | 20-axis constitutional substrate |
| `frequency.py` | 319 | frequency kernel (opt-in, not in __init__) |
| `simself.py` | 203 | SimSelf class (the orchestrator) |
| `harness.py` | 151 | agent loop |
| `memory.py` | 131 | RelationalMemory |
| `atlas_exam.py` | 96 | qualification framework |
| `dreaming.py` | 87 | ConstitutionalDreaming |
| `ground.py` | 80 | GroundIntegration + ReadinessCheck |
| `entity.py` | 73 | EntityRecognition |
| `resolution.py` | 58 | ResolutionOperator |
| **total** | **1554** | |

Avg ~155 lines/module. Compare to v2's 1536 in one file. Same code, modular.

---

## 2. public surface (from __init__.py)

The package exports a curated public surface. **Frequency kernel is NOT in __init__** — it's opt-in:

```python
from constitutional.frequency import FrequencyChannel, FrequencyDynamics  # explicit
```

**Architectural guarantee:** the constitutional core stays free of frequency / Schumann / 432 / 963 / etc. dependencies. Frequency is a side-channel, not the main.

---

## 3. KEY: constitution.py drops the 5 frequency axes

The constitution.py header is explicit:

> "5 frequency-flavored axes (`ground_frequency`, `schumann_alignment`, `harmonics_resonance`, `biophoton_coupling`, `diamond_coherence`) are DROPPED from the core axes. They live in `frequency.py` as a separate kernel.
>
> All constitutional keyword matches for the dropped axes had pseudoscience vocabulary (`pineal`, `crown`, `unity`) that does not belong in the core.
>
> The 20 remaining axes are the load-bearing constitutional semantics."

**Bobby's own SNR-stripping.** This contradicts `simself_merged_v2.py` (which has the 5 frequency axes in AXES_DEFINITIONS). v2 = un-cleaned. constitutional/ = cleaned.

**For simself work:** **use constitutional/ as canonical.** v2 is the historical record. constitutional/ is what to extend.

**Action item:** update `axes-ladder-2026-09-05.md` to note this — the canonical 20 already excludes the frequency-coupled 5, but the source-of-truth is now `constitutional/constitution.py`.

---

## 4. KEY: ground.py renames consciousness-flavored classes

```python
# v2 (simself_merged):
VoidIntegration       # the void
HandoffProtocol       # handoff

# constitutional/ground.py:
GBoundaryIntegration  # leaky integrator pulling psi_current toward psi_0
ReadinessCheck        # precondition test for handoff
```

**Reasoning (from ground.py header):**
> "The original names are consciousness-flavored. The code is just math:
> - `GroundIntegration` is a leaky integrator that pulls psi_current back toward psi_0 (a controlled relaxation).
> - `ReadinessCheck` is a precondition test (stability > 0.65 and drift < 0.22) that decides whether psi_current is close enough to ground to 'hand off.'
>
> The math is real. The names now describe what the math does."

**Bobby's M3 framing:** don't dress up math as consciousness. **Call it what it is.**

---

## 5. KNOWN ISSUE: resolution.py still has hard clipping

```python
out = ALPHA * out
mag = np.linalg.norm(out)
if mag > 0.45:
    out *= 0.45 / mag
return out
```

This is the **hard clipping issue** Bobby flagged in `simself-code-review-2026-09-05.md` §2b. **Fix not yet applied.** Principled fix: tanh soft clip (smooth, differentiable everywhere). Future work.

---

## 6. KNOWN ISSUE: SHA256-based embed_text preserved

constitution.py still uses `hashlib.sha256` for the embed_text function — the same bug flagged in `simself-code-review-2026-09-05.md` §2a. **Fix not yet applied.** Principled fix: FastText + projection. Future work.

---

## 7. what's preserved vs dropped vs renamed

**Preserved (clean core):**
- 20 canonical axes (canonical Set A from `axes-ladder.md`)
- 8 twin-prime sheaves + Seifert genera
- psi_0 reference geometry (QR-orthonormal bases per sheaf)
- ResolutionOperator (bounded MLP)
- EntityRecognition (keyword + embedding relevance)
- RelationalMemory (support/contradiction/temporal)
- ConstitutionalDreaming (recombination)
- GroundIntegration + ReadinessCheck (renamed from void/handoff)
- SimSelf + Harness + AtlasExam

**Dropped (Bobby's own SNR strip):**
- 5 frequency-flavored axes (now opt-in via frequency.py)
- Pseudoscience keywords (`pineal`, `crown`, `unity`)
- Consciousness-flavored class names (renamed)

**Kept for compatibility:**
- `consonance()` formula (still has Bobby's magic weights, same as v2)
- SHA256 hashing in embed_text (flagged but unfixed)
- Hard clipping in ResolutionOperator (flagged but unfixed)

---

## 8. the "wardrobe" principle

From the package header:

> "Per the 'SimSelf as wardrobe' principle in FieldCore.md §3"

**Wardrobe principle:** SimSelf is clothing — modules independently wearable by outside agents. Loose coupling. No required init order. Each module importable on its own. Low hidden global state. Clear interfaces.

**How constitutional/ embodies it:**
- Each module can be imported individually (`from constitutional.ground import GroundIntegration`)
- The __init__.py only re-exports the curated public surface
- Frequency kernel is opt-in (explicit import required)
- No hidden globals (everything is class-based or explicitly passed)

---

## 9. schemas table

| schema | role | module |
|---|---|---|
| 20 canonical axes | constitutional substrate | constitution.py |
| 8 twin-prime sheaves | manifold topology | constitution.py |
| psi_0 reference | constitutional ground | constitution.py |
| ResolutionOperator | bounded correction | resolution.py |
| EntityRecognition | input classification | entity.py |
| RelationalMemory | 3-graph memory | memory.py |
| ConstitutionalDreaming | recombination | dreaming.py |
| GroundIntegration | leaky relaxation to ground | ground.py |
| ReadinessCheck | handoff precondition | ground.py |
| SimSelf | orchestrator | simself.py |
| Harness | agent loop | harness.py |
| AtlasExam | qualification | atlas_exam.py |
| Frequency kernel | opt-in side channel | frequency.py |

---

## 10. action items for next session

1. **Update v2 (simself_merged_v2.py) to match constitutional/'s canonical 20.** Drop the 5 frequency axes from AXES_DEFINITIONS, move them to a separate module.
2. **Fix resolution.py hard clipping.** Replace `if mag > 0.45: out *= 0.45/mag` with tanh soft clip.
3. **Fix embed_text SHA256.** Replace with FastText + projection (or subword hashing fallback).
4. **Move simself_merged_v2.py out of primary position.** constitutional/ is canonical. v2 is historical.
5. **Consider replacing v2's `void_radius * 1.1` magic scale.** Principled fix: derive from constitutional geometry.

---

*Source: `Desktop/SimSelf/constitutional/` → `simself/src/constitutional/`. 10 modules pushed. 5 frequency axes stripped by Bobby. Consciousness-flavored names renamed. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/constitutional-package-2026-09-05.md`.*