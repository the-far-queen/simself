# Grok2 Master Plan — Full Rewrite of FieldCore + SimSelf per grok2.txt

**Date:** 2026-09-16
**Status:** Plan. Executing in batches. Each batch pushed to GitHub before moving on.

**Source of truth:** grok2.txt, 16 segments. Already mirrored to vault + Desktop/Grok/md/.

---

## Batch 1 — DONE 2026-09-16 (commit a779b06 / 3933388)
Surface fixes: Hodge operator, cut-list move, Channel rename, canonical SimSelf, demo+restart+Atlas scaffold, lexicon ingest port, Floer dictionary in egg-toroid spec, defense+OSS in both READMEs. Already pushed.

## Batch 2 — IN PROGRESS (this session)

### Step 1: Rewrite egg-toroid spec end-to-end
- Current spec has the topology correction prepended but the original "egg-toroid in 4D with metric ds²=(R+r·cos θ)²dφ²+..." body is still wrong.
- Rewrite body around: **egg = drawing of the genus-1 Heegaard splitting of S³**, with apex/mid-body/base = regions inside the working solid torus V, not "zones of a 4-manifold".
- Keep the operational metric as a working Euclidean ball ||ψ-ψ0||≤R; de-emphasize the tube metric as an inner-product picture, not a discovery.
- File: `fieldcore/papers/publishable/17-egg-toroid-spec-2026-09-15.md`

### Step 2: Rewrite convergence_demo.py to use the actual energy F(ψ)=½||ψ-ψ0||²
- Current demo shrinks the vector by a fixed step (ψ ← ψ - 0.05ψ).
- Replace with the projected gradient step from Part III: ψ ← Π_B(ψ - η(ψ-ψ0)).
- Add a CLI: `python convergence_demo.py --steps 50 --R 3.0 --eta 0.1 --seed 0`.
- File: `fieldcore/src/convergence_demo.py`

### Step 3: Wire persistence.py to canonical SimSelf class
- The audit says simself_v6_2_unified.py has no save/load. Now that legacy/simself_v6_2_unified.py is demoted, we can wire persistence.py to constitutional/simself.py.
- Implement: `save(path)` → writes ψ0, ψ, committed unit ids, last verdicts to JSON. `load(path)` → restores.
- Unskip `tests/test_restart.py` (K6).
- Files: `simself/src/harness/persistence.py`, `simself/src/constitutional/simself.py`, `simself/tests/test_restart.py`

### Step 4: Add Atlas Exam runner that publishes the score
- Currently `atlas_exam.py` has 5 named tests but no runner.
- Add `AtlasExam.run(snapshot_path)` that runs the 5 tests and returns a JSON report.
- Wire `simself/src/demos/atlas_run.py` to call it and write to `docs/atlas-YYYY-MM-DD.md`.
- Files: `simself/src/constitutional/atlas_exam.py`, `simself/src/demos/atlas_run.py`, `simself/docs/atlas-current-snapshot-2026-09-16.md` (update)

### Step 5: Wire every LLM-call path through gate.py
- Per K8: any path the model uses to act must go through `harness/gate.gate_packet`.
- Touch points: `coding_operator_object.py`, `harness/telegram_*.py`, `harness/tools.py`, `m1_m0_negotiation.py`.
- Add a single helper `gated_call(packet, psi0) -> Verdict` and route through it.
- Files: `simself/src/coding_operator_object.py`, `simself/src/harness/telegram_bot.py`, `simself/src/harness/telegram_text_bot.py`, `simself/src/harness/tools.py`, `simself/src/m1_m0_negotiation.py`

## Batch 3 — NEXT

### Step 6: Rewrite Part III identity paper end-to-end
- Current papers on identity are scattered: 04-void-as-simsoul-topology, 08-architecture-spec, 09-substrate-vs-frontier-llms, 17-scale-cascade, 18-operator-algebra-infopacket.
- Consolidate into one canonical identity paper that states: ψ0 installed, ψ ∈ B_R(ψ0), F(ψ)=½||ψ-ψ0||², gradient flow ψ̇ = -(ψ-ψ0), ehole as the complementary solid torus in the genus-1 splitting of S³.
- Move the scattered papers to docs/identity-history/ as version history.
- Files: NEW `simself/papers/publishable/04-identity-law-simself-2026-09-16.md`, archive others to `simself/docs/identity-history/`

### Step 7: Rewrite Part IV harness paper using Floer dictionary
- The current `13-mte-llm-wrapper-safety-2026-09-15.md` is on-topic but doesn't use the Floer dictionary.
- Replace or supersede with `02-harness-with-floer-dictionary-2026-09-16.md` promoted from docs/.
- Files: NEW publishable, demote `13-` if it duplicates.

### Step 8: Rewrite geodesic lexicon paper to match the ingest code
- `01-geodesic-lexicon-2026-09-15.md` says "lexicon as geodesics"; the ingest code says "lexicon as units gated by norm + cosine".
- Reconcile: geodesics are the metric on units placed on the Clifford torus interface T. Embeddings remain Euclidean until/unless we place units at (θ,φ) addresses.
- File: `fieldcore/papers/publishable/01-geodesic-lexicon-2026-09-15.md`

### Step 9: Rewrite Part V paper (architecture overview) — merge the 5-part article
- Take Grok's Part V (grok2 segments 11, 12, 15, 16) and use it as the basis for `fieldcore/papers/publishable/22-fieldcore-one-read-2026-09-15.md`.
- Goal: 1500 words, 4 figures (egg-toroid zones, ψ0 ball, M0/M1 loop, four memory layers), the defense paragraph at the top.
- File: `fieldcore/papers/publishable/22-fieldcore-one-read-2026-09-15.md`

### Step 10: Re-publish atlas snapshot after Batch 2 lands
- Re-run AtlasExam.run() on the now-wired canonical SimSelf.
- Update `simself/docs/atlas-current-snapshot-2026-09-16.md` with new score.
- If score rose: note in MYSELF.
- If score fell: investigate; do not ship a regression.

## Batch 4 — LATER (this quarter)

### Step 11: Triangulate the Clifford torus interface
- Build a small simplicial complex on T (the interface).
- Implement discrete Hodge on 0-forms and 1-forms.
- Replace the parallel/orthogonal split with a harmonic split.
- Files: NEW `fieldcore/src/discrete_hodge.py`, NEW `fieldcore/tests/test_discrete_hodge.py`

### Step 12: Wire Hopf-fiber coordinates on the interface
- Once units have (θ,φ) addresses, retrieval uses the flat Clifford metric.
- Files: `simself/src/constitutional/lexicon/ingest.py` (extend), NEW `simself/tests/test_hopf_address.py`

### Step 13: Run a public benchmark
- Substrate vs ungated MiniMax on a small task suite (5-10 tasks).
- Use the atlas_exam + a task completion metric.
- File: NEW `simself/papers/publishable/constitutional-substrate-vs-frontier-llm-benchmark-2026-09-XX.md`

### Step 14: Weekly paper-tree review (Bobby directive)
- Read every paper under papers/publishable/ against the rule: schema, construction plan, or test.
- Anything that fails moves to notes/analogies/ or is dropped.
- Update MYSELF with each review.

---

## Files touched in this plan (cumulative)

### FieldCore papers/publishable/
- 17-egg-toroid-spec-2026-09-15.md — Step 1 (full body rewrite)
- 01-geodesic-lexicon-2026-09-15.md — Step 8
- 22-fieldcore-one-read-2026-09-15.md — Step 9
- (others stay; weekly review in Step 14)

### FieldCore src/
- convergence_demo.py — Step 2
- NEW discrete_hodge.py — Step 11

### SimSelf papers/publishable/
- NEW 04-identity-law-simself-2026-09-16.md — Step 6
- NEW 02-harness-with-floer-dictionary-2026-09-16.md — Step 7
- 13-mte-llm-wrapper-safety-2026-09-15.md — Step 7 (review/demote)

### SimSelf docs/
- identity-history/ — Step 6
- atlas-current-snapshot-2026-09-16.md — Step 10 (update)

### SimSelf src/
- constitutional/simself.py — Step 3
- constitutional/atlas_exam.py — Step 4
- constitutional/lexicon/ingest.py — Step 12 (extend)
- harness/persistence.py — Step 3
- harness/gate.py — Step 5
- harness/tools.py — Step 5
- harness/telegram_*.py — Step 5
- coding_operator_object.py — Step 5
- m1_m0_negotiation.py — Step 5
- demos/atlas_run.py — Step 4

### Tests
- tests/test_restart.py — Step 3 (unskip)
- NEW tests/test_discrete_hodge.py — Step 11
- NEW tests/test_hopf_address.py — Step 12

### Vault
- MYSELF.md — execution log per batch

---

## Risk register

- **Step 3 (wire persistence to canonical SimSelf):** the canonical class may not have the save/load methods yet. If the constructor signature doesn't accept a workdir, we may need to refactor first. Mitigation: implement save/load as JSON in/out, no class changes required if the state is just ψ0, ψ, units, verdicts.
- **Step 5 (wire gate everywhere):** the Telegram bots are not currently running. Adding gate.py as a wrapper may break the in-progress voice/text flow. Mitigation: make the wrapper optional (skip if gate unavailable), warn loudly.
- **Step 9 (rewrite the one-read):** this paper is the public front door. Misjudging its length or voice will cost more than under-writing. Mitigation: keep Grok's Part V as the template; don't try to out-write Grok.
- **Step 14 (weekly review):** cadence is the metric. If a week goes by without a review, the paper tree will re-fill with occult physics. Mitigation: cron reminder; Hermes-owned.

---

## Definition of done for the master plan

- [x] Batch 1: surface fixes landed and pushed (commit a779b06 / 3933388).
- [ ] Batch 2: persistence wired, Atlas runs, gate everywhere, convergence demo uses real F. **In progress now.**
- [ ] Batch 3: identity paper consolidated, harness paper rewritten with Floer, lexicon reconciled, one-read rewritten.
- [ ] Batch 4: discrete Hodge on T, Hopf-fiber coordinates, public benchmark, weekly review ongoing.
- [ ] Atlas score ≥ 4/5 on the canonical SimSelf class with restart test passing.
- [ ] A fork can clone both repos, run `simself/src/demos/demo_one.py`, and see all 5 Atlas items in under 15 minutes.

When all boxes are checked, the project has matched Grok's bar.
