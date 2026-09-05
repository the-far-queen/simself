"""SimSelf: The self-model with curiosity axes.

Module B - manages:
- Embedding (current state representation)
- Curiosity axes (what to explore)
- Coherence tracking
"""

import numpy as np
from typing import Dict, Any, Optional


class SimSelf:
    """Self-model with curiosity-driven exploration.
    
    Manages:
    - embedding: current state vector
    - curiosity_axes: what to explore next
    - coherence: how stable is the self-model
    """
    
    def __init__(self, dim: int = 16, initial_coherence: float = 0.5):
        self.dim = dim
        
        # Current state embedding
        self.embedding = np.random.randn(dim)
        self.embedding /= np.linalg.norm(self.embedding) + 1e-8
        
        # Previous embedding (for novelty calculation)
        self.previous_embedding = self.embedding.copy()
        
        # Coherence score (0-1)
        self.coherence = initial_coherence
        
        # Curiosity axes (directions to explore)
        self.curiosity_axes = self._init_curiosity_axes()
        
        # Experience buffer
        self.experiences = []
        self.max_experiences = 100
        
    def _init_curiosity_axes(self) -> Dict[str, np.ndarray]:
        """Initialize curiosity exploration directions."""
        # Core axes: sensor modalities
        return {
            "touch": np.random.randn(self.dim),
            "temperature": np.random.randn(self.dim),
            "wetness": np.random.randn(self.dim),
            "label": np.random.randn(self.dim)
        }
    
    def update(self, sensor_data: Dict[str, float], field_embedding: Optional[np.ndarray] = None):
        """Update self-model from sensor data."""
        # Update previous
        self.previous_embedding = self.embedding.copy()
        
        # Mix sensor data into embedding
        if field_embedding is not None:
            # Blend with field state
            alpha = 0.7
            self.embedding = alpha * field_embedding + (1 - alpha) * self.embedding
        else:
            # Direct sensor update
            sensor_vector = self._sensors_to_vector(sensor_data)
            self.embedding = 0.8 * self.embedding + 0.2 * sensor_vector
            
        # Normalize
        self.embedding /= np.linalg.norm(self.embedding) + 1e-8
        
        # Update coherence
        self._update_coherence()
        
        # Update curiosity
        self._update_curiosity(sensor_data)
        
        # Record experience
        self._record_experience(sensor_data)
    
    def _sensors_to_vector(self, sensors: Dict[str, float]) -> np.ndarray:
        """Convert sensor dict to embedding vector."""
        vector = np.zeros(self.dim)
        
        # Map each sensor to its curiosity axis
        for sensor, value in sensors.items():
            if sensor in self.curiosity_axes:
                vector += self.curiosity_axes[sensor] * value
        
        # Add some noise for exploration
        vector += np.random.randn(self.dim) * 0.1
        
        return vector
    
    def _update_coherence(self):
        """Update coherence score based on embedding stability."""
        # Coherence = inverse of change magnitude
        change = np.linalg.norm(self.embedding - self.previous_embedding)
        self.coherence = 1.0 / (1.0 + change * 10)
    
    def _update_curiosity(self, sensors: Dict[str, float]):
        """Update curiosity axes based on sensor data."""
        # Strengthen axes with strong signals
        for sensor, value in sensors.items():
            if abs(value) > 0.5 and sensor in self.curiosity_axes:
                # Reinforce this axis
                self.curiosity_axes[sensor] *= 1.1
                
        # Normalize all axes
        for axis in self.curiosity_axes:
            self.curiosity_axes[axis] /= np.linalg.norm(self.curiosity_axes[axis]) + 1e-8
    
    def _record_experience(self, sensors: Dict[str, float]):
        """Record experience for learning."""
        self.experiences.append({
            "embedding": self.embedding.copy(),
            "sensors": sensors.copy(),
            "coherence": self.coherence
        })
        
        if len(self.experiences) > self.max_experiences:
            self.experiences.pop(0)
    
    def get_novelty(self) -> float:
        """Calculate novelty (change from previous state)."""
        return float(np.linalg.norm(self.embedding - self.previous_embedding))
    
    def get_curiosity_vector(self) -> np.ndarray:
        """Get combined curiosity direction."""
        combined = np.zeros(self.dim)
        for axis in self.curiosity_axes.values():
            combined += axis
        combined /= len(self.curiosity_axes)
        return combined
    
    def inject_label(self, label: str):
        """Inject breakthrough label into self-model."""
        # Create strong association with label
        if label in self.curiosity_axes:
            self.curiosity_axes[label] *= 2.0  # Strengthen
            self.curiosity_axes[label] /= np.linalg.norm(self.curiosity_axes[label]) + 1e-8
        
        # Add as new axis if not exists
        if label not in self.curiosity_axes:
            self.curiosity_axes[label] = np.random.randn(self.dim)
            self.curiosity_axes[label] /= np.linalg.norm(self.curiosity_axes[label]) + 1e-8
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state for debugging."""
        return {
            "coherence": self.coherence,
            "novelty": self.get_novelty(),
            "embedding_norm": float(np.linalg.norm(self.embedding)),
            "curiosity_axes": list(self.curiosity_axes.keys()),
            "experience_count": len(self.experiences)
        }
    
    def __repr__(self):
        return f"SimSelf(coherence={self.coherence:.2f}, dim={self.dim})"
