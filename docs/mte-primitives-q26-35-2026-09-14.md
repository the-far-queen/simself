# MTE Typing + SimSelf Primitives + Distributed Node Prototype

**Source:** `Desktop/SimSelf/docs/mte-typing-simself-primitives.md` (12.3KB)
**Filed:** 2026-09-14 by Hermes for Bobby (re-mining pass)
**Status:** **engineering reference** — 4 workstreams: w26 MTE typing, w27 distributed node, w28 meta-sheaf, w29 primitives.

---

## 1. MTE Typing Systems (w26)

### Option 1: Minimal Typed English (MTE) Lattice

Partial-order type system for utterances. **6 base types:**
- Declarative
- Imperative
- Interrogative
- Exclamatory
- Optative
- Subjunctive

**Subtypes:** Factual, Hypothetical, Causal.

**Rejection rules** block untypable/conflicting inputs:
- imperative without authority → reject
- subjunctive without condition → reject

Computable via mini-LLM (regex + embedding checks). Enforces safety (reject "do harm" as invalid imperative).

### Option 2: Grounded Semantic Primitives

Maps English to 20–50 atomic primitives (MOVE, OBSERVE, MERGE) with invariants (MOVE requires location bounds). Translation via projector (mini-LLM + rules). Rejection on ungroundable phrases. Extends to robots/code (MOVE → actuator call).

### Option 3: Code Loops as Language Bridge

Wraps English in code (Python functions for intents). Executes in sandbox. Rejection via static analysis (no unbounded loops). Outputs structured (dict with invariants). Scales to multi-step.

### Recommendation

Start with **MTE (Option 1)** — global constraint, plugs into others. Define lattice/rejections first, build/test/qualify/promote. English as proposal only (no direct execution). Prevents drift, applies to all domains.

---

## 2. SimSelf Distributed Node Prototype (w27)

### Core setup — 3-node network

- **VisionStalk**: detects objects
- **ArmStalk**: positions
- **HandStalk**: grasps

Each node has:
- compressed embedding (np.int8 log-scaled)
- precision domain (bit_width, epsilon ε)
- invariants (e.g., energy <1.0, norm <1.0)
- recovery_map (decompress to fp32)

### Gluing governor

Checks compatibility:
- invariant overlap
- ε alignment
- semantic distance <0.5

Merges embeddings (weighted avg). Unions invariants. Rejects with reason ("energy mismatch"). Multimodal (vision-arm glue for grasp).

### Simulation loop

1. Initialize nodes
2. Attempt pairwise glues (vision-hand if object detected)
3. Execute if successful (grasp if torque ok)

**Demonstrates safety:** failed glue = no action.

### Extensions

- Add language node (command parsing)
- Swap NumPy for Torch quantization
- Visualize manifolds (Matplotlib plots)

Minimal but faithful to topo-sheaf + mixed-precision.

---

## 3. Meta-Sheaf Resonance & Resilience Mechanisms (w28)

### M1-M0 negotiation

- **M1** (elastic intent layer): dynamic tuner like PLL, adapts to noise via phase lock
- **M0** (plastic reality layer): fixed geometry, enforces invariants
- **Resilience** = interplay (M1 absorbs perturbations, M0 provides anchors)
- Prevents collapse (M1 rephrases noisy input to fit M0 bounds)

### Meta-sheaf definition

Oversees sheaf as resonant manifold. Maintains coherence via negotiation:
- M1 proposes glue
- M0 checks invariants
- feedback refines

Ties to PLL (phase error → adjustment, lock threshold >0.8).

### Implementation ties

- M1 = adaptive projector (mini-LLM with elasticity params)
- M0 = fixed governor (invariant checks)
- resonance score = 1 - phase_error
- Extends to Module D (technical education: predict failures, shift modes proactively)

### Next evolution

Q3 curriculum for proactive health (pilot predicts noise from world model, requests mode shift). Transitions reactive → anticipatory resilience.

---

## 4. Core Primitives Normalization & SimSelf Integration (w29)

### Primitives in machine register

**Self:**
- Persistent, accumulating subsystem (state vector + history buffer)
- Experiences via OperatorObjects (domain-specific interfaces: coding, robot, language)
- Bounded (no direct authority access, governor owns decisions)

**Authority:**
- External geometric governor (invariant enforcement)
- SimSelf queries but cannot override
- Read-only for SimSelf, write via approved ops

**Agency:**
- Scoped action capacity (select ops within budget)
- Bounded by invariants (energy < threshold)
- SimSelf exercises via OperatorObjects but rejects unsafe (no unbounded recursion)

---

## 5. Sacred Library Write Rules (w34)

### Rules for pilot (B)

SimSelf commits only if:
- coherence > 0.8
- novelty > 0.5 (not redundant)
- invariants preserved (truth > 0.7)
- lineage traceable

Prune low-confidence (<0.6) periodically. Bounded size (max 1k entries, FIFO on overflow).

### Conflict resolution

- Detect via embedding distance + invariant clash (e.g., "move fast" vs "quiet/slow")
- Resolve by priority: user prefs > commands, coherence-weighted
- Fallback query ("resolve conflict?")
- Log resolutions for learning

---

## 6. Proactive Resilience Simulation for Q3 (w35)

### Setup

Pilot (B) analyzes world model (W) trends to predict failures (e.g., noise spikes via entropy delta >0.2). Requests mode shifts (full-flow → bounded-safe) before impact. Tests via harness (perturbations, traps: drift, overload).

### Key components

- Health metrics (coherence stability, invariant drift, resource headroom)
- Predictive model (simple ARIMA on trends)
- Intervention requests ("degrade to safe mode")
- Audit logs outcomes (~85% preemptive success)

### Trap scenarios

- Gradual drift (slow entropy rise → predict realignment)
- Sudden overload (spike detection → halt)
- False positives (over-caution → refine thresholds)
- Multi-trap chains (cascades → sequential shifts)

### Outcomes & certification

- Survival certifies predictive resilience
- Graceful degradation (lock invariants during traps)
- Transitions reactive → proactive (B as "seer")

### Mode-degradation taxonomy

- **Full-Flow** (unbounded ops)
- **Bounded-Safe** (invariant clamps, reduced radius)
- **Locked-Halt** (read-only, query authority)

Triggers on predictions (coherence <0.7 forecast → step down).

---

## 7. FieldCore IDE Forking & CodingOperator Environment (w32)

### Vision

Fork VSCode into "FieldCore IDE" (shell for governor M0). Specialized for sheaves:
- Sr Engineer (high-reasoning mode, full invariants)
- Jr (fast/cheap, bounded ops)
- Robotics (actuator sims)
- LLM (intent projections)

Progressive unlock: code first, then robotics.

### Safety invariants for handoffs

English-to-coding: reject if:
- untypable (MTE fail)
- invariants clash (no unbounded loops)
- confidence < 0.8

Mini-LLM checks before commit. Governor (M0) halts breaking changes (diff analysis for drift >0.1).

### Resources & ties

GitHub forks (Ralph-Wiggum, AgentScope), Anthropic Claude Code integration. Shifts CodingOperator to environment (IDE as interface). Persistent via Sacred Library commits.

### Implications

Not just editor — full FieldCore shell. Enables safe, sheaf-aware development. Ties to resilience (invariants prevent unsafe forks).

---

*Filed 2026-09-14 by Hermes. Per Bobby: re-mining pass on underused originals.*
