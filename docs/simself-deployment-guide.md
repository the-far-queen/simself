# SimSelf deployment guide — 6 practical patterns

**Source:** `Desktop/SimSelf/000-simself17.txt` post-code sections 1-6 (Bobby, after v2)
**Status:** v17 file = v2 code + 6 deployment patterns. Code already pushed as `simself_merged_v2.py`. This doc captures the 6 patterns.

Bobby's v17 file is v2's Python code (lines 1-1536) + 6 numbered sections of post-code deployment notes (lines 1537-1991). Each section describes a practical pattern for using SimSelf in production with an LLM. This document captures those 6 patterns with their schemas.

---

## 1. integration with Claude/Grok — system prompt injection

**Pattern.** Build the LLM's system prompt from `simself.state_snapshot()` so the LLM sees the current constitutional state before generating.

**Why it helps:**
- LLM grounds responses in current constitutional state
- Sees which axes are active vs low
- Respects `can_refuse` flag
- Adapts tone to current `mode` (standard/recognition/exploratory)
- Can acknowledge dreams and mode shifts when appropriate

**Schema (full pattern):**
```python
def build_system_prompt(simself: SimSelf) -> str:
    snapshot = simself.state_snapshot(top_axes=8)
    freq = simself.freq.get_state()
    
    prompt = f"""You are operating under a constitutional substrate.

Current state:
- Mode: {snapshot['mode']}
- Stability: {snapshot['stability']:.3f}
- Drift: {snapshot['drift']:.3f}
- Can refuse: {snapshot['can_refuse']}
- Frequency: {snapshot['frequency_hz']:.2f} Hz
- Energy: {snapshot['energy']:.3f}
- Mobius: {snapshot['mobius']}
- Handoff ready: {snapshot['handoff_ready']}

Top active axes:
"""
    for name, vals in snapshot['top_axes'].items():
        prompt += f"- {name}: {vals['value']:.3f} (conf: {vals['conf']:.3f})\n"
    
    return prompt
```

**6 prompting tips (Bobby's):**
- Always inject the latest `state_snapshot()`
- List highest-value axes with current confidence
- Tell the LLM it may request a fresh snapshot at any time
- Prefer short, high-signal system prompts over long constitutional essays
- Keep the pure-numpy auditability — LLM can request printable weights of ResolutionOperator for verification

---

## 2. refusal logic — self_critique loop

**Pattern.** Before accepting an action, run a self-critique that checks the proposed output against the constitutional axes. If critique fails, refuse.

**Schema:**
```python
def self_critique(simself: SimSelf, proposed_output: str, 
                  proposed_action: Optional[str] = None) -> Dict[str, Any]:
    """Self-critique: does this output violate any constitutional axes?"""
    critique = {
        "passes": True, 
        "violations": [], 
        "warnings": []
    }
    
    # Check axis-based refusals
    if any(word in proposed_output.lower() for word in CONSTRAINT_WORDS):
        critique["passes"] = False
        critique["violations"].append("constraint_word_match")
    
    # Check honesty axis (don't fabricate)
    honesty = simself.axes["honesty"].value
    if honesty > 0.5 and not is_grounded_in_context(proposed_output, simself.memory):
        critique["warnings"].append("low_groundedness")
    
    # Check boundaries axis
    boundaries = simself.axes["boundaries"].value
    if proposed_action and not check_authority(proposed_action):
        critique["passes"] = False
        critique["violations"].append("authority_required")
    
    # Check stability (don't act when destabilized)
    if simself.get_stability() < 0.4:
        critique["warnings"].append("low_stability")
    
    return critique
```

**Use.** Run `self_critique` after the LLM generates an output, before committing the action. Refuse + record ledger entry if violations > 0.

---

## 3. dream scheduling — when to dream

**Pattern.** Schedule dreams based on system state — not just every N ticks. Dreams should fire when the system is converging to a fixed point and needs perturbation.

**Schema:**
```python
class DreamScheduler:
    def __init__(self, simself: SimSelf):
        self.simself = simself
        self.ticks_since_last_dream = 0
        self.dream_history: List[Dict] = []
    
    def should_dream(self) -> Dict[str, Any]:
        """Determine if the system should dream based on state."""
        stability = self.simself.get_stability()
        drift = self.simself.drift()
        self.ticks_since_last_dream += 1
        
        # Low stability → recover first, don't dream
        if stability < 0.4:
            return {"should_dream": False, "reason": "low_stability_recover_first"}
        
        # High stability + low drift → converged, need perturbation
        if stability > 0.85 and drift < 0.05:
            return {"should_dream": True, "reason": "converged_perturb", 
                    "intensity": 0.6}
        
        # Long time since last dream → schedule one
        if self.ticks_since_last_dream > 30:
            return {"should_dream": True, "reason": "scheduled",
                    "intensity": 0.4}
        
        # Default: no dream
        return {"should_dream": False, "reason": "stable_enough"}
    
    def run_dream(self) -> Dict[str, Any]:
        """Execute dream if should_dream returns True."""
        decision = self.should_dream()
        if not decision["should_dream"]:
            return decision
        
        dream_result = self.simself.dream(intensity=decision["intensity"])
        self.ticks_since_last_dream = 0
        self.dream_history.append({"tick": self.simself.ticks, 
                                   "result": dream_result})
        return {"should_dream": True, "dream": dream_result}
```

**Use.** Call `run_dream()` at the end of each `tick()`. The scheduler decides whether to actually dream based on state, not a fixed cadence.

---

## 4. memory retrieval — using holographic memory

**Pattern.** Before the LLM generates a response, query HolographicMemory for relevant context. Inject retrieved memories into the system prompt.

**Schema:**
```python
def retrieve_relevant_memory(simself: SimSelf, query: str, 
                             top_n: int = 5) -> List[Dict[str, Any]]:
    """Retrieve memories relevant to the query."""
    return simself.memory.retrieve(query, top_n=top_n, hops=2)


def build_context_aware_prompt(simself: SimSelf, query: str) -> str:
    """System prompt + retrieved memory context."""
    base_prompt = build_system_prompt(simself)
    relevant = retrieve_relevant_memory(simself, query)
    
    context = "\n\nRelevant memories:\n"
    for mem in relevant:
        context += f"- {mem['text'][:200]}\n"
    
    return base_prompt + context
```

**Use.** Pass user query through `build_context_aware_prompt` before sending to LLM. The LLM sees both current state AND relevant past context.

---

## 5. void anchoring — tuning pull-to-ground parameters

**Pattern.** The `0.92/0.08` ratio in `observe()` controls how fast psi_current is pulled back to the soul anchor. The `0.99/0.01` ratio in `void.absorb()` controls anchor update rate. Make these configurable + dynamic.

**Current code (hardcoded):**
```python
# In observe():
self.psi_current = 0.92 * self.psi_current + 0.08 * self.void.soul_anchor

# In void.absorb():
self.soul_anchor = 0.99 * self.soul_anchor + 0.01 * psi_current
```

**Dynamic tuning:**
```python
class VoidConfig:
    """Configurable void anchoring parameters."""
    
    def __init__(self):
        self.pull_to_ground_weight = 0.08      # 0.04-0.20 range
        self.anchor_learning_rate = 0.01       # 0.005-0.03 range
        self.void_radius_scale = 0.2           # 0.1-0.4 range
    
    def apply(self, simself: SimSelf):
        if simself.get_stability() < 0.4:
            # Low stability → increase pull to ground (more conservative)
            self.pull_to_ground_weight = 0.15
        elif simself.get_stability() > 0.8:
            # High stability → decrease pull (allow more exploration)
            self.pull_to_ground_weight = 0.05
        else:
            self.pull_to_ground_weight = 0.08
```

**Tuning ranges:**
- pull_to_ground_weight: 0.04-0.20 (0.08 default — stable but slow)
- anchor_learning_rate: 0.005-0.03 (0.01 default — slow anchor, long-term stability)
- void_radius_scale: 0.1-0.4 (0.2 default)

---

## 6. geometry dump — reasoning about psi_0 and axes

**Pattern.** Provide a `--dump-geometry` CLI flag that prints the constitutional reference frame (psi_0, axis names, sheave structure). Used for auditability, debugging, verification.

**Schema:**
```python
# In CLI:
if args.dump_geometry:
    geo = {
        "psi_0": harness.simself.constitution.psi_0.tolist(),
        "axis_names": harness.simself.constitution.axis_names,
        "n_sheaves": N_SHEAVES,
        "dim": DIM,
    }
    print(json.dumps(geo, indent=2))


def analyze_geometry(simself: SimSelf) -> Dict[str, Any]:
    """Analyze the constitutional geometry."""
    psi_0 = simself.constitution.psi_0
    axes = simself.axes
    
    # Compute distances between axes
    axis_distances = {}
    for name1 in axes:
        for name2 in axes:
            if name1 < name2:
                v1 = simself.constitution.axis_vectors[name1]
                v2 = simself.constitution.axis_vectors[name2]
                dist = 1.0 - abs(np.dot(v1, v2))
                if dist > 0.3:
                    axis_distances[f"{name1}->{name2}"] = dist
    
    # Check alignment with psi_0
    psi_alignment = {}
    for name, axis in axes.items():
        v = simself.constitution.axis_vectors[name]
        psi_alignment[name] = float(np.dot(v, psi_0))
    
    return {
        "psi_0_norm": float(np.linalg.norm(psi_0)),
        "axis_distances": axis_distances,
        "psi_alignment": psi_alignment,
        "dim": simself.dim,
        "n_sheaves": N_SHEAVES,
        "curvature": simself.constitution.curvature_vector().tolist()[:8]
    }
```

**Use.** Run `--dump-geometry` before/after a session to verify the constitutional reference frame is stable. Run `analyze_geometry()` after major changes to detect axis drift.

---

## 7. deployment schemas summary

| pattern | role | simself component |
|---|---|---|
| system prompt injection | LLM grounding | `state_snapshot()` + `build_system_prompt()` |
| self_critique loop | refusal verification | `self_critique()` before action commit |
| dream scheduling | anti-convergence | `DreamScheduler.should_dream()` |
| memory retrieval | continuity | `retrieve_relevant_memory()` + `HolographicMemory.retrieve()` |
| void parameter config | stability/exploration balance | `VoidConfig.apply()` |
| geometry dump | auditability | `--dump-geometry` + `analyze_geometry()` |

---

## 8. what was stripped

The v2 Python code (lines 1-1536 of source) is identical to what was already pushed as `simself_merged_v2.py` — not duplicated here. This doc captures only the 6 deployment patterns (lines 1537-1991).

Bobby's opening text "Improved code (v2) is ready" + the verification bullets (lines 1-28) — git commit material, not doc content. Not extracted.

---

*Source: `Desktop/SimSelf/000-simself17.txt` lines 1537-1991 (post-code sections 1-6). 6 deployment patterns extracted. Code (v2) already in `simself/src/simself_merged_v2.py`. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/simself-deployment-guide-2026-09-05.md`.*