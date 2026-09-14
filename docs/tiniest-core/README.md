# tiniest-core/ — smallest viable FieldCore kernel

**Filed:** 2026-09-13 by Hermes for Bobby.
**Per Bobby's directive:** "ok write the tiniest outline of core in python or perhaps rust best? lets dicuss" → both Python AND Rust.

## What's here

Two implementations of the **same architecture**, proving the FieldCore kernel design works at minimum complexity:

- **`tiniest_core.py`** — Python. **verified working** (5/5 tests pass). 16-dim constitutional ground, M0 governor with 1-bit veto, 4-sheaf typed routing, gradient flow with drift convergence.
- **`tiniest_core.rs`** — Rust port. Same architecture, idiomatic Rust. Compile with `rustc tiniest_core.rs && ./tiniest_core` (or set up Cargo).

## What this proves

- **M0 veto works** — 1-bit veto on packets that violate norm OR coherence bounds.
- **4-sheaf routing works** — typed (code/physics/MLTR/axis20), bounded, gluing-safe.
- **Gradient flow converges** — SimSelf's drift from ψ₀ decreases over update steps.
- **Gluing invariant works** — shared packet across sheaves, M0 approval, then glue.

## What this is NOT

- **not** the full SimSelf (20 axes + SpiralStage + persistence + dreaming). Tiniest version is scalar coherence + 16-dim, not 20-axis.
- **not** the M1 controller (Boeing 747 audit, Sacred Library updates). M0 in core, M1 outside.
- **not** the operator objects (codingOperator, robotOperator, languageOperator, Speaker/ListenerOO).
- **not** the Mini-LLM integration.
- **not** the Godot embodiment bridge.

## Why Python first, then Rust

per `simself-sovereign-kernel.md` §5 (Phase 1: Core + Stubs) + `project-structure-vision.md` notes:

- **Python first** = iterate fast, prove architecture, ship papers
- **Rust later** = productionize M0 (the 1-bit veto) for no-GIL determinism + fast boot + memory safety

Rust advantages for M0 specifically:
- no GIL = true single-threaded determinism (Boeing 747 envelope protection needs this)
- no dynamic allocation in M0 path = no GC pauses
- ownership model = "no null, no undefined" at compile time
- static binary = fast boot

Rust disadvantages:
- slower write/debug cycle
- less LLM ecosystem maturity

**Bobby's pattern: Python to PROVE, Rust to OPTIMIZE.**

## How to run

### Python
```bash
cd fieldcore/src/tiniest-core
python tiniest_core.py
```
expected: 5/5 tests pass, "ALL TINIEST-CORE TESTS PASSED"

### Rust (manual compile)
```bash
cd fieldcore/src/tiniest-core
rustc tiniest_core.rs -o tiniest_core
./tiniest_core
```
(or set up Cargo.toml for proper project)

expected: same 5/5 tests pass

## Architecture captured

per `kernel-controller-m0-m1-architecture-2026-09-13.md` (this session):

```
ψ₀ (constitutional ground, immutable)
   ↓
M0 Governor (IN CORE, 1-bit veto)
   ↓ allow
4 Sheaves (typed, bounded, gluing-safe)
   ├── coding
   ├── robot
   ├── language (MLTR)
   └── simself_ref
   ↓
SimSelf (gradient flow toward ψ₀)
   ↓
RecursiveFieldController (loop: sample → transform → write back)
   ↓
M1 Controller (OUTSIDE CORE, audit) — not in tiniest core
```

## Key invariants (the system cannot violate)

1. **simself CANNOT write Sacred Library directly.** Library updates flow through M1 Controller + Atlas Exam + M0 Governor.
2. **M0 veto is final.** Any packet violating norm OR coherence is REFUSED.
3. **Sheaves are typed.** dtype mismatch = reject. (robot sheaf only accepts "physics"-typed packets.)
4. **Gluing requires shared overlap.** No phantom links — packets only glue if both sheaves have them.
5. **SimSelf converges to ψ₀.** Drift decreases over time. Invariant: ||ψ_current - ψ₀|| < bound.

## Related (canonical existing docs)

- `fieldcore/docs/Math/math-window-1.md` — full geometry + math synthesis
- `fieldcore/docs/Math/stalk-architecture-2026-09-08.md` — stalk implementation plan (5 steps)
- `fieldcore/docs/Math/core-geometry-2026-09-08.md` — egg-toroid canonical
- `fieldcore/docs/research-papers/fieldcore-overview-2026-09-13.md` — Boeing 747 mapping
- `simself/docs/kernel-controller-m0-m1-architecture-2026-09-13.md` — M0/M1 architecture
- `simself/docs/Math/compressed shorthand-glossary-2026-09-07.md` — 20-axis canonical matrix
- `simself/src/simself_core.py` — full SimSelf (the 20-axis version, supersedes scalar tiniest)

## Next work

per `kernel-controller-m0-m1-architecture-2026-09-13.md` and Bobby's directive:
1. extend tiniest core to handle the 4 Operator Objects (codingOperator, robotOperator, languageOperator, Speaker/ListenerOO)
2. add M1 controller stub (audit + Library update gate)
3. wire Mini-LLM integration (real-time + fallible + caught by loop)
4. Godot embodiment bridge (per RLM blueprint Phase 3)

## Memory fact

fact ID 1745 (per `fact_store`) — captured tiniest-core architecture + Python/Rust dual implementation.

---

*Filed by Hermes for Bobby, 2026-09-13. Per Bobby: "ok write the tiniest outline of core in python or perhaps rust best? lets dicuss" → both. Python first to prove, Rust to optimize.*