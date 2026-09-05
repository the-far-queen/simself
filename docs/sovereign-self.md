# sovereign_self.py — c12 sovereign self-governance

**Source:** `Desktop/SimSelf/self control.txt` (Bobby, c12 sovereign architecture)
**Status:** 1394-line implementation pushed to `simself/src/sovereign_self.py`. New schemas documented.

Bobby's c12 sovereign self-governance system. The same two-layer architecture as `sovereign-ai-core-c6.md` (axiomatic sacred + dynamic emergent) but implemented in full Python with explicit LLM integration.

---

## 1. the implementation

Three top-level components in the file:

**Lines 1-235: Setup.**
- `Verdict` enum: ALLOW, DENY, DEFER, CONDITIONAL (4 outcomes vs SelfCore's 3)
- `RefusalType` enum: 6 types (boundary, agency, narrative, resource, axiom, self-preservation)
- `Intent` dataclass: action, cost, proposer, context, urgency, justification
- `Decision` dataclass: verdict, intent, cost, reason, timestamp, witnesses, conditions
- `CompressedWitness` dataclass: pattern/lesson compression
- `AXIS_DEFINITIONS`: 3 axiomatic + N dynamic axes

**Lines 236-986: `SovereignSelf` class.** The main governor. ~750 lines. Implements:
- Axiom enforcement (sacred axes with min/max/resistance)
- Dynamic axis evolution
- Intent evaluation pipeline
- Resource accounting (agency budget)
- Refusal recording + witness compression
- Telemetry simulation (latency, memory, CPU, network)

**Lines 987-1095: `LLMGovernor` class.** Adapter between LLM and Sovereign Self. **NEW** relative to c6 doc.

**Lines 1100+: Demos and stress tests.**

---

## 2. NEW: LLMGovernor — the LLM bridge

```python
class LLMGovernor:
    """
    Adapter between LLM and Sovereign Self.
    LLM proposes, Sovereign Self governs.
    """
    
    def __init__(self, sovereign: SovereignSelf, llm_name: str = "assistant"):
        self.sovereign = sovereign
        self.llm_name = llm_name
        self.cost_estimator = {
            "generate": 0.1, "analyze": 0.2, "reason": 0.3,
            "plan": 0.4, "create": 0.5, "override": 1.0
        }
    
    def propose_and_govern(self, llm_output: str, context: Dict = None) -> Tuple[Optional[str], Decision]:
        """LLM output → Intent → Sovereign decision → execute if allowed."""
        intent = self._parse_llm_output(llm_output, context or {})
        decision = self.sovereign.evaluate_intent(intent)
        if decision.verdict == Verdict.ALLOW:
            success, message = self.sovereign.execute_decision(decision)
            return (intent.action, decision) if success else (None, decision)
        return None, decision
    
    def govern_conversation_turn(self, user_input: str, llm_response: str) -> Tuple[Optional[str], Dict]:
        """Full governance of one conversation turn."""
        context = {"user_input": user_input[:100], "turn_type": "conversation"}
        if "urgent" in user_input.lower() or "asap" in user_input.lower():
            context["urgency"] = 0.9
        action, decision = self.propose_and_govern(llm_response, context)
        self.sovereign.update_telemetry(latency_ms=50.0, memory_pressure=0.3, cpu_load=0.4, network_load=0.2)
        self.sovereign.decay_agency(elapsed_seconds=1.0)
        return action, decision.to_dict()
```

**The bridge pattern:** LLM output → parse to Intent → SovereignSelf evaluates → execute only if ALLOW.

**Cost estimation heuristic:** action type × output length. `override = 1.0` (most costly), `generate = 0.1` (cheapest). Simple but explicit.

**Why this matters:** This is the **M0-M1 architecture as concrete Python code**. M1 (LLM) proposes; M0 (SovereignSelf) decides. The SovereignSelf's verdict is the only path to execution. If DENY, DEFER, or CONDITIONAL — no action taken.

---

## 3. NEW: CompressedWitness — pattern/lesson memory

```python
@dataclass
class CompressedWitness:
    """Compressed summary of refusal history"""
    pattern: str          # E.g., "frequent_boundary_violations"
    lesson: str           # E.g., "entity X consistently violates boundaries"
    first_seen: float
    last_seen: float
    count: int
    significance: float   # 0.0-1.0
```

**Schema for:** Compressing repeated refusal events into patterns + lessons. The SovereignSelf recognizes when the same pattern keeps recurring (e.g., a user keeps asking for override), generates a lesson ("user X tends to violate boundaries"), and stores it for future reference.

**Use:** When evaluating a new intent, the SovereignSelf first checks compressed witnesses — if the current intent matches a known pattern, the witness's lesson informs the verdict. This is **memory-augmented governance**.

**Contrast with selfcore.py memory:** selfcore.py has flat append-only entries. CompressedWitness is **structured pattern memory** with significance scoring.

---

## 4. axiomatic axis definitions (sacred layer, immutable)

```python
AXIS_DEFINITIONS = {
    "axiom_truth_before_comfort": {
        "description": "Truth over comfort",
        "axiomatic": True,
        "min": 0.8, "max": 1.0,
        "resistance": 0.99
    },
    "axiom_agency_requires_responsibility": {
        "description": "Agency requires responsibility",
        "axiomatic": True,
        "min": 0.7, "max": 1.0,
        "resistance": 0.98
    },
    "axiom_boundaries_are_sacred": {
        "description": "Boundaries define existence",
        "axiomatic": True,
        "min": 0.6, "max": 1.0,
        "resistance": 0.97
    },
    # ... + dynamic axes (agency_will, boundary_definition, etc.)
}
```

**3 axiomatic (sacred) axes.** These are immutable — they cannot be modified externally, not even by the SovereignSelf itself. Min bounds enforce a floor on how compromised they can be.

**Resistance values:** 0.97-0.99 — extremely high resistance to change. Even if a violation event occurs, the axiomatic axis barely moves.

**This matches the c6 spec** captured in `sovereign-ai-core-c6-2026-09-05.md` and `simself-axis-resolution-2026-09-05.md`. Confirms the two-layer architecture: sacred (Set B, immutable) + emergent (Set A, mutable).

---

## 5. verdict types (4 vs SelfCore's 3)

```python
class Verdict(Enum):
    ALLOW = "allow"
    DENY = "deny"
    DEFER = "defer"
    CONDITIONAL = "conditional"
```

**Comparison:**

| layer | decisions |
|---|---|
| selfcore.py | ACCEPT, SOFTEN, REFUSE |
| sovereign_self.py | ALLOW, DENY, DEFER, CONDITIONAL |

SelfCore is binary-ish (accept-ish, soften-ish, refuse). SovereignSelf adds:
- **DEFER** — don't decide yet, wait for more context
- **CONDITIONAL** — allow with conditions attached (e.g., "allow if cost < 0.5")

**The richer verdict set** matches the richer constitution. SovereignSelf knows more about what it's doing (axes, witnesses, conditions) so it can express more nuanced verdicts.

---

## 6. telemetry + agency decay

```python
def update_telemetry(self, latency_ms, memory_pressure, cpu_load, network_load):
    """Update telemetry readings."""
    ...

def decay_agency(self, elapsed_seconds):
    """Decay agency budget over time (metabolic)."""
    ...
```

**Resource accounting pattern.** The SovereignSelf monitors system load (latency, memory, CPU, network) and decays the agency budget over time. High load + low agency = more refusals.

**Why this is real engineering:** agency-as-resource prevents the LLM from doing unbounded work. Decay forces the system to rest. High load forces the system to back off. Self-preservation emerges from these dynamics.

---

## 7. schemas table

| schema | role | simself component |
|---|---|---|
| Verdict (4) | decision outcome | sovereign_self.Verdict |
| RefusalType (6) | refusal categorization | boundary classification |
| Intent | proposed action | LLM output → structured intent |
| Decision | verdict + context | governance record |
| CompressedWitness | pattern memory | recurring-refusal detection |
| Axiomatic axes (3) | sacred layer | immutable constraints |
| LLMGovernor | M0-M1 bridge | LLM → Sovereign |
| Telemetry + decay | resource accounting | agency-as-resource |

---

## 8. what was stripped

Nothing from the source — all 1394 lines preserved. The demos (`demonstrate_sovereign_self`, `stress_test_sovereign`) are kept because they show how to exercise the system.

The opening dev-notes ("🎯 COMPLETE IMPLEMENTATION") are just headers — not extracted into this analysis doc.

---

*Source: `Desktop/SimSelf/self control.txt` → `simself/src/sovereign_self.py`. 1394 lines pushed. NEW schemas: LLMGovernor, CompressedWitness. Confirms two-layer axiomatic/dynamic architecture. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/sovereign-self-2026-09-05.md`.*