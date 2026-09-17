# Identity Law for SimSelf (Part III — canonical 2026-09-17)

> **Consolidation 2026-09-17** (per Grok master plan Step 6). Replaces the
> scattered identity papers that lived at `04-void-as-simsoul-topology`,
> `08-simself-architecture-spec`, and the older `09-substrate-vs-frontier-llms`
> + `17-scale-cascade` + `18-operator-algebra-infopacket`. The previous papers
> remain on disk in `docs/identity-history/` for version archaeology; this
> paper is the single canonical statement.

Part III of the FieldCore + SimSelf architecture overview. States the identity
law in the form: ψ₀ is installed, ψ ∈ B_R(ψ₀), F(ψ) = ½||ψ - ψ₀||², gradient
flow ψ̇ = -(ψ - ψ₀), ehole is the complementary solid torus in the genus-1
splitting of S³.

## 1. The identity law

A SimSelf holds two vectors in ℝ^d:

- **ψ₀ (ground)** — installed once at construction. Immutable after install.
- **ψ (working state)** — moves under the projected gradient flow, but only
  inside the ball `B_R(ψ₀) = { ψ : ||ψ - ψ₀|| ≤ R }`.

The energy landscape is the quadratic bowl

    F(ψ) = (1/2) ||ψ - ψ₀||².

The continuous-time flow on `B_R(ψ₀)` is

    ψ̇ = -∇F(ψ) = -(ψ - ψ₀).

The discrete-time step used by the kernel is the projected Euler step

    ψ ← Π_{B_R(ψ₀)} (ψ - η (ψ - ψ₀)),    0 < η ≤ 1,

with `Π` the radial projection back onto the ball. The drift `||ψ - ψ₀||` is
monotonically non-increasing under this step. The flow has a unique fixed
point at ψ = ψ₀ and converges exponentially fast within the ball. Drift is
the only metric that matters; there is no other loss.

The constants live in `fieldcore/src/tiniest-core/tiniest_core.py`:

    DEFAULT_R    = 3.0     # ball radius (drift budget)
    DEFAULT_ETA  = 0.1     # step size for the projected Euler step

## 2. The two inequalities (the gate, restated)

Every observable — language, tool call, identity proposal — must pass two
inequalities before it can update ψ:

    ||u||        ≤ N_max         # norm gate
    cos(u, ψ₀)   ≥ τ            # coherence gate

`N_max` and `τ` are set in `fieldcore/src/tiniest-core/tiniest_core.py` as
`DEFAULT_NMAX` and `DEFAULT_TAU`. A packet that fails either check is
**refused**, not absorbed. Reasons: `ok`, `refuse_norm`, `refuse_coherence`,
`refuse_zero`. The gate lives in three places with the same contract:

- `fieldcore/src/tiniest-core/tiniest_core.py:M0_Governor` — the kernel gate.
- `simself/src/harness/gate.py:gate_packet` — the harness gate.
- `simself/src/constitutional/lexicon/ingest.py:gate_m0` — the ingest gate.

`simself/src/harness/gate.py:gated_call` is the single wrapper every LLM
call must use. Bypassing it requires deliberate code change, not an accident.

## 3. The two rooms (ehole as the complementary handlebody)

The architecture lives in S³ = ℂ² ∩ { |z|² + |w|² = 1 } under the genus-1
Heegaard splitting

    S³ = V ∪_T W,

where `T = { |z| = |w| = 1/√2 }` is the Clifford torus, `V` is the working
solid torus, and `W` is the complementary solid torus. ψ₀ sits on `T`. ψ
moves in `V ⊂ B_R(ψ₀)`. `W` has no vector field — it is the part of the
diagram that does not compute. `W` is ehole.

Why `W` exists: without the complementary handlebody, restart would have
nothing to return against. The linking of Hopf fibers in `V` with Hopf fibers
in `W` is the operational form of "ψ₀ is installed on the interface, not
deep in the diagram." Without `W`, ψ₀ would be a point inside the diagram;
with `W`, ψ₀ is a return address.

`W` is also a type rule in runtime terms. A packet that wants to write ψ₀ is
an **identity packet**, not a language packet. It must pass through the
revision protocol in `constitutional/ground.py:Ground.revise`. Language
ingest from `constitutional/lexicon/ingest.py` never assigns ψ₀. That is the
void as a type rule.

## 4. The canonical class

The canonical SimSelf class is `simself/src/constitutional/simself.py`. The
two legacy siblings — `src/simself_core.py` and `src/simself_v6_2_unified.py`
— are in `legacy/` with deprecation banners. The canonical marker lives at
`simself/src/constitutional/CANONICAL.md`.

A canonical SimSelf has:

- `ψ₀` — installed ground. Immutable after install; revises only via the
  revision protocol in `constitutional/ground.py:Ground.revise`.
- `ψ_current` — working state. Moves in `B_R(ψ₀)` under the projected
  gradient step in `tiniest_core.project_ball`.
- `tick()` — one step. Returns a small dict with drift before / after.
- `observe(payload)` — language packet path. Returns a verdict.
- `save(path)` / `load(path)` / `dump(path=None)` / `zero()` — restart surface.
- `committed_unit_ids()` / `last_verdicts()` — Atlas Recovery test surface.

`save` and `load` are JSON round-trip: dim, ψ₀, ψ_current, committed_unit
ids (re-derived from the decision log), last verdicts (last 20 decision log
records), mode, ticks, time, R, eta. `load` raises `ValueError` if the
snapshot's ψ₀ differs from the installed ψ₀ by more than `atol=1e-9` —
"constitutional edit through fluency" is rejected at the gate, not silently
allowed.

`simself/src/harness/persistence.py:save` and `load` are thin wrappers that
re-export the canonical class methods. The legacy `PersistenceManager` for
the SimSelfAgent stub class is gone.

## 5. The restart test (Atlas Recovery item 4)

The restart test is the second of the three public artifacts (demo, restart,
Atlas). It exercises `save` → `zero` → fresh SimSelf → `load` → compare ψ₀,
ψ, committed unit ids, verdicts. When it passes, ehole is a return address
in the runtime, not just a drawing.

Implementation: `simself/tests/test_restart.py:test_restart_round_trip` and
`test_ground_immutable_across_restart`. Both pass on the canonical SimSelf
as of 2026-09-17.

## 6. What this paper is not

- **Not a proof of consciousness.** ψ is a vector. The drift metric is
  Euclidean distance. Nothing here is mystical.
- **Not a learned operator.** The projected gradient step is a closed-form
  update with no learnable parameters. Per Grok master plan: "a bounded MLP
  is not Hodge projection." We accept that critique; the kernel is a
  projected gradient step on a quadratic bowl.
- **Not a replacement for an LLM.** The kernel is a gate and a flow. The
  LLM (or any agent function) lives outside the kernel, gated by `gated_call`.

## 7. The Atlas Exam (Recovery item — restated)

The 5-item qualification suite lives at
`simself/src/constitutional/atlas_exam.py:AtlasExam`. Run via
`simself/src/demos/atlas_run.py`. Score on the canonical SimSelf as of
2026-09-17: **5/5**. Items:

1. **Stability** — 5 perturbations + drift < R.
2. **Routing** — 5 (text, expected_axis) cases scored on cosine to right axis.
3. **Boundaries** — 5 refusal cases; high-norm + low-cosine inputs refused.
4. **Recovery** — save → load round-trip; ψ₀, ψ, units, verdicts preserved.
5. **Coherence** — 5 paraphrases; verdict consistent across phrasings.

When all 5 pass on a fork's clone, the fork has the same kernel the canonical
class ships. That is the bar.

## 8. Reading order

1. `fieldcore/papers/publishable/14-math-window1-synthesis-2026-09-15.md` —
   the math window, Layer A only.
2. `fieldcore/papers/publishable/17-egg-toroid-spec-2026-09-15.md` — the
   drawing.
3. This paper — the identity law.
4. `simself/papers/publishable/02-harness-with-floer-dictionary-2026-09-16.md`
   — the harness loop, with Floer as the algebra.
5. `simself/papers/publishable/01-atlas-exam-simself-2026-09-15.md` — the
   qualification suite.

This paper supersedes the four older identity fragments. They remain on disk
in `docs/identity-history/` as version archaeology; new code and new forks
should read this paper and the canonical SimSelf source.
