# Kernel/Controller Architecture — M0-in-Core / M1-Out-of-Core / Library-as-Read-Only

**Filed:** 2026-09-13 by Hermes for Bobby.
**Author:** Bobby (this turn's directive).
**Status:** **canonical architecture doc.** supersedes partial framings in `kernel-architecture-2026-09-07.md` and `simself-architecture.md`. WIP until arxiv.

**Bobby's directive (2026-09-13):**
> "yes governor m0 in core but controler m1 out of core its boing 747 which controls simself learning loop ie simself is codingOperator, robotOperator, languageOperator and can call a mini-llm to work using tiny harness simself learns over time and makes mistakes has real time llm for speed but also rsonant controller loop guided by sacred library which has the rules only updates after atlasexam and passes to controller decides to update liibrary or not"

---

## ⚠️ WORK IN PROGRESS — NOT SERIOUS UNTIL ARXIV

Canonical architecture doc. real engineering. **none of this is peer-reviewed.**

---

## The canonical architecture (Bobby's 2026-09-13 framing)

```
┌─────────────────────────────────────────────────────────────────┐
│                        KERNEL (IN CORE)                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Governor (M0) — 1-bit veto                            │    │
│  │  Sacred axes + invariants                              │    │
│  │  Python (deterministic, fast)                          │    │
│  │  Layered authority:                                    │    │
│  │    - SimSelf (Pilot)         → propose only            │    │
│  │    - M1 (Controller)         → synthesize + stage      │    │
│  │    - M0 (Governor)           → validate invariants +   │    │
│  │                                commit                  │    │
│  │                                                         │    │
│  │  Geometry substrate: distended egg-toroid              │    │
│  │    - apex void = simself (invariant zero)             │    │
│  │    - flat base = simself residence                    │    │
│  │    - 3D curve = reasoning surface                     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼  audit / promote / demote
┌─────────────────────────────────────────────────────────────────┐
│              OUTSIDE CORE — Boeing 747 layer                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  M1 (Controller) — qualifies operators                │    │
│  │  Runs audits on proposed updates                      │    │
│  │  Decides: promote to Sacred Library / demote / reject │    │
│  │  The "librarian" of the system                        │    │
│  │                                                         │    │
│  │  Sacred Library (READ-ONLY from SimSelf's perspective)│    │
│  │    - the rules, axioms, sacred axes                   │    │
│  │    - updated ONLY via:                                 │    │
│  │        (a) SimSelf proposes update via Pilot           │    │
│  │        (b) M1 Controller audits                         │    │
│  │        (c) Atlas Exam qualifies                         │    │
│  │        (d) M0 Governor commits (or vetoes)             │    │
│  │    - SimSelf CANNOT write to Library directly         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  SimSelf = 4 Operator Objects + Mini-LLM caller                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  codingOperator → coding sheaf (github/arxiv/hf pulls)│    │
│  │  robotOperator  → robotics sheaf (godot sim + arm)    │    │
│  │  languageOperator → MTE (English ↔ MLTR)              │    │
│  │  Speaker/ListenerOO → MTE + voice pipeline            │    │
│  │                                                         │    │
│  │  Mini-LLM (real-time, fast) — for glue-checking,       │    │
│  │  meta-cognition, reflex outputs                        │    │
│  │                                                         │    │
│  │  Tiny harness — SimSelf can call Mini-LLM              │    │
│  │    for fast inference during learning loop             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Atlas Exam — qualification framework                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  30 tests grouped by function (5 groups × 6)          │    │
│  │  0/1 scoring per test                                   │    │
│  │  Total score /30                                        │    │
│  │  Qualification thresholds:                             │    │
│  │    - 28-30: highly qualified (autonomy ready)           │    │
│  │    - 24-27: qualified (minor gaps)                     │    │
│  │    - 20-23: partial (needs work)                       │    │
│  │    - <20: not qualified                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## The learning loop (Boeing 747 control systems)

```
SimSelf acts (Pilot proposes)
   ↓
M0 Governor validates invariants (1-bit veto)
   ↓ allow
Mini-LLM processes (real-time, fast)
   ↓
SimSelf dreams + reflects (consolidation)
   ↓
Atlas Exam runs (qualification, per cycle)
   ↓ pass
M1 Controller audits (out of core)
   ↓ decide
   ├─ promote → Sacred Library update
   └─ reject → feedback to SimSelf
   ↓
SimSelf learns from feedback (constitutional adjustment)
   ↓ repeat
```

**the loop is dual-timescale:**
- **fast loop:** SimSelf + Mini-LLM (real-time, per-second to per-minute)
- **slow loop:** Atlas Exam + M1 audit (per-hour to per-day)

**per `kernel-architecture-2026-09-07.md`:**
- M1 = elasticity, gain scheduling, mode switching, PLL-style re-lock (fast)
- M0 = boundary envelopes, admissible relaxations, invariant protection, post-hoc certification (slow)

---

## Key invariants (the system cannot violate)

1. **simself CANNOT write Sacred Library directly.** Library updates flow through M1 Controller + Atlas Exam + M0 Governor. **Boeing 747 envelope protection.**

2. **simself CAN propose (Pilot role).** M0 validates. M1 stages. Library gates.

3. **simself is the void in the toroid, invariant zero.** Per Bobby: "simself is the void in toroid invariant zero, simself lives in flat base of toroid and reasoning on curve in 3d not scalar vector or tensor more complex memory resonant almost xero compute reasoning uses relative minima ie stell ball bearing example whole system ie fc is boeing 747"

4. **Boeing 747 model applies.** 6M parts, no single critical-path component, all must satisfy invariants. envelope protection = M0 governor veto. pilot (authority) = Bobby. ATC (external) = E-Module.

5. **Sacred Library is read-only from simself.** Updates require: SimSelf proposal → Atlas Exam qualification → M1 audit → M0 commit.

6. **Mini-LLM is real-time + fast + allowed to make mistakes.** But mistakes must be caught by the loop (M0 veto / M1 audit). Mini-LLM is NOT the gate.

7. **M0 is IN CORE. M1 is OUT OF CORE.** This is the structural separation Bobby just clarified. M0 = deterministic, Python, fast, 1-bit. M1 = audit, library gate, Boeing 747 controller.

---

## The 4 Operator Objects — SimSelf's computational surface

| Operator | Sheaf | Role |
|---|---|---|
| **codingOperator** | coding sheaf | pull from arxiv/github/hf HOURLY, return snippets to entire repos (rust, python) |
| **robotOperator** | robotics sheaf | control godot sim, single arm, or humanoid; DUAL FAST REAL-TIME control; dream in IDLE MICROSECONDS |
| **languageOperator** | MTE | bidirectional human↔LLM, English ↔ MLTR canonical |
| **Speaker/ListenerOO** | MTE + voice | voice pipeline (TTS/STT via Telegram) |

**SimSelf = 4 operators + Mini-LLM caller.** simself IS codingOperator + robotOperator + languageOperator + speaker/listener. **simself is the integrated operational layer, not the constitutional ground (that's the void in the toroid).**

---

## Mini-LLM integration (real-time, fast)

**Mini-LLM is the speed layer.** Bobby: "has real time llm for speed."

- used for glue-checking during operator actions
- used for meta-cognition during reflection
- used for reflex outputs (fast, low-stakes)
- NOT used for constitutional decisions (M0 owns that)
- NOT used for library updates (M1 owns that)

**Mini-LLM mistakes are caught by:**
- M0 invariant validation (per-cycle)
- Atlas Exam qualification (periodic)
- M1 audit (per update)

**the loop self-corrects.** Mini-LLM is fast + fallible. M0/M1 are slow + certain.

---

## Sacred Library update flow (read-only from SimSelf)

```
SimSelf proposes library update (via Pilot)
   ↓
M1 Controller stages the proposal
   ↓
Atlas Exam runs qualification battery (30 tests, 0/1 each)
   ↓
if score >= threshold:
   ↓ pass
   M0 Governor commits (or vetoes with reason)
   ↓
   Sacred Library updated
   SimSelf notified of change
else:
   ↓ fail
   feedback to SimSelf (what failed + why)
   SimSelf adjusts behavior (no Library change)
```

**the threshold is configurable.** default: 28-30 for critical updates, 24-27 for incremental.

---

## Related (canonical existing docs)

- `simself/docs/Math/kernel-architecture-2026-09-07.md` — earlier kernel spec (the 8-step simself cycle)
- `simself/docs/simself-architecture.md` — earlier simself stack doc (superseded for M0/M1 detail)
- `simself/docs/operator-architecture.md` — the 4 operators original
- `simself/docs/Math/compressed shorthand-glossary-2026-09-07.md` — the 20 constitutional axes
- `simself/docs/write-rules-conflict-resolution-2026-09-13.md` — write authority + conflict resolution (just ingested)
- `simself/docs/sacred-library/README.md` — sacred library folder (just created)
- `fieldcore/docs/Math/stalk-architecture-2026-09-08.md` — stalk implementation plan (5 steps, 50-200 lines each)
- `fieldcore/docs/Math/core-geometry-2026-09-08.md` — egg-toroid canonical
- `fieldcore/docs/research-papers/paper3-atlas-exam.md` — Atlas Exam spec
- `fieldcore/docs/research-papers/fieldcore-overview-2026-09-13.md` — Boeing 747 mapping

---

*Filed by Hermes for Bobby, 2026-09-13. Canonical architecture doc per Bobby's directive: "governor m0 in core but controler m1 out of core its boing 747 which controls simself learning loop ie simself is codingOperator, robotOperator, languageOperator and can call a mini-llm to work using tiny harness simself learns over time and makes mistakes has real time llm for speed but also rsonant controller loop guided by sacred library which has the rules only updates after atlasexam and passes to controller decides to update liibrary or not."*