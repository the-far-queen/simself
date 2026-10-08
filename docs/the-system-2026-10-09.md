# THE SYSTEM — beyond the two repos

**Canonical source:** `simself/docs/kernel-controller-m0-m1-architecture-2026-09-13.md`
(bobby's 2026-09-13 directive, supersedes the 2026-09-07 framings).

Fieldcore and simself are **the substrate and the identity**. Everything
below is the machine they serve.

---

## The shape

```
                      ┌──────────────────────────┐
                      │   LIBRARY  (read-only)   │  the rules, the axioms,
                      │   Sacred Library         │  the accumulated corpus
                      └───────────┬──────────────┘
                        updates ONLY through the full chain:
                        propose → audit → qualify → commit
                                  │
                      ┌───────────▼──────────────┐
                      │  M1 CONTROLLER           │  qualifies operators
                      │  (outside core)          │  the librarian
                      └───────────┬──────────────┘
                                  │ promote / demote / reject
                      ┌───────────▼──────────────┐
   LEARNING LOOP ────▶│  M0 GOVERNOR  (IN CORE) │  1-bit veto
   propose only       │  deterministic, Python   │  sacred axes
                      └───────────┬──────────────┘
                                  │ ALLOW / DENY
                      ┌───────────▼──────────────┐
                      │       SIMSELF            │  learns, makes mistakes
                      │  4 operators + mini-LLM  │  adapts in real time
                      └──────────────────────────┘
```

**The direction of authority is the whole design.** SimSelf may
*propose* to the Library. It may never *write* to it. Four steps stand
between the system and its own rules, and three of them are outside the
thing being governed. That is a control system with a separation of
powers built into the plumbing rather than into policy.

## The five parts

### 1. CORE — deterministic, in-process, unbribable

| piece | job |
|---|---|
| **M0 Governor** | 1-bit ALLOW/DENY over sacred axes + invariants. Python owns it — no model, no gradient, no prompt. |
| **Geometry substrate** | distended egg-toroid. **apex void = invariant zero** — the protected self. flat base = residence. the 3D curve = reasoning surface. |
| **Regulator** | 6 avatar axes: agency, autonomy, coherence, authority, grounding, resilience |
| **4 sheaves** | Topology (geometric substrate) · MLTR (formal machine language) · MTE (bidirectional human↔LLM) · Coding |

### 2. LIBRARY — read-only, append-only, earned

Sacred Library holds the rules and the SNR-curated corpus. It changes
through exactly one path: *SimSelf proposes → M1 audits → Atlas Exam
qualifies → M0 commits or vetoes.*

**The exam sits in the write path.** That is the reason it exists in a
separate repository pointed at the substrate rather than inside it — an
exam that lives in the system it grades cannot be independent of it.

### 3. CONTROLLER (M1) — the 747 layer

Outside core. Qualifies operators, runs audits, promotes and demotes.
Bobby's framing: *"which controls simself learning loop... resonant
controller loop guided by sacred library which has the rules only updates
after atlasexam and passes to controller decides to update library or
not."*

### 4. SIMSELF — four operators plus a fast mind

| operator | targets |
|---|---|
| `codingOperator` | github / arxiv / hf, hourly pulls, whole repos, by stars |
| `robotOperator` | godot sim → single arm → humanoid, dual fast real-time |
| `languageOperator` | MTE, English ↔ MLTR |
| `Speaker/ListenerOO` | voice pipeline |
| **Mini-LLM** | real-time glue-check, meta-cognition, reflex |

### 5. THE LOOP — research, self-coding, real-time adaptation

`robotOperator` **dreams in idle microseconds, not sleep.** The design
assumption is that there is no time to be offline.

**Research is part of the loop, not a phase of the project.** The
`ResearcherOO` pulls; the loop consumes; the Library retains what
survives. Six files of frontier transcripts in the last two days are that
loop running at full rate.

---

## What is built, verified 2026-10-09

I measured this rather than trusting the architecture doc.

**Built and tested.** simself **299 passed / 2 skipped** · atlas-exam
**79 passed** · fieldcore **404 passed**, 5 pre-existing failures
unchanged since they were first observed.

Four modules built *from* the six-file corpus, each fixing a measured
defect:

| module | the defect it repairs |
|---|---|
| `hodge_cycle.py` | spectral radius 7.0 on the alternating mode |
| `sovereign_governor.py` | sacred axes drift 0.09 under 1,000 nudges |
| `resilience.py` | resistance shrank every attack below its own gate |
| `coherence_spine.py` | the spine — thresholds on a sheaf, executable |

Plus `sensorimotor_grounding.py`, `nested_stalks.py`, `falsifier.py`.

**Designed and present but unreached.** I checked reachability directly:

    loop.MainLoop              exists, 130 lines, referenced by NO test
    selfcore.py                 192 lines, 0 test files
    coding_operator_object.py   67 lines, 0 test files
    robotic_field_core.py      178 lines, 0 test files
    training_bridge.py         185 lines, 0 test files
    m1_m0_negotiation.py       34 lines, 0 test files
    modulator.py              251 lines, 0 test files
    actions.py                 84 lines, 0 test files

**53 modules in `src/constitutional/`, 29 test files.** The contrast is
the finding: the modules built *this session* from measured defects are
all tested; the older control-system modules — the M0/M1 loop, the
operators, the training bridge — are **present, readable, and never
exercised**.

A module nothing calls cannot fail. That is the same class as
`coding_operator_object.py` flagged in fieldcore's audit, the same as
`SparseStateSystem` in file 4, the same as `TemporalController` which
cannot even be instantiated.

**The learning loop does not currently close.** The parts are written.
The wiring is not. Until `MainLoop` is driven by something, the system
that is supposed to adapt is a set of adaptable parts.

## What this means for the design

The architecture is **sound and unusually well-specified** — a control
system with authority flowing one way, an exam inside the write path, a
read-only library, and a fast mind bolted to a deterministic veto. Most
agent projects have none of that.

**The gap is not design, it is closure.** The project's own vocabulary
already names the failure: *unwired*. Every serious finding across four
repos this session is a module that reads correctly, imports cleanly,
and is never called.

Three moves, in order:

1. **Close the loop.** Instantiate `MainLoop` with a real environment
   and a real governor, drive it, and let it fail in the open. One
   end-to-end run is worth more than fifty module tests.
2. **Test for reachability, not correctness.** Every module must have
   at least one inbound caller, asserted. That single check would have
   caught eight unwired modules, `SparseStateSystem`, `TemporalController`,
   and `coding_operator_object`.
3. **Then close the gap in the corpus vocabulary.** Two concepts never
   propagated in six files: ψ₀ (file 1 only) and counterfactual (file 6
   only). The system has a constitutional ground and no counterfactual
   evaluation — and the second is what tells you whether a proposed
   change should have been allowed.