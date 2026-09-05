# SimSelf kernel schemas — MTE, primitives, gates

**Source:** `Desktop/FieldCore/mte-typing-simself-primitives.md` (Bobby, 2026-03-03; covers w26-w35)
**Status:** 4 unique schemas extracted. CS-loaded terms stripped. Implementation-ready.

Bobby's note covers 5 sections with multiple concepts. Most overlap with existing vault docs (MTE as the language gate, FieldCore IDE fork in `chorus-ide-design.md`, etc.). Four schemas are new and directly constructible.

---

## 1. M1-M0 negotiation architecture (w28)

**Two-layer adaptive system.**

**M0 (plastic reality layer).** Fixed geometric governor. Enforces invariants. Cannot be overridden. This is the constitutional filter — sacred axes, hard constraints.

**M1 (elastic intent layer).** Dynamic tuner. Adapts to noise via phase lock (PLL). Rephrases noisy inputs to fit M0's bounds. Absorbs perturbations. This is the adaptive processor — emergent axes, soft constraints.

**Resilience mechanism.** M1 proposes actions, M0 checks invariants, feedback refines M1's next proposal. Phase-lock loop. Resonance score = 1 - phase_error. Lock threshold > 0.8.

**Schema for construction:**
```python
class M1M0Governor:
    """Two-layer adaptive governor: M1 elastic + M0 plastic."""
    
    def __init__(self, m0_config, m1_config):
        self.m0 = GeometricGovernor(m0_config)   # fixed invariants
        self.m1 = AdaptiveProjector(m1_config)  # PLL elastic
        self.phase_error = 1.0
        self.lock_threshold = 0.8
    
    def process(self, input_signal):
        # M1 proposes a candidate action
        proposed = self.m1.project(input_signal)
        # M0 checks invariants
        if self.m0.violates(proposed):
            # Phase error: M1 needs to refine
            self.phase_error = self.m0.violation_distance(proposed)
            if self.phase_error > (1 - self.lock_threshold):
                return Refusal(reason='invariant_violation', phase_error=self.phase_error)
            # M1 refines (PLL step)
            self.m1.refine(input_signal, feedback=self.m0.violation_reason(proposed))
            return Refusal(reason='refining', phase_error=self.phase_error)
        # Locked — accept
        return Accept(proposed)
    
    @property
    def resonance(self):
        return 1.0 - self.phase_error
```

**Mathematical interpretation.** The M1-M0 pair implements a **fixed-point iteration** in the action space: M1 proposes x_{n+1}, M0 checks against invariant set I. If x ∉ I, project x back to I and add feedback to M1. This converges when the proposal lies in I (M0 lock).

**Use in SimSelf.** The cognitive loop's "Decide" stage runs M1-M0. M1 is the LLM-based projector (adaptive), M0 is the constitutional governor (geometric invariants). This is the cleanest pattern for wrapping an LLM as a frozen backbone with a learnable projection layer.

---

## 2. four primitives — Self, Authority, Agency, Identity (w29)

Bobby's defined schema for SimSelf's core:

**Self.** Persistent, accumulating subsystem. State vector + history buffer. Experiences via OperatorObjects (domain-specific interfaces: coding, robot, language). Bounded — no direct authority access; governor owns decisions.

**Authority.** External geometric governor. Invariant enforcement. SimSelf queries but cannot override. Constrained — read-only for SimSelf, write via approved ops.

**Agency.** Scoped action capacity. Selects ops within budget. Bounded by invariants (e.g., energy < threshold). SimSelf exercises via OperatorObjects but rejects unsafe (e.g., no unbounded recursion).

**Identity.** Immutable core ID + mutable refinement. Hash of initial state + accumulated lineage. Persistent across domains. Bounded — no fragmentation, shared across OperatorObjects.

**Schema for construction:**
```python
@dataclass
class SimSelfSubsystem:
    """Central SimSelf packet — single instance, multiple OperatorObjects."""
    id: str                              # immutable core ID
    embedding: np.ndarray                # self-embedding
    axes: Dict[str, float]               # Swedenborgian axes (Set A, emergent)
    history: List[StateChange]           # accumulated lineage
    operator_objects: List[OperatorObject]  # coding, robot, language, ...
    
    def query_authority(self, intent: TypedIntent) -> AuthorityResponse:
        """Read-only query to the geometric governor."""
        return authority.check(intent)
    
    def exercise_agency(self, op: OperatorObject, action: Action) -> ActionResult:
        """Exercise agency within budget + invariant constraints."""
        if op.budget < action.cost:
            return ActionResult.rejected('budget_exceeded')
        if not authority.allows(op, action):
            return ActionResult.rejected('authority_denied')
        result = op.execute(action)
        op.budget -= action.cost
        self.history.append(StateChange(op=op, action=action, result=result))
        return result
    
    def refine_identity(self, new_state_hash: str) -> None:
        """Append new state hash to identity lineage (mutable refinement)."""
        self.axes['lineage_length'] += 1
        self.axes['identity_hash'] = hash_combine(self.id, new_state_hash)
```

**Mathematical interpretation.** Self = stateful subsystem with memory. Authority = invariant-checking oracle (read-only). Agency = budgeted action space with constraints. Identity = monotonic lineage (only grows, never resets). The four primitives cleanly partition SimSelf's roles.

**Use in SimSelf.** All SimSelf code uses these four primitives. Authority is the M0 governor. Agency wraps OperatorObjects. Self holds the persistent state. Identity preserves provenance.

---

## 3. TypedIntent schema + 5 gate types (w33)

**TypedIntent.** Canonical action representation. Dataclass with:
- `intent_type` — one of OBSERVE, TRANSFORM, MERGE, MOVE, etc.
- `parameters` — dict with bounds, invariants
- `confidence` — float in [0, 1]
- `lineage` — source trace (which English input, which OperatorObject)
- `gate_results` — dict of 5 gate results

**5 gate types** (validation stages):
1. **Structural** — parse validity (does the intent match its type's structure?)
2. **Semantic** — meaning coherence (do the parameters make semantic sense?)
3. **Invariant** — field/physics checks (do the parameters respect M0 invariants?)
4. **Authority** — permission bounds (does SimSelf have authority to execute this intent?)
5. **Projection** — typability (does the intent map to a known OperatorObject action?)

Rejection at any gate. Each gate has a reason code. Confidence < 0.8 → automatic rejection (low confidence = unsafe).

**Schema for construction:**
```python
@dataclass
class TypedIntent:
    intent_type: str                     # OBSERVE, TRANSFORM, MERGE, MOVE, ...
    parameters: Dict[str, Any]           # bounds, invariants, etc.
    confidence: float                    # [0, 1]
    lineage: List[str]                   # source trace
    gate_results: Dict[str, GateResult]  # populated by validation
    
    def validate(self, governor: M0) -> 'TypedIntent':
        """Run all 5 gates; populate gate_results."""
        self.gate_results = {
            'structural': self.check_structural(),
            'semantic': self.check_semantic(),
            'invariant': governor.check_invariant(self),
            'authority': governor.check_authority(self),
            'projection': self.check_projection()
        }
        return self


class MTEEngine:
    """Pre-action layer: English → TypedIntent → governor."""
    
    def __init__(self, governor, embedding_model, type_classifier):
        self.governor = governor
        self.embedding_model = embedding_model
        self.type_classifier = type_classifier
    
    def compile(self, english_input: str) -> TypedIntent:
        """Translate English to TypedIntent via mini-LLM + rules."""
        embedding = self.embedding_model.encode(english_input)
        intent_type, confidence = self.type_classifier.predict(embedding)
        parameters = self.extract_parameters(embedding, intent_type)
        intent = TypedIntent(
            intent_type=intent_type,
            parameters=parameters,
            confidence=confidence,
            lineage=[english_input],
            gate_results={}
        )
        return intent.validate(self.governor)
    
    def is_acceptable(self, intent: TypedIntent) -> bool:
        """All 5 gates pass + confidence ≥ 0.8."""
        return all(r.passed for r in intent.gate_results.values()) and intent.confidence >= 0.8
```

**Mathematical interpretation.** Each gate is a binary classifier in the action space. The 5 gates form a sequential filter: an intent must pass all 5 to be executable. Confidence threshold (0.8) acts as a global guard. This is a **multi-stage validation pipeline** — each stage catches a different failure mode (malformed, incoherent, unsafe, unauthorized, untypable).

**Use in SimSelf.** Every English utterance that proposes an action becomes a TypedIntent, gets validated through the 5 gates, and is either accepted (executed) or refused (with reason). The MTE engine is the front door to action.

---

## 4. Sacred Library write rules (w34)

**Write conditions.** SimSelf commits a memory entry only if:
- `coherence > 0.8` — the entry fits with existing state
- `novelty > 0.5` — the entry is not redundant with existing entries
- `truth > 0.7` — the entry is verified (not hallucinated)
- `invariants_preserved` — no sacred-axis violations
- `lineage_traceable` — source can be traced

**Pruning.** Periodic pruning of low-confidence entries (confidence < 0.6). FIFO on overflow (max 1000 entries default).

**Conflict resolution.** Detect via:
1. Embedding distance to existing entries (similar but not identical)
2. Invariant clash (claims contradict each other)

Resolve by priority:
1. User preferences > commands (user authority highest)
2. Coherence-weighted (higher-coherence entry wins)
3. Fallback to query (ask user to disambiguate)

Log all resolutions for learning.

**Schema for construction:**
```python
class SacredLibrary:
    """Validated persistent memory (Bobby's "L" — Sacred Library)."""
    
    def __init__(self, max_size=1000, write_thresholds=None):
        self.entries = []
        self.max_size = max_size
        self.thresholds = write_thresholds or {
            'coherence': 0.8,
            'novelty': 0.5,
            'truth': 0.7,
            'min_confidence_for_prune': 0.6
        }
    
    def write(self, entry) -> bool:
        """Commit entry if all write conditions met."""
        coherence = self.compute_coherence(entry)
        novelty = self.compute_novelty(entry)
        truth = self.compute_truth(entry)
        if not (coherence > self.thresholds['coherence'] and
                novelty > self.thresholds['novelty'] and
                truth > self.thresholds['truth'] and
                self.invariants_preserved(entry) and
                self.lineage_traceable(entry)):
            return False
        # Conflict check
        conflicts = self.find_conflicts(entry)
        if conflicts:
            entry = self.resolve_conflicts(entry, conflicts)
        self.entries.append(entry)
        if len(self.entries) > self.max_size:
            self.prune()
        return True
    
    def find_conflicts(self, entry):
        """Embedding-similar entries with invariant clashes."""
        conflicts = []
        for existing in self.entries:
            distance = cosine(entry.embedding, existing.embedding)
            if distance < 0.3 and self.invariants_clash(entry, existing):
                conflicts.append(existing)
        return conflicts
    
    def resolve_conflicts(self, new, conflicts):
        """Priority: user prefs > commands, coherence-weighted, fallback query."""
        # For now, return new (highest coherence wins by recency)
        return new
    
    def prune(self):
        """Remove low-confidence entries (FIFO on overflow)."""
        self.entries = [e for e in self.entries 
                        if e.confidence >= self.thresholds['min_confidence_for_prune']]
        if len(self.entries) > self.max_size:
            self.entries = self.entries[-self.max_size:]  # FIFO
```

**Mathematical interpretation.** The Sacred Library is a **validated append-only memory** with explicit write conditions. The conditions (coherence > 0.8, novelty > 0.5, truth > 0.7) define what counts as "sacred" — only high-confidence, novel, verified entries are committed. This is the wisdom-ledger pattern from `sovereign-ai-core-c6.md` extended with quality gates.

**Use in SimSelf.** The Sacred Library is SimSelf's high-trust persistent memory. Different from the three-layer w23 memory architecture — Sacred Library is for validated, high-confidence knowledge that the governor approves. Three-layer memory holds everything (including untrusted); Sacred Library holds what passed the gates.

---

## 5. cross-cutting schemas

| schema | source | status | simself component |
|---|---|---|---|
| M1-M0 negotiation | w28 | rigorous | adaptive governor layer |
| Self/Authority/Agency/Identity | w29 | rigorous | core primitives |
| TypedIntent + 5 gates | w33 | rigorous | action validation pipeline |
| Sacred Library write rules | w34 | rigorous | validated memory |

---

## 6. what was stripped

- "w26 Option 2" (Grounded Semantic Primitives 20-50 atomic ops) — common pattern, no FieldCore-specific derivation. Not used.
- "w26 Option 3" (Code Loops as Language Bridge) — well-trodden, not FieldCore-specific. Not used.
- "w27 Distributed Node Prototype" (VisionStalk, ArmStalk, HandStalk) — embodied sketch, no derivation. Reference only.
- "w30 Adversarial Input" (the "you lout a boorish bear" example) — useful test case but not architecture. Not extracted.
- "w31 LLM Reasoning/Latent Emergence" — real thesis but speculative. Manifold view of cognition already implicit in FieldCore topology. Not extracted here.
- "w32 FieldCore IDE Fork" — already covered in `chorus-ide-design.md`. Not duplicated.
- "w35 Q3 Proactive Resilience" — control theory, useful but not core architecture. Reference only.

---

*Source: `Desktop/FieldCore/mte-typing-simself-primitives.md`. 4 schemas extracted (M1-M0, primitives, gates, library). Construction pseudocode for all 4. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/mte-simself-primitives-2026-09-05.md`.*