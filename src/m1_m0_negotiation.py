"""
M1-M0 Negotiation with PLL - FieldCore v1

M1: Elastic Intent Layer (adaptive, proposes actions)
M0: Plastic Reality Layer (fixed geometry, enforces invariants)

Based on docs/fieldcore/docs/meta_sheaf_resonance.md
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import time


class ResonanceState(Enum):
    """States of M1-M0 resonance"""
    LOCKED = "locked"        # High resonance, working
    SEARCHING = "searching"  # Adjusting to find resonance
    LOST = "lost"           # Resonance broken
    RECOVERING = "recovering"  # Actively recovering


@dataclass
class PhaseError:
    """Difference between M1 proposal and M0 reality"""
    magnitude: float
    direction: np.ndarray
    component_errors: Dict[str, float]


@dataclass
class NegotiationResult:
    """Result of M1-M0 negotiation"""
    reached_consensus: bool
    final_state: Optional[np.ndarray]
    phase_error: Optional[PhaseError]
    n_iterations: int
    resonance_score: float


# === M0: PLASTIC REALITY LAYER ===

class M0Reality:
    """
    M0: Plastic Reality Layer
    
    - Fixed geometry (invariants never change)
    - Enforces boundary conditions
    - Rejects invalid proposals
    - Provides anchors
    """
    
    def __init__(self):
        # Invariant boundaries (FIXED)
        self.boundaries = {
            "norm_max": 10.0,
            "energy_max": 15.0,
            "coherence_min": 0.3,
            "temporal_continuity_min": 0.5
        }
        
        # Current state
        self.state: np.ndarray = np.zeros(64)
        self.state_history: List[np.ndarray] = []
    
    def enforce(self, proposed_state: np.ndarray) -> Tuple[bool, Dict]:
        """
        Enforce invariants on proposed state.
        
        Returns: (passed, violation_details)
        """
        violations = {}
        
        # Check norm
        norm = np.linalg.norm(proposed_state)
        if norm > self.boundaries["norm_max"]:
            violations["norm_exceeded"] = {
                "actual": norm,
                "max": self.boundaries["norm_max"]
            }
        
        # Check energy
        energy = np.sum(proposed_state ** 2)
        if energy > self.boundaries["energy_max"]:
            violations["energy_exceeded"] = {
                "actual": energy,
                "max": self.boundaries["energy_max"]
            }
        
        # Check coherence
        if len(proposed_state) > 1:
            coherence = 1.0 - np.var(proposed_state)
            if coherence < self.boundaries["coherence_min"]:
                violations["coherence_below_min"] = {
                    "actual": coherence,
                    "min": self.boundaries["coherence_min"]
                }
        
        passed = len(violations) == 0
        
        return passed, violations
    
    def get_anchor(self) -> np.ndarray:
        """Get current anchor state"""
        return self.state.copy()
    
    def update_state(self, new_state: np.ndarray):
        """Update reality state"""
        self.state_history.append(self.state.copy())
        self.state = new_state.copy()
        
        # Limit history
        if len(self.state_history) > 100:
            self.state_history = self.state_history[-50:]


# === M1: ELASTIC INTENT LAYER ===

class M1Intent:
    """
    M1: Elastic Intent Layer
    
    - Dynamic tuner (like PLL)
    - Adapts to noise
    - Proposes actions
    - Absorbs perturbations
    """
    
    def __init__(self, elasticity: float = 0.5):
        self.elasticity = elasticity  # How much to adapt
        
        # PLL-like parameters
        self.lock_threshold = 0.8
        self.search_gain = 0.3
        self.damping = 0.9
        
        # State
        self.proposal: Optional[np.ndarray] = None
        self.adaptation_history: List[float] = []
    
    def propose(self, intent: np.ndarray, feedback: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Propose state based on intent + feedback adaptation.
        
        PLL analogy:
        - intent = desired phase
        - feedback = phase error signal
        - elasticity = loop gain
        """
        self.proposal = intent.copy()
        
        # Adapt based on feedback
        if feedback is not None:
            # PLL correction: new = old + gain * error
            correction = self.search_gain * feedback
            self.proposal = intent + correction * self.elasticity
            
            # Track adaptation
            error_magnitude = np.linalg.norm(correction)
            self.adaptation_history.append(error_magnitude)
        
        return self.proposal
    
    def adapt_to_feedback(self, phase_error: PhaseError) -> np.ndarray:
        """
        Adapt proposal based on phase error from M0.
        
        This is the key: M1 absorbs perturbations to protect M0.
        """
        if self.proposal is None:
            return phase_error.direction * 0
        
        # Reduce magnitude in error direction
        correction = -phase_error.direction * phase_error.magnitude * self.elasticity
        
        # Apply with damping
        damped_correction = correction * self.damping
        
        adapted = self.proposal + damped_correction
        
        self.adaptation_history.append(phase_error.magnitude)
        
        return adapted
    
    def get_resonance_score(self, m0_state: np.ndarray) -> float:
        """Calculate resonance: 1 - phase_error"""
        if self.proposal is None:
            return 0.0
        
        # Phase error = distance between proposal and M0 state
        if np.linalg.norm(m0_state) < 1e-8:
            return 0.0
        
        # Cosine similarity as resonance
        norm_p = np.linalg.norm(self.proposal)
        norm_r = np.linalg.norm(m0_state)
        
        if norm_p < 1e-8 or norm_r < 1e-8:
            return 0.0
        
        similarity = np.dot(self.proposal, m0_state) / (norm_p * norm_r)
        
        # Resonance = 1 - error (error is 1-similarity)
        resonance = max(0, similarity)
        
        return float(resonance)


# === M1-M0 NEGOTIATION ===

class MetaSheafNegotiation:
    """
    Meta-Sheaf: Oversees sheaf as resonant manifold.
    
    M1-M0 Negotiation:
    1. M1 proposes glue
    2. M0 checks invariants
    3. Feedback refines proposal
    4. Repeat until resonance >= threshold
    """
    
    def __init__(self):
        # Layers
        self.m1 = M1Intent(elasticity=0.5)
        self.m0 = M0Reality()
        
        # Negotiation parameters
        self.lock_threshold = 0.8
        self.max_iterations = 20
        self.convergence_rate = 0.1
        
        # State
        self.state = ResonanceState.SEARCHING
        self.negotiation_history: List[NegotiationResult] = []
    
    def negotiate(self, intent: np.ndarray) -> NegotiationResult:
        """
        Run M1-M0 negotiation until resonance or max iterations.
        """
        iteration = 0
        current_proposal = intent.copy()
        
        for iteration in range(self.max_iterations):
            # Step 1: M1 proposes
            self.m1.propose(current_proposal)
            
            # Step 2: M0 enforces invariants
            passed, violations = self.m0.enforce(self.m1.proposal)
            
            # Step 3: Calculate phase error
            phase_error = self._calculate_phase_error(
                self.m1.proposal, 
                self.m0.state,
                violations
            )
            
            # Step 4: Check resonance
            resonance = self.m1.get_resonance_score(self.m0.state)
            
            if passed and resonance >= self.lock_threshold:
                # LOCKED - consensus reached
                self.state = ResonanceState.LOCKED
                
                # Update M0 with new reality
                self.m0.update_state(self.m1.proposal)
                
                result = NegotiationResult(
                    reached_consensus=True,
                    final_state=self.m1.proposal.copy(),
                    phase_error=phase_error,
                    n_iterations=iteration + 1,
                    resonance_score=resonance
                )
                
                self.negotiation_history.append(result)
                return result
            
            # Step 5: M1 adapts to feedback (absorbs perturbation)
            current_proposal = self.m1.adapt_to_feedback(phase_error)
        
        # Failed to reach consensus
        self.state = ResonanceState.LOST
        
        result = NegotiationResult(
            reached_consensus=False,
            final_state=None,
            phase_error=phase_error,
            n_iterations=iteration + 1,
            resonance_score=resonance
        )
        
        self.negotiation_history.append(result)
        
        return result
    
    def _calculate_phase_error(
        self, 
        proposal: np.ndarray, 
        reality: np.ndarray,
        violations: Dict
    ) -> PhaseError:
        """Calculate phase error between M1 proposal and M0 reality"""
        
        # Direction of error
        if np.linalg.norm(reality) < 1e-8:
            direction = np.zeros_like(proposal)
        else:
            direction = (proposal - reality) / (np.linalg.norm(proposal - reality) + 1e-8)
        
        # Magnitude
        magnitude = np.linalg.norm(proposal - reality)
        
        # Component errors
        component_errors = {}
        for key, val in violations.items():
            component_errors[key] = val.get("actual", 0) / (val.get("max", 1) + 1e-8)
        
        return PhaseError(
            magnitude=magnitude,
            direction=direction,
            component_errors=component_errors
        )
    
    def recover(self, intent: np.ndarray) -> NegotiationResult:
        """
        Attempt to recover from lost resonance.
        """
        self.state = ResonanceState.RECOVERING
        
        # Reset M1 adaptation
        self.m1.adaptation_history.clear()
        
        # Retry negotiation with lower threshold
        old_threshold = self.lock_threshold
        self.lock_threshold = 0.5
        
        result = self.negotiate(intent)
        
        # Restore threshold
        self.lock_threshold = old_threshold
        
        if result.reached_consensus:
            self.state = ResonanceState.LOCKED
        else:
            self.state = ResonanceState.LOST
        
        return result
    
    def get_status(self) -> Dict:
        """Get current negotiation status"""
        return {
            "state": self.state.value,
            "lock_threshold": self.lock_threshold,
            "negotiations_total": len(self.negotiation_history),
            "consensus_rate": sum(1 for r in self.negotiation_history if r.reached_consensus) / max(len(self.negotiation_history), 1)
        }


# === USAGE EXAMPLE ===

if __name__ == '__main__':
    print("=== M1-M0 Negotiation with PLL Demo ===\n")
    
    # Create negotiation system
    negotiation = MetaSheafNegotiation()
    
    # Test 1: Valid intent
    print("--- Test 1: Valid Intent ---")
    valid_intent = np.array([0.5, 0.3, 0.2, 0.1] * 16)  # Within bounds
    
    result = negotiation.negotiate(valid_intent)
    
    print(f"Consensus: {result.reached_consensus}")
    print(f"Iterations: {result.n_iterations}")
    print(f"Resonance: {result.resonance_score:.3f}")
    print(f"State: {negotiation.state.value}")
    
    # Test 2: Invalid intent (violates boundaries)
    print("\n--- Test 2: Invalid Intent ---")
    invalid_intent = np.array([5.0, 5.0, 5.0, 5.0] * 16)  # Exceeds norm
    
    result2 = negotiation.negotiate(invalid_intent)
    
    print(f"Consensus: {result2.reached_consensus}")
    print(f"Iterations: {result2.n_iterations}")
    print(f"Resonance: {result2.resonance_score:.3f}")
    
    # Test 3: Recovery
    print("\n--- Test 3: Recovery ---")
    recovery_result = negotiation.recover(invalid_intent)
    
    print(f"Recovered: {recovery_result.reached_consensus}")
    print(f"State: {negotiation.state.value}")
    
    # Status
    print("\n--- Status ---")
    status = negotiation.get_status()
    for k, v in status.items():
        print(f"  {k}: {v}")
    
    # Test M0 invariants
    print("\n--- M0 Invariants ---")
    m0 = M0Reality()
    
    test_states = [
        np.array([0.5, 0.3, 0.2]),
        np.array([10.0, 10.0, 10.0]),  # Too large
    ]
    
    for state in test_states:
        passed, violations = m0.enforce(state)
        print(f"State {state[:3]}: {'✓' if passed else '✗'} {violations}")
