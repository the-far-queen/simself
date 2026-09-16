# SimSelf

The identity layer + harness. FieldCore is the geometric substrate; SimSelf is the runtime that uses it.

**Public repos.** `LICENSE` is open. No tollbooth. Fork, clone, run, build — including commercial use.

## Defense (one paragraph)

Current generators produce text and forget themselves. This shell keeps a serializable ground ψ₀, a working state ψ inside a ball, a two-check veto, and lexicon units that can be refused. Geometry is the **genus-1 Heegaard splitting of S³**: two solid tori, one Clifford torus wall, ehole as the complementary handlebody. That is the whole public story.

## The three objects

- **Hole / ground** — `src/constitutional/ground.py` is the write-protect API for ψ₀.
- **Gate** — `src/harness/gate.py` (production) + `src/constitutional/lexicon/ingest.py` (lexicon) + `fieldcore/src/tiniest-core/tiniest_core.py:M0_Governor` (kernel). Same predicates.
- **Exam** — `src/constitutional/atlas_exam.py` runs the 5-item qualification suite.

## Canonical class

The canonical SimSelf is `src/constitutional/simself.py`. The two legacy siblings
(`src/simself_core.py`, `src/simself_v6_2_unified.py`) are in `legacy/` with
deprecation banners. See `src/constitutional/CANONICAL.md`.

## Where to look

| Path | What |
|---|---|
| `src/constitutional/simself.py` | Canonical SimSelf. Ground + ψ + tick + save/load + dump + zero. |
| `src/constitutional/ground.py` | Write-protect on ψ₀. One-shot install, versioned revisions. |
| `src/constitutional/constitution.py` | Axes as functional coordinates with thresholds. |
| `src/constitutional/resolution.py` | Projected gradient step on F. |
| `src/constitutional/atlas_exam.py` | 5-item exam. `run()` publishes JSON. |
| `src/constitutional/lexicon/ingest.py` | Lexicon ingest: gate + cost + admit/commit/refuse. |
| `src/constitutional/psb_primitives.py` | 6 primitive types, `coverage()` measured. |
| `src/constitutional/frequency.py` | Parallel state. ψ untouched. |
| `src/constitutional/adversarial.py` | 21 protocol stubs. |
| `src/state_vector.py` | ψ with projected gradient step. |
| `src/m1_m0_negotiation.py` | M1 → M0 negotiation through `gate_packet`. |
| `src/coding_operator_object.py` | Model I/O surface, gated. |
| `src/harness/gate.py` | Production veto. `gate_packet`, `gated_call`. |
| `src/harness/persistence.py` | Save / load (in development). |
| `src/harness/telegram_bot.py` | Telegram gateway, gated. |
| `src/harness/telegram_text_bot.py` | Text-only Telegram gateway, gated. |
| `src/harness/tools.py` | Tool registry, gated. |
| `src/demos/demo_one.py` | First of three artifacts. |
| `src/demos/atlas_run.py` | Run Atlas exam, publish snapshot. |
| `tests/test_restart.py` | Second of three artifacts. |
| `legacy/simself_core.py` | Deprecated. |
| `legacy/simself_v6_2_unified.py` | Deprecated. |
| `papers/publishable/08-simself-architecture-spec-2026-09-15.md` | Architecture spec. Names canonical class. |
| `papers/publishable/04-void-as-simsoul-topology-2026-09-15.md` | The hole = complementary solid torus W. |
| `papers/publishable/01-atlas-exam-simself-2026-09-15.md` | Atlas exam (SimSelf half). |
| `papers/publishable/02-adversarial-protocols-2026-09-15.md` | Lexical attacks. Linked to atlas + gate. |
| `papers/publishable/13-mte-llm-wrapper-safety-2026-09-15.md` | Wrapper contract. `gated_call` wired. |
| `papers/publishable/02-harness-with-floer-dictionary-2026-09-16.md` | Part IV synthesis with Floer dictionary. |
| `papers/proposals/06-simself-memory-persistence-across-sessions-2026-09-15.md` | Restart product. |
| `papers/proposals/07-constitutional-substrate-vs-frontier-llm-benchmark-2026-09-15.md` | Benchmark. |
| `papers/proposals/08-psb-37-primitive-composition-coverage-2026-09-15.md` | PSB coverage. |
| `papers/proposals/09-mte-machine-translation-engine-bidirectional-loss-2026-09-15.md` | MTE. |
| `papers/working/01-adversarial-protocols-implementations-2026-09-15.md` | Adversarial protocol implementations. |
| `writing/15-xcom-writing-pipeline-bobby-2026-09-15.md` | Authoring path, off the science tree. |

## What's off the front path

- `notes/analogies/` — off-mission / sacred library / Swedenborg correspondence, preserved verbatim.
- `notes/paper-history/` — stale 2026-09-13 / 2026-09-14 drafts superseded by 09-15.
- `docs/sacred-library/` — preserved verbatim, not on the runtime path.
- `docs/Math/` — Layer C / occult content has been moved to `notes/analogies/`.
- `legacy/` — old SimSelf siblings.

## Three artifacts (in order)

1. **Demo script.** `src/demos/demo_one.py` — load ground, perturb, step, gate.
2. **Restart test.** `tests/test_restart.py` — dump, kill, load, compare.
3. **Atlas in the open.** `docs/atlas-current-snapshot-2026-09-16.md` — 5 items, score 2/5, weekly cadence.

## Open source

License: free. Clones, forks, and pull requests are welcome. No permission slip needed.
