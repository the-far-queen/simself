# Paper 3 — Atlas Exam (simself-side: empirical work)

**Title:** *Atlas Exam: Geometric Framework for AI Substrate Evaluation*

**Status:** Paper 1 in ranking. **This is the simself-side half.** The fieldcore-side (framework theory) is at `fieldcore/docs/research-papers/paper3-atlas-exam.md`. **Both halves are the SAME paper, committed separately.**

**Authors:** Bobby (first) + Hermes (second).

**Target venue:** AI evaluation venue (NeurIPS eval track / HELM workshop / FAccT). ~16-20 pages.

**Effort:** ~6 weeks (3 weeks correlation study + 3 weeks writing).

---

## ⚠️ Caveat: this paper is joint with fieldcore repo

The paper has two halves that must be written and committed together:

| Half | Repo location |
|---|---|
| Framework theory, mathematical substrate, 8-rung ladder math | `fieldcore/docs/research-papers/paper3-atlas-exam.md` |
| **Empirical correlation study, test infrastructure, Atlas exam protocol (THIS FILE)** | **`simself/docs/research-papers/paper3-atlas-exam.md`** |

Bobby is author on both. The two halves must be written in parallel. **No half may be submitted without the other.**

---

## What this half contains

- **Atlas exam protocol** — test scaffolding, substrate instantiation, per-rung test definitions.
- **Test infrastructure** — `simself/src/constitutional/atlas/` (or similar) — code that runs Atlas on any substrate.
- **Empirical correlation study design** — 5 substrate variants, statistical analysis plan.
- **Results section** — Atlas pass/fail per substrate, correlation with engineering properties.
- **Failure mode case study** — routing 2/5 pre-existing flakiness as honest limitation.

## What this half does NOT contain

- Framework theory (that lives in fieldcore-side).
- Mathematical substrate proofs (fieldcore-side).
- 27-area taxonomy (split between repos).

## Empirical state — current (simself-side)

- `simself/src/constitutional/test_frequency_layer.py` — 7/7 tests pass.
- Atlas exam — 4/5 tests pass (routing 2/5 pre-existing).
- `simself_merged_v3_5.py` — embryogenic Ψ₀ = installed Ψ₀, cos sim = 1.000000.

## Empirical state — REQUIRED before writing

- Atlas exam applied to 5 substrate variants.
- Per-variant test pass/fail table.
- Per-variant engineering property measurements (stability, robustness, frequency distinctness, recovery time, boundary preservation).
- Correlation analysis: Pearson r between Atlas pass rate and engineering property.

## What this paper IS NOT

- Not a benchmark suite.
- Not an LLM leaderboard.
- Not a safety framework.
- Not an alignment evaluation.

## Open questions

1. **Test infrastructure location** — `simself/src/constitutional/atlas/` or `simself/tests/atlas/`?
2. **Correlation statistical analysis** — write Python analysis script in repo?
3. **Atlas protocol versioning** — does Atlas evolve with the substrate, or stay frozen?

---

*Stub. Source: `simself/docs/research-papers-2026-09-13.md` §Paper 3.*

*Joint paper with fieldcore. Both halves must be written in parallel.*