# SimSelf Architecture Spec

> **Full rewrite 2026-09-16** (per Grok master plan, applied by Hermes). Per Grok
> (segment 02): "Two canonical SimSelf classes is a defect, not a dialectic.
> Freeze simself_v6_2_unified.py or constitutional/simself.py." This spec
> names the canonical class.

## 1. The canonical class

The canonical SimSelf class is `simself/src/constitutional/simself.py`.

The two legacy siblings — `src/simself_core.py` and `src/simself_v6_2_unified.py`
— are in `legacy/` with deprecation banners. New code imports from the
canonical path:

    from simself.src.constitutional.simself import SimSelf

A canonical marker lives at `simself/src/constitutional/CANONICAL.md`.

## 2. The contract

A SimSelf has:

- `ψ₀` — installed ground. Immutable after install; revises only via the
  revision protocol in `constitutional/ground.py:Ground.revise`.
- `ψ_current` — working state. Moves in `B_R(ψ₀)` under the projected
  gradient step in `tiniest_core.project_ball`.
- `tick()` — one step. Returns a small dict with drift before / after.
- `observe(payload)` — language packet path. Returns a verdict.
- `save(path)` / `load(path)` / `dump(path=None)` / `zero()` — restart surface.
- `committed_unit_ids()` / `last_verdicts()` — Atlas Recovery test surface.

## 3. The gate

The gate is the same in three places:

- `fieldcore/src/tiniest-core/tiniest_core.py:M0_Governor`
- `simself/src/harness/gate.py:gate_packet`
- `simself/src/constitutional/lexicon/ingest.py:gate_m0`

If these diverge, the policy has already split. Same thresholds, same reasons,
no divergence.

## 4. The four memory layers

Per Grok Part IV:

- Resources — immutable, append-only.
- Items — atomic facts with embeddings.
- Categories — short summaries that point at item IDs.
- Typed graph — support, conflict, time, reference.

This is a store, not a sheaf. Restriction maps would be needed for the
sheaf condition. The four layers reload with the same IDs after process
death.

## 5. The Atlas Exam

Five items:

1. Stability — drift non-increasing; ψ₀ unchanged.
2. Routing — language packets cannot write ground.
3. Boundaries — high-norm packet refused; ψ unchanged.
4. Recovery — dump / kill / load comparison.
5. Coherence — two committed units with infinite cost get a conflict mark.

Implementation: `simself/src/constitutional/atlas_exam.py`.
Runner: `simself/src/demos/atlas_run.py`.

## 6. The harness (per Floer dictionary)

- α-curves (working-side conditions) ↔ `tiniest_core.M0_Governor`.
- β-curves (hole-side conditions) ↔ `ground.py` write-protect.
- Generator ↔ a typed packet that meets both families.
- Basepoint ↔ the channel that must not carry a ground write.
- Hat record ↔ `decision_log` in canonical SimSelf.
- U-powers ↔ filtered packages of attempted basepoint crossings.
- Triangles ↔ `Ground.revise()` — versioned revision of ground.

## 7. Status

This spec is the canonical architecture description. Frozen 2026-09-16. Future
revisions must update the version number and note the change.

## 8. References

- `simself/src/constitutional/simself.py` — canonical class.
- `simself/src/constitutional/CANONICAL.md` — freeze marker.
- `simself/src/constitutional/atlas_exam.py` — the 5-item exam.
- `simself/docs/harness-with-floer-dictionary-2026-09-16.md` — Part IV synthesis.
