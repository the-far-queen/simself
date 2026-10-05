---
name: frozen-experiment-discipline
description: >-
  Use when the user wants to run, freeze, audit, or replicate a simself experiment with
  EFMW-style discipline. Triggers: "frozen experiment", "MANIFEST_SHA256", "audit ledger",
  "scientific integrity", "EFMW", "replicate before self-dictate".
---

# Frozen experiment discipline (EFMW-style)

the EFMW program (jmikedupont2, MIT) ships a frozen-experiment discipline that simself adopts verbatim. **prediction before observation. ablation before interpretation. replication before generalization. frozen experiments are immutable. failed predictions stay in the ledger.**

## when to use

any time you want to:
- run the 5-item atlas exam (commit-frozen version)
- add a new gate test (F1..F5 / M1..M5 / G1..G5)
- publish a new far-* pipeline schema
- audit an existing test against drift

## workflow

1. **predict first.** specify the expected behavior in the test docstring:
   ```python
   def test_F1_repro_id():
       """F1: same axes -> same id; different axes -> different id.

       predicted:
         - 100% match for repeated input
         - 100% distinct for varied input
         - deterministic across python versions
       """
   ```
2. **ablate.** every test should have a corresponding failure case:
   ```python
   def test_F1_ablate():
       """F1 ablation: removing canonical-filter should still produce same hash
       on identical input but may differ on partial dicts.
       """
   ```
3. **freeze the manifest.** before publishing, generate:
   ```
   test_F1_repro_id:    sha256(canonical(axes)) == sha256(canonical(axes))
   inputs:  {"aspect_ratio": "2.39:1", "lens_mm": 35, ...}
   outputs: {"shot_id": "fff5950..."}
   manifest_sha256: <hash of all of the above>
   ```
4. **publish the manifest.** commit `atlas-exam-frozen/EXP-<NN>/MANIFEST_SHA256.txt`.
5. **never edit.** once published, the experiment is immutable. a new experiment = new EXP-<NN+1>.
6. **record all runs.** every run goes in `atlas-exam-frozen/EXP-<NN>/results/LEDGER.md` — including failures. failures are not deleted.

## file layout (target)

```
simself/
└── atlas-exam-frozen/
    ├── EXP-001/
    │   ├── MANIFEST_SHA256.txt         # frozen manifest
    │   ├── SCIENTIFIC_INTEGRITY.md     # 10 rules (this file)
    │   ├── audit/
    │   │   └── TRANSPORT_NOTE.md       # deviations
    │   ├── inputs/                     # frozen inputs
    │   ├── results/
    │   │   ├── LEDGER.md               # every run, including failures
    │   │   ├── result.<timestamp>.json # per-run output
    │   └── analysis.md                 # post-hoc interpretation
    └── EXP-002/                        # next experiment
```

## the 10 integrity rules

per `simself/docs/constitutional/scientific-integrity-2026-10-06.md`:

1. prediction before observation
2. ablation before interpretation
3. replication before generalization
4. frozen experiments are immutable
5. failed predictions remain in the ledger
6. corrections require a new version
7. exploratory analyses are labeled exploratory
8. positive bounded test ≠ proof of the whole framework
9. synthetic benchmark ≠ real-world validation
10. transport and execution deviations must be disclosed

## current state

EFMW-FULL ships EXP-001 with **PASS** result (16.5 timesteps lead-time gain, bootstrap 95% CI [3.5, 18.5]). EFMW's full manifest has 28 SHA-256 hashes.

simself has not yet published a frozen EXP-001. this skill file is the prerequisite.

## see also

- `simself/docs/constitutional/scientific-integrity-2026-10-06.md`
- `C:\Users\HP\Desktop\WORK\scavenge\jmikedupont2-efmw-friction-atlas-2026-10-06.md`
- `work_repos/jmikedupont2-scavenge/EFMW-FULL/` (cloned source)

---

*adopted 2026-10-06 by hermes (minimax-m3). source: jmikedupont2/EFMW-FULL (MIT).*