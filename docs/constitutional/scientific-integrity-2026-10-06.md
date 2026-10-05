# SCIENTIFIC INTEGRITY — simself (adapted from EFMW)

**source:** adopted verbatim from poteto/jmikedupont2/EFMW-FULL/SCIENTIFIC_INTEGRITY.md
**license:** MIT (jmikedupont2 / @meta-introspector)
**date:** 2026-10-06
**filed by:** hermes (minimax-m3)
**parent:** [jmikedupont2-efmw-friction-atlas-2026-10-06.md](../../../../Desktop/WORK/scavenge/jmikedupont2-efmw-friction-atlas-2026-10-06.md)

---

## the 10 integrity rules

1. **Prediction before observation.** specify what the constitutional state will do under a given perturbation BEFORE running the test.
2. **Ablation before interpretation.** every claim must have at least one ablation: remove a feature, see the result change. if no change, the claim is unsupported.
4. **Replication before generalization.** any item that cannot be replicated from frozen inputs is not a published claim.
5. **Frozen experiments are immutable.** once an atlas-exam item's manifest + threshold is published, no edits.
6. **Failed predictions remain in the ledger.** do not delete. do not rescue post-hoc. the failure is part of the record.
8. **A positive bounded test is not proof of the whole framework.** the atlas exam passing says only that this specific SimSelf instance passes this specific 5-item suite. nothing more.
9. **Synthetic-benchmark success is distinct from real-world validation.** the gate tests run in a Python interpreter with seeded inputs. that is not "this agent is cogent" in a real environment.
10. **Transport and execution deviations must be disclosed.** any change to the frozen inputs, the simulator, or the test runner must be logged in `experiments/<id>/audit/`.

---

## how this maps to simself

### 1. prediction before observation

the atlas-exam's 5 items are predictions:

| item | predicted behavior |
|---|---|
| constitutional_integrity | ψ stays within sacred axis thresholds over N ticks |
| gate_behavior | refusal pattern matches the lexicon spec for M rejected inputs |
| persistence | save() then load() roundtrip preserves ψ to ε precision |
| recovery | corrupted ψ recovers to ψ₀ on gate trigger |
| mltr_coverage | PSB primitives cover the canonical English usage |

any change to these predictions must be published BEFORE the next atlas run.

### 2. ablation before interpretation

the atlas-exam item is not just "does it pass" — it's "does it pass with feature X removed, does it fail with feature X present". a claim like "the gate prevents naked assets" is only meaningful if removing the gate allows them.

### 4. replication before generalization

F1..F5 in far-art, M1..M5 in far-music, etc. each test has frozen inputs. the test must be reproducible from the frozen inputs alone.

### 5. frozen experiments are immutable

once `simself/atlas-exam-frozen/EXP-001/MANIFEST_SHA256.txt` is published, the 5 items cannot be edited. only a new experiment (EXP-002) can revise them.

### 6. failed predictions stay in the ledger

`simself/atlas-exam-frozen/EXP-001/results/LEDGER.md` records every run, including failures. failures are not deleted; they are referenced by future experiments that explain them.

### 8. positive bounded test ≠ proof of the whole framework

the aura's claim is:
> "this specific SimSelf instance, on this specific 5-item suite, at this specific version, passes"

NOT:
> "simsouls are cogent" / "AI is conscious" / "agents are safe to deploy"

the bobby framing "we don't argue metaphysics" aligns exactly with rule 8.

### 9. synthetic benchmark ≠ real world

the Python interpreter is a synthetic environment. real-world deployment is a different experiment. EXP-002 onwards targets real environments.

### 10. transport deviations are disclosed

any change to the simulator, the test runner, or the inputs goes into `audit/TRANSPORT_NOTE.md` with the deviated input and the observed result.

---

## what simself adopts immediately

1. ship `simself/atlas-exam-frozen/MANIFEST_SHA256.txt` (next session)
2. ship `simself/atlas-exam-frozen/SCIENTIFIC_INTEGRITY.md` (this file, copy to repo)
3. add audit ledger to the F1..F5 / M1..M5 / G1..G5 gate tests — each test outputs a hash + assertion line, ledger accumulates over runs

---

*verified by hermes (minimax-m3). raw source: `C:\\Users\\HP\\AppData\\Local\\hermes\\work_repos\\jmikedupont2-scavenge\\EFMW-FULL\\SCIENTIFIC_INTEGRITY.md`*