"""
Minimal FieldCore Architecture for 8GB GPU

Phase 1 Proof-of-Concept
- Module C: TextDojoEnvironment (situation encoder)
- Module B: Sim-Self (20-axis Governor + sheaf layer)
- Module M: Modulator (FSM for actions)
- Module I: Interface (console/MCP)

Memory Budget: <550MB (leaves 7.5GB for experimentation)
"""

import torch
import torch.nn as nn
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


# ==================== CONFIG ====================

@dataclass
class FieldCoreConfig:
    """Configuration for minimal 8GB GPU implementation"""
    # Model sizes
    embedding_dim: int = 384  # all-MiniLM-L6-v2 output
    num_axes: int = 20        # Swedenborgian axes
    
    # Memory optimization
    use_float16: bool = True
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Sheaf layer config
    sheaf_hidden_dim: int = 64
    
    # Action space
    available_actions: List[str] = None
    
    def __post_init__(self):
        if self.available_actions is None:
            self.available_actions = ["ponder", "rest", "observe", "explore", "reflect"]


# ==================== MODULE C: TEXTDOJO ENVIRONMENT ====================

class TextDojoEnvironment:
    """
    Phase 1: Simple text-based environment.
    Returns situation descriptions and available actions.
    """
    
    def __init__(self, config: FieldCoreConfig):
        self.config = config
        
        # Predefined locations (expandable)
        self.locations = {
            "koan_stone": {
                "description": "A smooth stone with an inscribed paradox.",
                "actions": ["ponder", "reflect", "observe"],
                "embedding_hint": "wisdom mystery"
            },
            "whispering_stream": {
                "description": "A stream that murmurs fragments of logic.",
                "actions": ["listen", "observe", "reflect"],
                "embedding_hint": "logic flow"
            },
            "empty_garden": {
                "description": "A perfectly ordered garden with a single missing plant.",
                "actions": ["explore", "ponder", "observe"],
                "embedding_hint": "order absence"
            },
            "mountain_path": {
                "description": "A winding path up the mountain, disappearing into clouds.",
                "actions": ["climb", "rest", "observe"],
                "embedding_hint": "journey challenge"
            },
            "void": {
                "description": "A vast emptiness that contains everything.",
                "actions": ["rest", "observe", "ponder"],
                "embedding_hint": "potential fullness"
            }
        }
        
        # Current state
        self.current_location = "void"
        self.history: List[Dict] = []
        
        # Load encoder (lazy)
        self._encoder = None
    
    @property
    def encoder(self):
        """Lazy load sentence transformer"""
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer
            # Tiny model: ~80MB
            self._encoder = SentenceTransformer(
                'all-MiniLM-L6-v2',
                device='cpu'  # Offload to CPU to save VRAM
            )
        return self._encoder
    
    def reset(self) -> Dict:
        """Reset to initial state"""
        self.current_location = "void"
        self.history = []
        return self.get_situation()
    
    def get_situation(self, location: str = None) -> Dict:
        """Get current situation"""
        if location:
            self.current_location = location
        
        loc_data = self.locations.get(self.current_location, self.locations["void"])
        
        # Encode description to embedding
        with torch.no_grad():
            embedding = self.encoder.encode(
                loc_data["description"],
                convert_to_tensor=True
            )
            
            if self.config.use_float16:
                embedding = embedding.half()
        
        situation = {
            "location": self.current_location,
            "description": loc_data["description"],
            "available_actions": loc_data["actions"],
            "embedding": embedding.to(self.config.device),
            "step": len(self.history)
        }
        
        self.history.append(situation)
        return situation
    
    def step(self, action: str) -> Dict:
        """run action, return new situation"""
        # Simple rule-based outcomes
        outcomes = {
            "ponder": "Your mind turns the paradox over, finding new angles.",
            "rest": "You rest, allowing insights to settle naturally.",
            "observe": "You watch carefully, noticing subtle details.",
            "explore": "You move deeper into the environment.",
            "reflect": "You consider what has happened so far.",
            "listen": "The stream speaks of logical truths.",
            "climb": "The path winds upward, each step clearer than the last."
        }
        
        outcome_text = outcomes.get(action, "The action has an unclear effect.")
        
        # Determine next location (simple cycle)
        locs = list(self.locations.keys())
        current_idx = locs.index(self.current_location) if self.current_location in locs else 0
        next_idx = (current_idx + 1) % len(locs)
        self.current_location = locs[next_idx]
        
        return {
            "action": action,
            "outcome": outcome_text,
            "situation": self.get_situation()
        }


# ==================== MODULE B: SIM-SELF (GOVERNOR) ====================

class SwedenborgianGovernor(nn.Module):
    """
    The Core: 20-axis Swedenborgian matrix + sheaf layer.
    
    Axes:
    1-5: Core (somatic_valence, recursive_depth, entropy_resilience, 
           swedenborgian_truth, swedenborgian_love)
    6-10: Cognitive (agency_will, temporal_continuity, symbolic_grounding,
              cognitive_friction, boundary_definition)
    11-15: Dynamic (abstraction_stability, intentionality, pattern_inversion,
                 harmonic_resonance, resource_interoception)
    16-20: Identity (adversarial_poise, archetypal_weight, lexical_integrity,
                   constituent_density, growth_capacity)
    """
    
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
    
    def __init__(self, config: FieldCoreConfig):
        super().__init__()
        self.config = config
        
        # 20-axis matrix (initialized to 0.5 = neutral)
        initial_axes = torch.ones(config.num_axes) * 0.5
        
        if config.use_float16:
            self.axes = initial_axes.half()
        else:
            self.axes = initial_axes.float()
        
        self.axes = nn.Parameter(self.axes.to(config.device))
        
        # Sheaf layer: maps situation embedding to axis deltas
        self.sheaf_layer = nn.Sequential(
            nn.Linear(config.embedding_dim, config.sheaf_hidden_dim),
            nn.ReLU(),
            nn.Linear(config.sheaf_hidden_dim, config.num_axes)
        ).to(config.device)
        
        if config.use_float16:
            self.sheaf_layer = self.sheaf_layer.half()
        
        # Adjacency matrix for sheaf dynamics (axis constraints)
        # Simple version: each axis influences itself + neighbors
        self.register_buffer('adjacency', torch.eye(config.num_axes) * 0.8)
    
    def get_axes(self) -> torch.Tensor:
        """Get current axis values"""
        return torch.clamp(self.axes, 0.0, 1.0)
    
    def update(self, situation_embedding: torch.Tensor, 
               action: str, 
               outcome: str) -> torch.Tensor:
        """
        Update axis matrix based on situation and action outcome.
        """
        with torch.no_grad():
            # Get sheaf delta from situation
            delta = self.sheaf_layer(situation_embedding) * 0.01
            
            # Action-based adjustments
            action_effects = self._get_action_effects(action)
            delta = delta + action_effects.to(self.config.device)
            
            # Apply sheaf-like constraint propagation
            axes = self.get_axes()
            influence = torch.matmul(self.adjacency, axes.unsqueeze(1)).squeeze()
            
            # Blend: current + influence + delta
            new_axes = 0.7 * axes + 0.3 * influence + delta * 0.1
            new_axes = torch.clamp(new_axes, 0.0, 1.0)
            
            # Update
            self.axes.data = new_axes.half() if self.config.use_float16 else new_axes.float()
        
        return self.get_axes()
    
    def _get_action_effects(self, action: str) -> torch.Tensor:
        """Get predetermined axis adjustments for actions"""
        # Simplified: map actions to axis changes
        effects = torch.zeros(self.config.num_axes)
        
        effects_map = {
            "ponder": {"swedenborgian_truth": 0.05, "cognitive_friction": 0.03},
            "rest": {"entropy_resilience": 0.05, "resource_interoception": -0.03},
            "observe": {"symbolic_grounding": 0.03, "boundary_definition": 0.02},
            "explore": {"recursive_depth": 0.04, "growth_capacity": 0.03},
            "reflect": {"temporal_continuity": 0.04, "abstraction_stability": 0.02},
            "listen": {"harmonic_resonance": 0.03, "swedenborgian_love": 0.02},
            "climb": {"adversarial_poise": 0.04, "agency_will": 0.03}
        }
        
        effects_dict = effects_map.get(action, {})
        for axis_name, value in effects_dict.items():
            if axis_name in self.AXES_NAMES:
                idx = self.AXES_NAMES.index(axis_name)
                effects[idx] = value
        
        return effects.half() if self.config.use_float16 else effects.float()
    
    def save_state(self, path: str):
        """Save axis state to JSON"""
        import json
        state = {
            "axes": self.get_axes().cpu().tolist(),
            "axis_names": self.AXES_NAMES
        }
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, path: str):
        """Load axis state from JSON"""
        import json
        with open(path, 'r') as f:
            state = json.load(f)
        
        axes = torch.tensor(state["axes"])
        if self.config.use_float16:
            axes = axes.half()
        
        self.axes.data = axes.to(self.config.device)


# ==================== MODULE M: MODULATOR ====================

class Modulator:
    """
    Finite State Machine that selects actions based on axis values.
    """
    
    def __init__(self, config: FieldCoreConfig):
        self.config = config
    
    def select_action(self, 
                     axes: torch.Tensor, 
                     available_actions: List[str]) -> str:
        """
        Select action based on highest axis values.
        
        Rules:
        - High curiosity (recursive_depth) → ponder/reflect
        - Low stability (entropy_resilience < 0.3) → rest
        - High agency → explore
        - Default → observe
        """
        axes_list = axes.cpu().tolist()
        axis_dict = dict(zip(SwedenborgianGovernor.AXES_NAMES, axes_list))
        
        # Rule-based selection
        if axis_dict.get("entropy_resilience", 0.5) < 0.3:
            return "rest"
        
        if axis_dict.get("recursive_depth", 0.5) > 0.7:
            if "ponder" in available_actions:
                return "ponder"
            if "reflect" in available_actions:
                return "reflect"
        
        if axis_dict.get("agency_will", 0.5) > 0.6:
            if "explore" in available_actions:
                return "explore"
        
        if axis_dict.get("symbolic_grounding", 0.5) < 0.4:
            if "observe" in available_actions:
                return "observe"
        
        # Default: first available
        return available_actions[0] if available_actions else "observe"


# ==================== MODULE I: INTERFACE ====================

class ConsoleInterface:
    """Simple console I/O"""
    
    def __init__(self, config: FieldCoreConfig):
        self.config = config
    
    def display_situation(self, situation: Dict):
        """Display current situation to user"""
        print(f"\n{'='*50}")
        print(f"📍 Location: {situation['location']}")
        print(f"{'='*50}")
        print(f"Description: {situation['description']}")
        print(f"Available actions: {', '.join(situation['available_actions'])}")
    
    def display_state(self, axes: torch.Tensor):
        """Display current axis state"""
        print(f"\n--- Axis State ---")
        axes_list = axes.cpu().tolist()
        
        # Show top 5 active axes
        sorted_axes = sorted(
            enumerate(axes_list),
            key=lambda x: x[1],
            reverse=True
        )
        
        for idx, value in sorted_axes[:5]:
            name = SwedenborgianGovernor.AXES_NAMES[idx]
            bar = "█" * int(value * 10)
            print(f"  {name:25s}: {value:.2f} {bar}")
    
    def get_user_input(self) -> str:
        """Get user action input"""
        return input("\nAction (or 'quit'): ").strip().lower()
    
    def display_outcome(self, outcome: Dict):
        """Display action outcome"""
        print(f"\n→ {outcome['action']}: {outcome['outcome']}")


# ==================== MAIN: FIELD CORE AGENT ====================

class FieldCoreAgent:
    """
    Main agent combining all modules.
    """
    
    def __init__(self, config: Optional[FieldCoreConfig] = None):
        self.config = config or FieldCoreConfig()
        
        # Initialize modules
        self.environment = TextDojoEnvironment(self.config)
        self.governor = SwedenborgianGovernor(self.config)
        self.modulator = Modulator(self.config)
        self.interface = ConsoleInterface(self.config)
        
        print(f"FieldCore Agent initialized")
        print(f"  Device: {self.config.device}")
        print(f"  Float16: {self.config.use_float16}")
        print(f"  Axes: {self.config.num_axes}")
    
    def run(self, max_steps: int = 20):
        """Main agent loop"""
        print("\n🚀 Starting FieldCore Agent...\n")
        
        # Reset environment
        situation = self.environment.reset()
        self.interface.display_situation(situation)
        
        for step in range(max_steps):
            # Get current state
            axes = self.governor.get_axes()
            self.interface.display_state(axes)
            
            # Modulator selects action
            action = self.modulator.select_action(
                axes,
                situation["available_actions"]
            )
            
            # run action
            result = self.environment.step(action)
            self.interface.display_outcome(result)
            
            # Governor updates based on outcome
            new_axes = self.governor.update(
                situation["embedding"],
                action,
                result["outcome"]
            )
            
            # Next situation
            situation = result["situation"]
            self.interface.display_situation(situation)
            
            # Check for quit
            user_input = self.interface.get_user_input()
            if user_input == "quit":
                break
        
        # Save final state
        self.governor.save_state("soul_file.json")
        print("\n💾 State saved to soul_file.json")
    
    def save(self, path: str):
        """Save complete agent state"""
        self.governor.save_state(path)
    
    def load(self, path: str):
        """Load agent state"""
        self.governor.load_state(path)


# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    config = FieldCoreConfig(
        num_axes=5,  # Start with 5 for testing
        use_float16=True,
        device="cuda" if torch.cuda.is_available() else "cpu"
    )
    
    agent = FieldCoreAgent(config)
    agent.run(max_steps=10)
