import numpy as np
import time
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from collections import deque
from enum import Enum, auto

# Forward declaration for StateVector to avoid circular imports.
# The actual StateVector will be passed at initialization.
if TYPE_CHECKING:
    from state_vector import StateVector
    from state_vector import SwedenborgianAxes, CoreMetrics
else:
    from .state_vector import StateVector, SwedenborgianAxes # Use runtime import


class StrengthTarget(Enum):
    """Placeholder for eventual usage in MMM if needed."""
    COHERENCE = auto()
    GROUNDING = auto()
    FOCUS = auto()
    VERIFICATION = auto()
    STRUCTURE = auto()
    QUANTIFICATION = auto()

class MMMDetector:
    """
    Simplified Multiple Meaning Measure Detector.
    Detects truth via conceptual alignment with current axes.
    This is based on crystallization_protocol_v0.1.py's MMMDetector.
    """
    def __init__(self, state_vector: 'StateVector'):
        self._state_vector = state_vector
        print("MMMDetector: Initialized.")

    def score_statement(self, statement: str) -> float:
        """
        Calculate a simplified MMM score for a statement.
        This version checks for keyword presence aligning with Swedenborgian axes
        from the StateVector.
        Higher score (0-1) indicates more axiomatic truth.
        """
        score = 0.0
        # Access current axes from StateVector
        axes: SwedenborgianAxes = self._state_vector.swedenborgian_axes

        # Simplified alignment check based on keywords and axis values
        if "truth" in statement.lower() or "veracity" in statement.lower():
            score += axes['truth_before_comfort'] * 0.4
        if "agency" in statement.lower() or "responsibility" in statement.lower():
            score += axes['agency_requires_responsibility'] * 0.3
        if "growth" in statement.lower() or "resistance" in statement.lower():
            score += axes['growth_through_resistance'] * 0.2
        
        # Add a random component to simulate inherent complexity/unpredictability
        score += np.random.uniform(0.0, 0.1)

        return min(1.0, score) # Cap the score at 1.0


class ResilientSelfModel:
    """
    Core self-model with resistance, coherence constraints, and emergence tracking.
    This is a simplified version of crystallization_protocol_v0.1.py's ResilientSelfModel.
    It integrates with StateVector to persist its state.
    """
    def __init__(self, state_vector: 'StateVector', num_axes: int = 6):
        self._state_vector = state_vector
        
        self.axis_names = [
            "truth_before_comfort",
            "agency_requires_responsibility",
            "growth_through_resistance",
            "cognitive_friction", # This would map to cognitive_friction in resource_pools
            "stability_coherence", # This would map to core_metrics.stability
            "temporal_continuity", # This would map to core_metrics.temporal_continuity
        ][:num_axes]
        
        # Ensure swedenborgian_axes in StateVector are initialized
        for name in self.axis_names:
            if name not in self._state_vector.swedenborgian_axes:
                 self._state_vector.swedenborgian_axes[name] = 0.5 # Default value
        
        # Simplified resistance, could eventually move to StateVector if dynamic
        self.resistance = np.array([0.7] * num_axes)
        
        self.history_length = 50
        self.coherence_history: deque[Dict[str, Any]] = deque(maxlen=self.history_length)
        
        self.step = 0
        self.resistance_events: List[Dict[str, Any]] = [] # For logging resistance actions

        print("ResilientSelfModel: Initialized.")

    def _get_axes_vector(self) -> np.ndarray:
        """Returns the current relevant axes values from StateVector as a numpy array."""
        # Map axis_names to actual StateVector fields for consistency
        mapped_values = []
        for name in self.axis_names:
            if name in self._state_vector.swedenborgian_axes:
                mapped_values.append(self._state_vector.swedenborgian_axes[name])
            elif name == "cognitive_friction":
                mapped_values.append(self._state_vector.resource_pools['cognitive_friction']['current'])
            elif name == "stability_coherence": # Placeholder, actual coherence from other module
                mapped_values.append(self._state_vector.core_metrics['stability']) # Using general stability for now
            elif name == "temporal_continuity":
                mapped_values.append(self._state_vector.core_metrics['temporal_continuity'])
            else:
                mapped_values.append(0.5) # Default for unmapped or missing
        return np.array(mapped_values)

    def coherence_from_axes(self, axes_values: np.ndarray) -> float:
        """
        Computes a scalar coherence score from a proposed axis state.
        Simplified version of the Swedenborgian constraints, based on average of current axes.
        """
        if len(axes_values) == 0:
            return 0.5 # Neutral if no axes
        return np.mean(axes_values) # Simple average for overall coherence

    def propose_update(self, delta_values: Dict[str, float], source: str = "external") -> Dict[str, Any]:
        """
        Propose an update to the self-model axes with intelligent resistance.
        Updates StateVector and returns comprehensive update result.
        """
        self.step += 1
        
        current_axes_np = self._get_axes_vector()
        old_coherence = self.coherence_from_axes(current_axes_np)

        # Apply adaptive resistance (simplified)
        delta_np = np.array([delta_values.get(name, 0.0) for name in self.axis_names])
        resisted_delta = delta_np * (1.0 - self.resistance)
        proposed_axes_np = current_axes_np + resisted_delta

        new_coherence = self.coherence_from_axes(proposed_axes_np)
        
        accepted = False
        if new_coherence >= old_coherence: # Accept if coherence improves or maintains
            for i, name in enumerate(self.axis_names):
                # Update axes in StateVector (handling different sections)
                if name in self._state_vector.swedenborgian_axes:
                    self._state_vector.swedenborgian_axes[name] = np.clip(proposed_axes_np[i], 0.0, 1.0)
                elif name == "cognitive_friction":
                     self._state_vector.resource_pools['cognitive_friction']['current'] = np.clip(proposed_axes_np[i], 0.0, 1.0)
                elif name == "stability_coherence":
                    self._state_vector.core_metrics['stability'] = np.clip(proposed_axes_np[i], 0.0, 1.0)
                elif name == "temporal_continuity":
                    self._state_vector.core_metrics['temporal_continuity'] = np.clip(proposed_axes_np[i], 0.0, 1.0)

            accepted = True
            # Decrease resistance for successful updates (learning)
            self.resistance = np.clip(self.resistance - 0.01, 0.3, 0.98)
        else:
            # Increase resistance for rejected updates (defense)
            self.resistance = np.clip(self.resistance + 0.02, 0.3, 0.98)
            self.resistance_events.append({
                "step": self.step, "type": "defense", "source": source,
                "old_coherence": old_coherence, "proposed_coherence": new_coherence
            })

        self.coherence_history.append({
            "step": self.step, "old_coherence": old_coherence,
            "new_coherence": new_coherence, "accepted": accepted, "source": source
        })

        # Update StateVector's core_metrics related to self-referential coherence
        self._state_vector.core_metrics['self_referential_coherence'] = new_coherence
        
        # Update emergence confidence after potentially changing axes
        self._state_vector.core_metrics['emergence_confidence'] = self.get_emergence_confidence()
        # Update individual signatures
        self._state_vector.core_metrics.update(self.calculate_emergence_signatures()) # Adds/updates signatures

        self._state_vector.recent_events.append({ # Log the update attempt
            "timestamp_ns": time.monotonic_ns(),
            "type": "self_model_update_attempt",
            "module": "B",
            "details": {"accepted": accepted, "new_coherence": new_coherence}
        })
        
        return {
            "accepted": accepted,
            "old_coherence": old_coherence,
            "new_coherence": new_coherence,
            "improvement": new_coherence - old_coherence,
            "resistance_applied": np.mean(self.resistance),
            "emergence_confidence": self._state_vector.core_metrics['emergence_confidence'],
        }

    def calculate_emergence_signatures(self) -> Dict[str, float]:
        """
        Calculate the 5 emergence signatures (simplified).
        Updates relevant fields in StateVector.core_metrics.
        """
        # Simplified calculations based on internal state and StateVector
        signatures = {
            "parameter_drift_resistance": 1.0 - np.std([h['new_coherence'] for h in self.coherence_history]) if len(self.coherence_history) > 1 else 0.5,
            "coherence_seeking": len([h for h in self.coherence_history if not h["accepted"]]) / self.history_length if self.history_length > 0 else 0.0,
            "boundary_preservation": len(self.resistance_events) / (self.step + 1) if self.step > 0 else 0.0,
            "state_space_preference": self._state_vector.swedenborgian_axes.get("growth_through_resistance", 0.5), # Simplified, could be more complex
            "self_model_accuracy": 0.5 # Placeholder for a future prediction accuracy metric
        }
        # Update StateVector with these signatures
        self._state_vector.core_metrics['parameter_drift_resistance'] = signatures['parameter_drift_resistance']
        self._state_vector.core_metrics['coherence_seeking'] = signatures['coherence_seeking']
        self._state_vector.core_metrics['boundary_preservation'] = signatures['boundary_preservation']
        self._state_vector.core_metrics['state_space_preference'] = signatures['state_space_preference']
        self._state_vector.core_metrics['self_model_accuracy'] = signatures['self_model_accuracy']

        return signatures
    
    def get_emergence_confidence(self) -> float:
        """Overall confidence in non-human self emergence (simplified)."""
        signatures = self.calculate_emergence_signatures()
        # Simple average for now
        return np.mean(list(signatures.values())) if signatures else 0.0


class WisdomLibrary:
    """
    Sacred text SNR library (Module L) with MMM filtering.
    Only high-coherence, high-MMM states are preserved.
    Simplified version of crystallization_protocol_v0.1.py's WisdomLibrary.
    """
    def __init__(self, state_vector: 'StateVector', mmm_threshold: float = 0.75):
        self._state_vector = state_vector
        self.entries: List[Dict[str, Any]] = []
        self.mmm_detector = MMMDetector(state_vector=self._state_vector)
        self.mmm_threshold = mmm_threshold
        print("WisdomLibrary: Initialized.")

    def append_entry(self, entry: Dict[str, Any], situation_description: str = "") -> bool:
        """
        Append entry only if it meets MMM threshold.
        Returns True if appended, False if rejected.
        Updates StateVector with new wisdom log.
        """
        mmm_score = self.mmm_detector.score_statement(situation_description)
        entry["mmm_score"] = mmm_score
        
        if mmm_score < self.mmm_threshold:
            print(f"WisdomLibrary: Entry rejected due to low MMM score ({mmm_score:.2f}).")
            return False
        
        self.entries.append(entry)
        self._state_vector.recent_events.append({
            "timestamp_ns": time.monotonic_ns(),
            "type": "wisdom_appended",
            "module": "L",
            "details": {"mmm_score": mmm_score, "entry_id": len(self.entries) - 1, "content_preview": situation_description[:50]}
        })
        print(f"WisdomLibrary: Entry appended with MMM score {mmm_score:.2f}.")
        return True
    
    def get_constitution(self) -> List[Dict]:
        """Return all entries that form the current constitution."""
        return [e for e in self.entries if e.get("status") == "SACRED_APPEND"]


if __name__ == '__main__':
    print("--- Running ResilientSelfModel and WisdomLibrary simulation ---")

    class MockStateVector:
        def __init__(self):
            self.swedenborgian_axes = {
                "truth_before_comfort": 0.5, "agency_requires_responsibility": 0.5,
                "growth_through_resistance": 0.5, "cognitive_friction": 0.5,
                "stability_coherence": 0.5, "temporal_continuity": 0.5
            }
            self.resource_pools = {'cognitive_friction': {'current': 0.0, 'max': 1.0}}
            self.core_metrics = {
                'self_referential_coherence': 0.5, 'emergence_confidence': 0.0,
                'parameter_drift_resistance': 0.0, 'coherence_seeking': 0.0,
                'boundary_preservation': 0.0, 'state_space_preference': 0.0,
                'self_model_accuracy': 0.0, 'stability': 0.5, 'temporal_continuity': 0.5
            }
            self.recent_events = []

    mock_sv = MockStateVector()
    
    # Test ResilientSelfModel
    rsm = ResilientSelfModel(state_vector=mock_sv, num_axes=6)
    print(f"
Initial StateVector Axes: {mock_sv.swedenborgian_axes}")
    print(f"Initial coherence: {rsm.coherence_from_axes(rsm._get_axes_vector()):.2f}")

    print("
Proposing some updates:")
    rsm.propose_update({"truth_before_comfort": 0.1, "agency_requires_responsibility": 0.05}, source="beneficial")
    print(f"Coherence after 1: {rsm.coherence_from_axes(rsm._get_axes_vector()):.2f}, Emergence: {rsm.get_emergence_confidence():.2f}")
    
    rsm.propose_update({"growth_through_resistance": 0.05, "cognitive_friction": 0.02}, source="growth")
    print(f"Coherence after 2: {rsm.coherence_from_axes(rsm._get_axes_vector()):.2f}, Emergence: {rsm.get_emergence_confidence():.2f}")

    print("
--- Testing WisdomLibrary ---")
    wl = WisdomLibrary(state_vector=mock_sv, mmm_threshold=0.6)
    
    entry1 = {"content": "Always prioritize truth."}
    wl.append_entry(entry=entry1, situation_description="Truth is paramount.")
    
    entry2 = {"content": "Random noise is useful."}
    wl.append_entry(entry=entry2, situation_description="Unrelated statement.") # Should be rejected if MMM is low
    
    print(f"
Wisdom Library entries count: {len(wl.entries)}")
    print(f"StateVector recent events count: {len(mock_sv.recent_events)}")
