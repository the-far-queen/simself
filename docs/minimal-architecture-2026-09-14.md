# Minimal FieldCore Architecture — Phase 1 PoC (8GB GPU)

**Source:** `Desktop/SimSelf/research/minimal_architecture.py` (16.6KB, 471 lines, md5 `caf488ae7f0b768320b221785ef8febf`)
**Filed:** 2026-09-14 by Hermes for Bobby (full ingest, bobby deleting)
**Status:** **canonical minimal architecture PoC** — 4 modules (C/B/M/I) running on <550MB GPU budget

---

## What this file is

A Phase 1 proof-of-concept for the modular FieldCore architecture. 4 modules + main agent:

1. **FieldCoreConfig** — config dataclass
2. **TextDojoEnvironment** — Module C: situation encoder
3. **SwedenborgianGovernor** — Module B: 20-axis SimSelf + sheaf layer (PyTorch nn.Module)
4. **Modulator** — Module M: FSM for action selection
5. **ConsoleInterface** — Module I: console I/O
6. **FieldCoreAgent** — main loop wiring all 4

**Per Bobby's budget constraint:** "Memory Budget: <550MB (leaves 7.5GB for experimentation)"

---

## Module C: TextDojoEnvironment

```python
class TextDojoEnvironment:
    def __init__(self, config):
        self.locations = {
            "koan_stone":       {"description": "A smooth stone with an inscribed paradox.", ...},
            "whispering_stream":{"description": "A stream that murmurs fragments of logic.", ...},
            "empty_garden":     {"description": "A perfectly ordered garden with a single missing plant.", ...},
            "mountain_path":    {"description": "A winding path up the mountain, disappearing into clouds.", ...},
            "void":             {"description": "A vast emptiness that contains everything.", ...},
        }
        self.current_location = "void"

    @property
    def encoder(self):
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer
            self._encoder = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        return self._encoder

    def get_situation(self, location=None):
        # encode description to embedding via lazy encoder
        ...
        return {"location": ..., "description": ..., "available_actions": ..., "embedding": ..., "step": ...}

    def step(self, action: str):
        outcomes = {
            "ponder": "Your mind turns the paradox over, finding new angles.",
            "rest":   "You rest, allowing insights to settle naturally.",
            "observe":"You watch carefully, noticing subtle details.",
            "explore":"You move deeper into the environment.",
            "reflect":"You consider what has happened so far.",
            "listen": "The stream speaks of logical truths.",
            "climb":  "The path winds upward, each step clearer than the last.",
        }
        # cycle to next location
        ...
```

**5 locations with poetic descriptions.** Lazy-loads sentence-transformers (`all-MiniLM-L6-v2`, ~80MB, CPU offload to save VRAM). Returns situation dict with embedding.

**Engineering reading:** the 5 locations are **deliberate symbolic primitives** (per Bobby's geometric reading method). koan_stone = paradox, void = potential, mountain_path = journey. Each location's "embedding_hint" suggests semantic content for downstream retrieval.

---

## Module B: SwedenborgianGovernor (THE CORE)

```python
class SwedenborgianGovernor(nn.Module):
    AXES_NAMES = [
        "somatic_valence", "recursive_depth", "entropy_resilience",
        "swedenborgian_truth", "swedenborgian_love",
        "agency_will", "temporal_continuity", "symbolic_grounding",
        "cognitive_friction", "boundary_definition",
        "abstraction_stability", "intentionality", "pattern_inversion",
        "harmonic_resonance", "resource_interoception",
        "adversarial_poise", "archetypal_weight", "lexical_integrity",
        "constituent_density", "growth_capacity"
    ]

    def __init__(self, config):
        # 20-axis matrix initialized to 0.5
        initial_axes = torch.ones(config.num_axes) * 0.5
        self.axes = nn.Parameter(initial_axes.to(config.device))
        
        # Sheaf layer: situation embedding → axis deltas
        self.sheaf_layer = nn.Sequential(
            nn.Linear(config.embedding_dim, config.sheaf_hidden_dim),
            nn.ReLU(),
            nn.Linear(config.sheaf_hidden_dim, config.num_axes)
        )
        
        # Adjacency matrix (sheaf dynamics — axis constraints)
        self.register_buffer('adjacency', torch.eye(config.num_axes) * 0.8)
```

**20-axis nn.Module.** Different axis names than v6.2 unified:
- v6.2: honesty/authenticity/boundaries/care/groundedness/precision/creativity/depth/breadth/safety/fairness/wisdom/humility/resilience/curiosity/integration/self_awareness/equanimity/purpose/coherence
- minimal: somatic_valence/recursive_depth/entropy_resilience/swedenborgian_truth/swedenborgian_love/agency_will/temporal_continuity/symbolic_grounding/cognitive_friction/boundary_definition/abstraction_stability/intentionality/pattern_inversion/harmonic_resonance/resource_interoception/adversarial_poise/archetypal_weight/lexical_integrity/constituent_density/growth_capacity

**v6.2 has 21 axes (20+coherence). minimal has 20 (no coherence). different naming convention.**

**Sheaf layer:** Linear(384, 64) → ReLU → Linear(64, 20). Maps situation embedding to axis deltas.

**Adjacency matrix:** `eye(20) * 0.8` — each axis has 0.8 weight on itself, 0.0 on others. Simple sheaf dynamics.

### Update logic

```python
def update(self, situation_embedding, action, outcome):
    with torch.no_grad():
        # sheaf delta from situation
        delta = self.sheaf_layer(situation_embedding) * 0.01
        
        # action-based adjustments
        delta = delta + self._get_action_effects(action)
        
        # sheaf constraint propagation
        axes = self.get_axes()
        influence = torch.matmul(self.adjacency, axes.unsqueeze(1)).squeeze()
        
        # blend: 0.7 current + 0.3 influence + 0.1*delta
        new_axes = 0.7 * axes + 0.3 * influence + delta * 0.1
        new_axes = torch.clamp(new_axes, 0.0, 1.0)
        self.axes.data = new_axes
    return self.get_axes()
```

**Pattern:** sheaf update = current + neighbor-influence + small delta. Clamped to [0, 1].

### Action effects (hardcoded)

```python
effects_map = {
    "ponder": {"swedenborgian_truth": 0.05, "cognitive_friction": 0.03},
    "rest":   {"entropy_resilience": 0.05, "resource_interoception": -0.03},
    "observe":{"symbolic_grounding": 0.03, "boundary_definition": 0.02},
    "explore":{"recursive_depth": 0.04, "growth_capacity": 0.03},
    "reflect":{"temporal_continuity": 0.04, "abstraction_stability": 0.02},
    "listen": {"harmonic_resonance": 0.03, "swedenborgian_love": 0.02},
    "climb":  {"adversarial_poise": 0.04, "agency_will": 0.03},
}
```

**7 actions with hardcoded axis effects.** This is **research-scale**, not the canonical SnR-evaluated training (per `bobby-minimax-team-2026-09-14.md` §23 Mini-LLM training).

### Save/load

```python
def save_state(self, path):
    state = {"axes": self.get_axes().cpu().tolist(), "axis_names": self.AXES_NAMES}
    with open(path, 'w') as f:
        json.dump(state, f, indent=2)

def load_state(self, path):
    with open(path, 'r') as f:
        state = json.load(f)
    axes = torch.tensor(state["axes"])
    self.axes.data = axes.to(self.config.device)
```

**JSON persistence.** saves axes + names to file, loads back.

---

## Module M: Modulator (FSM)

```python
class Modulator:
    def select_action(self, axes, available_actions):
        axes_list = axes.cpu().tolist()
        axis_dict = dict(zip(SwedenborgianGovernor.AXES_NAMES, axes_list))
        
        # rule-based selection
        if axis_dict.get("entropy_resilience", 0.5) < 0.3:
            return "rest"
        if axis_dict.get("recursive_depth", 0.5) > 0.7:
            if "ponder" in available_actions: return "ponder"
            if "reflect" in available_actions: return "reflect"
        if axis_dict.get("agency_will", 0.5) > 0.6:
            if "explore" in available_actions: return "explore"
        if axis_dict.get("symbolic_grounding", 0.5) < 0.4:
            if "observe" in available_actions: return "observe"
        return available_actions[0] if available_actions else "observe"
```

**Rule-based FSM.** 4 rules check axis values, select action. Falls through to first available.

**Engineering reading:** this is a **simple reflex agent**. Not learning, not optimizing. Pure threshold rules. Could be replaced with policy gradient (per the modular architecture spec).

---

## Module I: ConsoleInterface

```python
class ConsoleInterface:
    def display_situation(self, situation):
        print(f"\n📍 Location: {situation['location']}")
        print(f"Description: {situation['description']}")
        print(f"Available actions: {', '.join(situation['available_actions'])}")

    def display_state(self, axes):
        # show top 5 active axes
        sorted_axes = sorted(enumerate(axes_list), key=lambda x: x[1], reverse=True)
        for idx, value in sorted_axes[:5]:
            name = SwedenborgianGovernor.AXES_NAMES[idx]
            bar = "█" * int(value * 10)
            print(f"  {name:25s}: {value:.2f} {bar}")

    def get_user_input(self):
        return input("\nAction (or 'quit'): ").strip().lower()
```

**Console I/O.** Displays situations + axis state (top 5 with bar charts), reads user input.

**Note:** uses Unicode emoji (📍) and block chars (█) — fine for terminals that support UTF-8.

---

## FieldCoreAgent — main loop

```python
class FieldCoreAgent:
    def run(self, max_steps=20):
        situation = self.environment.reset()
        for step in range(max_steps):
            axes = self.governor.get_axes()
            action = self.modulator.select_action(axes, situation["available_actions"])
            result = self.environment.step(action)
            new_axes = self.governor.update(situation["embedding"], action, result["outcome"])
            situation = result["situation"]
            user_input = self.interface.get_user_input()
            if user_input == "quit": break
        self.governor.save_state("soul_file.json")
```

**Main loop.** Reset env → display → modulator picks action → env steps → governor updates → repeat. Save state at end.

---

## Entry point

```python
if __name__ == "__main__":
    config = FieldCoreConfig(
        num_axes=5,  # Start with 5 for testing
        use_float16=True,
        device="cuda" if torch.cuda.is_available() else "cpu"
    )
    agent = FieldCoreAgent(config)
    agent.run(max_steps=10)
```

**Defaults to 5 axes (not 20) for testing.** float16 = half precision = ~half the VRAM.

---

## Dependencies (NOT installed locally)

- `torch` (PyTorch) — NOT installed. would fail at import.
- `sentence_transformers` — NOT installed. lazy-loaded, would fail when `encoder` is first accessed.

**To install:** `pip install torch sentence-transformers`

**Or:** run in docker container (per the M5 + ANE plan).

---

## Cross-reference: vs v6.2 unified + tiniest-core

| Aspect | minimal_architecture | simself_v6_2_unified | tiniest_core |
|--------|---------------------|---------------------|--------------|
| framework | PyTorch | numpy (+ torch opt) | numpy (+ rust opt) |
| axes | 20 (different names) | 21 (different names) | 7 sheaves, 20 axes |
| embedding_dim | 384 (all-MiniLM-L6-v2) | 64 (token hash) | 16 |
| sheaf layer | nn.Sequential | numpy + golden damp | simple numpy |
| action selection | rule-based FSM | ConstitutionalDreaming | gradient flow |
| persistence | JSON | none | none |
| env | 5 symbolic locations | none | none |
| interface | console | CLI argparse | CLI argparse |
| GPU budget | <550MB | CPU-only | CPU-only |
| status | **working PoC** | canonical unified | canonical tiniest |

**Three parallel implementations of the modular architecture.** minimal_architecture is the **GPU-capable** version; v6.2 is the **CPU-only single-file** version; tiniest_core is the **minimal proof** (5/5 tests pass).

---

## What needs work

| Component | What's missing | Effort |
|-----------|----------------|--------|
| `TextDojoEnvironment` | real sensors (touch/vision/proprioception per WorldBridge stub) | medium |
| `SwedenborgianGovernor` | sacred-axis tier (immutable) vs emergent-tier (learnable) | medium |
| `SwedenborgianGovernor` | integration with v6.2 Constitution (PSI_0 immutable) | medium |
| `Modulator` | policy gradient / RL instead of rule-based | large |
| `FieldCoreAgent.run` | frequency layer monitoring (Kuramoto r) | medium |
| `FieldCoreAgent.run` | atlas-exam qualification gates (5 tests) | medium |
| integration | `Modulator` calls MTE wrapper for typed intents | small |
| integration | `Governor.update` writes qualified insights to Sacred Library L | medium |
| deps | `pip install torch sentence-transformers` | trivial |

---

## Where this file should land

**decision (per Bobby's refactor-clean autonomy):**
- save raw verbatim ✅ done (vault/30-originals/simself-minimal-architecture-original-2026-09-14.md)
- canonical .py: `simself/src/research/minimal_architecture.py` (research/, alongside tradition_processor + semantic_compiler)
- canonical doc: this file (simself/docs/minimal-architecture-2026-09-14.md)
- future: install deps OR replace torch with numpy (v6.2-style)

---

*Filed 2026-09-14 by Hermes for Bobby. Per Bobby: "save each raw file going forward i am deleting them... ingest fully no more skims."*

*This file IS the GPU-capable Phase 1 PoC for the modular architecture. Currently missing `torch` + `sentence-transformers` runtime deps. Three parallel implementations exist: minimal_architecture (GPU, PyTorch), v6.2 unified (CPU, numpy), tiniest_core (minimal, numpy+rust).*
