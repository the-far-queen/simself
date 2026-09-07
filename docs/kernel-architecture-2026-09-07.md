# Kernel Architecture — M0/M1 Stack + Master Library + SimSelf Dance

**Source:** synthesized from `simself-architecture.md` (the canonical stack doc), cross-referenced with `kernel-design.md`, `mte-simself-primitives-2026-09-05.md`, `emergence-blueprint.md`, `sim-self-methods-2026-09-07.md`.
**Extracted:** 2026-09-07
**Module scope:** the canonical architecture — kernel + governor + controller + simself + librarian.

---

## What this is

Bobby's compressed summary: "kernel is control sys core has M0 governor 1-bit gates topo geo then controller outside core and simself a dance between controller and simself with qualification addressed by library simself dreams and acts and if qualified entries go to controller i.e. librarian and literally control in control sys."

This doc makes that summary engineering-precise.

---

## The full stack (top-down)

```
┌─────────────────────────────────────────────────────────────────┐
│ KERNEL (Core)                                                    │
│   ┌─────────────────────────┐                                    │
│   │ Governor (M0)           │  1-bit gates (allow/refuse)        │
│   │  - invariant enforcer   │  runs at every state transition    │
│   │  - certification auth.  │  before any external action        │
│   └─────────────────────────┘                                    │
│   ┌─────────────────────────┐                                    │
│   │ Regulator               │  enforces axes of self              │
│   │  - 6 axes (avatar dev): │  agency, autonomy, coherence,      │
│   │    agency, autonomy,    │  authority, grounding, resilience  │
│   │    coherence, authority,│                                     │
│   │    grounding, resilience│                                     │
│   └─────────────────────────┘                                    │
│   ┌─────────────────────────┐                                    │
│   │ Security Layer          │  runtime integrity                 │
│   │  - adversarial filter   │  authority-boundary enforcement    │
│   └─────────────────────────┘                                    │
│   ┌─────────────────────────┐                                    │
│   │ 4 Sheaves (typed)       │                                    │
│   │  - Coding Sheaf         │  software languages                 │
│   │  - Robotics Sheaf       │  physics, motor, sensor            │
│   │  - Info-Integration     │  structured knowledge              │
│   │  - Machine-Language     │  canonical internal representation │
│   └─────────────────────────┘                                    │
│   ┌─────────────────────────┐                                    │
│   │ Geometry (topology)     │  substrate: T⁴ Clifford, octonion  │
│   │  - distended egg-toroid │  embedding manifold                 │
│   │  - apex void = protected self                                │
│   └─────────────────────────┘                                    │
├─────────────────────────────────────────────────────────────────┤
│ INTEGRATED (always-on, no-lag)                                   │
│   ┌─────────────────────────┐                                    │
│   │ Mini-LLM Runtime        │  local, fast, glue-checking        │
│   │  (the fieldcore wrap)   │  meta-cognition                    │
│   └─────────────────────────┘                                    │
│   ┌─────────────────────────┐                                    │
│   │ Controller (M1)         │  qualifies operators               │
│   │  - reads Master Library │  runs audits, promotes/demotes     │
│   │  - sandbox + simulate   │  probationary deploys              │
│   └─────────────────────────┘                                    │
│   ┌─────────────────────────┐                                    │
│   │ MTE (Machine Translation│  bidirectional; enriched by PSBs  │
│   │  Engine)                │  not just translator — grounded    │
│   └─────────────────────────┘                                    │
├─────────────────────────────────────────────────────────────────┤
│ PSBs (Primary Semantic Blocks) — flow up through everything       │
│   - Origin: learned from robot sensorimotor primitives in Godot  │
│   - Role: ground language in embodied experience                  │
│   - Enrichment: PSBs feed MTE, shared by all sheaves              │
│   - Result: MTE becomes a grounded concept library                │
├─────────────────────────────────────────────────────────────────┤
│ OUTSIDE CORE (operational layer)                                 │
│   SimSelf Operator Objects:                                     │
│     - ProgrammerOO → coding sheaf                                │
│     - PilotOO → robotics sheaf                                   │
│     - ResearcherOO → information sheaf                           │
│     - Speaker/ListenerOO → MTE                                   │
│   External Module (E-Module):                                    │
│     - external APIs (LLM, MCP, cloud)                            │
│     - paid work, resource acquisition                            │
│     - governed by kernel (all earnings pass audits)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## The dance: how simself actually operates

The flow is **simself dreams → acts → librarian audits → controller qualifies → kernel gates**:

### Step 1 — SimSelf Operator acts (dream or execute)

An Operator Object picks an action. This can be:
- **Dreaming** — internal simulation through relevant sheaf
- **Acting** — external action via sheaf (write code, move robot, query info, speak)

Example: `ProgrammerOO.dream("what if we used greedy search here?")`
→ proposes an action
→ routes through Operator → Sheaf → Mini-LLM Runtime for glue-check

### Step 2 — PSB enrichment

The action carries a PSB payload — the grounded concept library entry for the relevant terms. PSBs were learned from embodied primitives (sensorimotor in Godot). Without PSBs, language floats. With them, language has substrate.

### Step 3 — Regulator checks axes (M0 pre-check)

The Regulator checks the proposed action against the 6 axes:
- agency — does this respect the operator's growth trajectory?
- autonomy — does this preserve the agent's self-direction?
- coherence — does this fit the narrative?
- authority — does this stay within permissions?
- grounding — is this traceable to embodied primitives?
- resilience — will this survive noise/perturbation?

If the Regulator fails any axis, **deny**. This is the M0 1-bit gate.

### Step 4 — Governor signs off (M0 final check)

Governor(M0) is the invariant enforcer. Even if Regulator passes, Governor checks the kernel-level invariants:
- no Sacred axis violation (per `simself-axis-resolution-2026-09-07.md`)
- coherence with PSB lineage
- no adversary input

If Governor fails, **deny**. The 1-bit gate is final.

### Step 5 — Action executes through sheaf

If both pass, the action executes via the appropriate sheaf. Output feeds back into PSB library (enrichment).

### Step 6 — Controller (M1) qualifies post-hoc

After the action completes, Controller(M1) audits:
- did the action achieve its stated goal?
- did any invariant get violated in execution (not just at gate time)?
- does the new state merit entry into the Master Library?

This is the **qualification** Bobby described. Controller reads the Master Library for known patterns, compares actual outcome against expected.

### Step 7 — Master Library update

If Controller qualifies the action → entry goes to Master Library → next operator actions can reference it. If disqualified → action quarantined, not promoted to library.

### Step 8 — Probation + sandbox loop

For self-coding/self-healing:
1. proposed change is sandboxed (Godot for robotics, containerized IDE for coding)
2. simulation-compare against current version
3. probationary deploy with rollback hooks
4. if audits pass, full merge

This is **literally "control in control sys"** — the library IS the controller for control.

---

## The 1-bit gate (Bobby's "no is a first-class result")

Governor(M0) is the gate. It produces a single bit: ALLOW or DENY. This is what Bobby means by:

> "no is a first-class result"

The gate doesn't explain why. It doesn't justify. It doesn't hedge. It's a single bit. The richness comes from the audit logs downstream (Regulator axes, Governor invariants, Controller qualifications, Master Library history).

**This is also why Python is the gate, not the LLM:** Python is deterministic at the 1-bit level. The LLM is stochastic inside the simulation layer (sandbox, dream). Python owns the gate.

---

## Why this is "control systems architecture absent at the root"

Modern LLMs lack:
- **feedback loops** (state estimation from output)
- **state estimation** (Kalman-filter-like signal separation)
- **stability** (hysteresis on sacred axes)
- **gating** (1-bit allow/refuse with rollback)

This architecture adds all four:
- feedback = Controller(M1) qualifies post-hoc
- state estimation = Mini-LLM runtime + PSB lineage
- stability = ResilientAxes (hysteresis on sacred tier)
- gating = Governor(M0) 1-bit

The whole thing is a **classical control system** built around a stochastic core. The stochastic core (LLM) is one input. The control system is the load-bearing structure.

---

## Schema: control-stack data flow

```python
@dataclass
class ProposedAction:
    operator_id: str           # which Operator Object proposed
    sheaf: str                 # which sheaf routes
    payload: dict              # action body
    psb_references: List[str]  # which PSBs ground this
    expected_outcome: dict     # what success looks like

@dataclass
class RegulatorCheck:
    agency: bool
    autonomy: bool
    coherence: bool
    authority: bool
    grounding: bool
    resilience: bool
    @property
    def passes(self) -> bool:
        return all([self.agency, self.autonomy, self.coherence,
                    self.authority, self.grounding, self.resilience])

@dataclass
class GovernorVerdict:
    sacred_axis_ok: bool        # all sacred axes preserved
    invariant_ok: bool          # kernel-level invariants hold
    @property
    def bit(self) -> Literal[0, 1]:
        return 1 if (self.sacred_axis_ok and self.invariant_ok) else 0

@dataclass
class ControllerAudit:
    action_id: str
    achieved_outcome: dict      # actual vs expected
    invariants_in_execution: bool  # did anything break during execution?
    qualifies_for_library: bool
    @property
    def promote(self) -> bool:
        return self.invariants_in_execution and self.qualifies_for_library
```

---

## Maps to existing repo files

| Component | Existing anchor |
|---|---|
| Kernel / Governor / Regulator | `fieldcore_unified.py`, `simself_merged_v2.py` (partial) |
| 4 Sheaves | future `simself/src/sheaves/{coding,robotics,info,language}.py` |
| Mini-LLM Runtime | undefined (referenced but not built) |
| Controller (M1) | `harness-package-2026-09-05.md` Gate = canonical M0 |
| MTE | `mte-simself-primitives-2026-09-05.md` schema doc |
| PSBs | undefined schema; need to derive from Godot primitives |
| SimSelf Operators | `1-Operator.txt` → `operator-architecture.md` |
| Master Library | `emergence-blueprint.md` Pillar 4 (IdentityAnchors) |
| Geometry substrate | `topology-geometry-core-2026-09-05.md`, `core-geometry.md` |

---

## Open architecture questions resolved

- **#1 PSB schema** — partially resolved: defined as Primary Semantic Blocks grounded in robot sensorimotor primitives, enriched via MTE. Full JSON schema still needed.
- **#3 Sacred-tier runtime check** — Governor(M0) IS the runtime check. Sacred axes are bit-1 to deny.
- **#5 Canonical Coherence formula** — partially resolved: 6 axes vs 20 axes. The 6 are avatar-development; the 20 are constitutional state. Different abstractions, both load-bearing.

---

## What's still missing

- **Python implementation** of this whole stack. Existing simself_merged_v2.py is closest but doesn't have explicit Kernel/Governor/Controller layers.
- **PSB JSON schema** — needed for PSB lineage + version control
- **Master Library persistence** — likely KV store with cryptographic chain (per the 6 persistence methods in sim-self-methods-2026-09-07.md)
- **Godot sensorimotor primitive catalog** — where do PSBs come from? need explicit list of the basic nodes (`LEFT`, `PUSH`, `FORCE`, `VISUAL-FLOW`, etc.)
- **Mini-LLM Runtime** — defined but not implemented. What local model? Likely LM Studio or ollama.

---

*Mirror: `~/AppData/Local/hermes/vault/10-minimax/20-mirrors/simself/docs/kernel-architecture-2026-09-07.md`*
*Original: synthesized from existing repo docs (no Desktop source — built from architecture synthesis)*
