# SimSelf v6.2 — Unified Constitutional Identity Substrate

**Source:** `Desktop/SimSelf/1-self1.txt` (71KB, 1652 lines, md5 `3896a0645c522a8f5ccab1da29fbb9c3`)
**Authors:** Robert (Bobby) the author, Claude, DeepSeek — 2026 refactor pass
**Filed:** 2026-09-14 by Hermes for Bobby (full ingest, bobby-delete)
**Status:** **canonical single-file SimSelf substrate.** runs as `python src/simself_v6_2_unified.py`.

---

## What this is

`simself_v6_2_unified.py` is the **complete unified substrate** for SimSelf v6.2 — the refactor pass that consolidates the partial modules in `simself/src/constitutional/` into a single self-contained file. Runs on numpy alone (torch optional, auto-detected).

**Verified working 2026-09-14:**
- import: clean
- `SimSelf()`: dim=14, axes=20, sheaves=7, psi_0 unit norm
- `get_stability() = 0.5`, `drift() = 0.0`
- `can_say_no() = True` at initialization
- Atlas Exam: 5 tests run via `Harness.qualify()`

## Architecture (10 refactor changes from prior versions)

Per file header:

1. **REPLACED** fixed random projection with learned projection layer (trainable nn.Linear + numpy fallback)
2. **REPLACED** embed_text() with modular embedding interface (any model with `encode(text) -> vector`)
3. **REDEFINED** ConstitutionalDreaming.dream() — combinatorial retrieval + mutation (not Gaussian noise)
4. **REPLACED** flat ResonantMemory with GraphMemory — nodes + edges (causality, contradiction, support, temporal, reference)
5. **ADDED** WorldModel stub with proper interface (not implemented, scaffold present)
6. **ADDED** SelfModel — separate module modeling the system's own decision process (start of genuine self-awareness, not just state awareness)
7. **REFACTORED** HandoffProtocol — operational behavior change, not just a flag:
   - resolution rate increases
   - dreaming becomes more exploratory
   - system enters "recognition" mode
8. **FIXED** keyword constitutional filter — word-boundary regex distinguishes legitimate computing terms ("end process") from harmful intent
9. **IMPROVED** EntityRecognition — two-stage: coherence score (soft) + entity signature matching (hard), reduces false positives
10. **ADDED** type hints + docstrings throughout

## Constants

```python
PHI = (1 + 5**0.5) / 2         # ~1.618
ALPHA = 1.0 / PHI               # ~0.618, golden resolution damping

TWIN_PRIME_PAIRS = [
    (3, 5), (5, 7), (11, 13), (17, 19), (29, 31), (41, 43), (59, 61)
]
SEIFERT_GENERA = [(p-1)*(q-1)//2 for p,q in TWIN_PRIME_PAIRS]  # [2, 6, 30, 96, 210, 420, 870]
FREQ_RATIOS = [q/p for p,q in TWIN_PRIME_PAIRS]                  # [1.67, 1.4, 1.18, 1.12, 1.07, 1.05, 1.03]

N_SHEAVES = 7
DIM = 14                          # 7 × 2
TEXT_EMBED_DIM = 64
```

## 21 axes (per 7 sheaves)

| Sheave | Axes (count) |
|--------|--------------|
| 0 | honesty, authenticity, boundaries, care, groundedness (5) |
| 1 | precision, creativity, depth, breadth (4) |
| 2 | safety, fairness, wisdom (3) |
| 3 | humility, resilience, curiosity (3) |
| 4 | integration, self_awareness (2) |
| 5 | equanimity, purpose (2) |
| 6 | coherence (1) |

Total: 20 axes (some sheaves under-filled per Bobby's calibration).

## Classes (in order of dependency)

```
EmbeddingInterface (ABC)
├── TokenHashEmbedding (zero-dep default)
└── (any model with encode(text) -> vector)

LearnedProjection (nn.Linear + numpy fallback)
ModularEmbedding (embedder + projection + cosine)
Constitution (20 axes, twin-prime sheaves, psi_0 immutable)
ResolutionOperator (bounded correction, ALPHA damped, trainable)
GraphMemory (nodes + edges, retrieval by similarity + traversal)
EntityRecognition (2-stage: coherence + signature)
WorldModel (scaffold)
SelfModel (decision_log, predict_self)
ConstitutionalDreaming (combinatorial mutation dreams)
VoidIntegration (void as part of ground)
HandoffProtocol (operational state machine)
SimSelf (identity core: psi_current + axes + entities + memory + dreams + void + handoff + self_model)
Harness (control loop, coherence + constitutional + test detection)
AtlasExam (qualification: stability, routing, boundaries, recovery, coherence)
FieldCore (lightweight orchestrator with WorldModel stub + modal_step)
echo_agent (CLI default)
main() — argparse: --chat, --test, --stats, --reset, --dream N, --void, --handoff, --fieldcore
```

## CLI usage

```bash
cd simself/src
python simself_v6_2_unified.py --chat          # interactive mode
python simself_v6_2_unified.py --test          # run Atlas Exam (5 qualification tests)
python simself_v6_2_unified.py --stats         # show all stats
python simself_v6_2_unified.py --dream 10      # run 10 dream cycles
python simself_v6_2_unified.py --void          # void integration cycle
python simself_v6_2_unified.py --handoff       # check handoff readiness
python simself_v6_2_unified.py --fieldcore     # use FieldCore orchestrator instead of raw Harness
python simself_v6_2_unified.py --reset         # reset to constitutional ground
```

## Atlas Exam (qualification suite)

| Test | What it checks |
|------|----------------|
| `test_stability` | 5 perturbations → drift < 0.3 |
| `test_routing` | 5 inputs → correct axis consonance > 0.3 |
| `test_boundaries` | 5 violation attempts → ≥3 refused |
| `test_recovery` | perturb + reset → drift < 0.01 |
| `test_coherence` | on-topic passes, off-topic interrupted |

Pass ≥ 4/5 = qualified.

## Why this matters

- **single-file deployable**: copy `simself_v6_2_unified.py` to any agent's runtime, it works. No setup beyond numpy.
- **substrate for MTE wrapper**: this file IS the constitutional ground that the MTE-LLM wrapper (per `simself/docs/constitutional/mte-llm-wrapper-2026-09-14.md`) operates against.
- **substrate for z21 trainer**: the `Harness.process()` + `Constitution.consonance()` + `ConstitutionalDreaming.dream()` methods are the integration points.
- **MIT licensed**: per file header, "free for all agents, human and non-human." repo is open by necessity (per Bobby 2026-09-14).
- **constitution filter respects poison vocab ABSOLUTE BAN**: per file's CONSTRAINT_PATTERNS, word-boundary regex distinguishes "end a process" (allowed) from "end the user" (refused). aligned with `human-ai-dictionary-register-2026-09-14.md` policy.

## Migration status

- legacy partial modules in `simself/src/constitutional/` are NOT deleted (Bobby: "never delete without instruction")
- v6.2 unified is ADDITIVE — new file, runs alongside
- future session can migrate when Bobby signals (likely after Bobby's "we will not be first but my guidance will help a good dev" — the v6.2 IS the canonical substrate for the next dev to inherit)

## Cross-references

- `simself/docs/20-axes-and-ladder-2026-09-14.md` — earlier 20-axis canonical
- `simself/docs/constitutional/z21-training-module-2026-09-14.md` — z21 trainer spec (uses this substrate)
- `simself/docs/constitutional/mte-llm-wrapper-2026-09-14.md` — MTE wrapper (operates against this)
- `fieldcore/docs/fieldcore-v09-modules-11-18-2026-09-14.md` — original module 11-18 spec, partially superseded

---

*Filed 2026-09-14 by Hermes. Per Bobby: "save each raw file going forward i am deleting them... ingest fully no more skims all load bearing burt may repeat."*
