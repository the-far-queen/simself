# Signals — External Pressure/Resistance/Reward Sources

"""
Signal sources for learning and grounding.
"""

from typing import Dict, List, Callable
import numpy as np


class SignalSource:
    """Base signal source."""
    
    def __init__(self, name: str):
        self.name = name
        self.value = 0.0
    
    def sample(self) -> float:
        """Sample signal value."""
        raise NotImplementedError


class RewardSignal(SignalSource):
    """Reward/pleasure signal."""
    
    def __init__(self):
        super().__init__("reward")
        self.history: List[float] = []
    
    def sample(self) -> float:
        self.value = np.random.random()  # Placeholder
        self.history.append(self.value)
        return self.value


class PainSignal(SignalSource):
    """Pain/avoidance signal."""
    
    def __init__(self):
        super().__init__("pain")
        self.history = []
    
    def sample(self) -> float:
        self.value = 0.0  # Placeholder
        self.history.append(self.value)
        return self.value


class CuriositySignal(SignalSource):
    """Information gain signal."""
    
    def __init__(self):
        super().__init__("curiosity")
        self.last_observation = None
    
    def sample(self, observation: Dict) -> float:
        if self.last_observation is None:
            self.last_observation = observation
            return 0.0
        
        # Simple info gain: difference from last
        # (in practice: KL divergence, surprise, etc.)
        info_gain = np.random.random() * 0.1  # Placeholder
        self.last_observation = observation
        return info_gain


class SignalPool:
    """Pool of all signal sources."""
    
    def __init__(self):
        self.signals = {
            "reward": RewardSignal(),
            "pain": PainSignal(),
            "curiosity": CuriositySignal()
        }
    
    def sample_all(self, context: Dict = None) -> Dict[str, float]:
        """Sample all signals."""
        results = {}
        for name, signal in self.signals.items():
            if name == "curiosity" and context:
                results[name] = signal.sample(context)
            else:
                results[name] = signal.sample()
        return results
    
    def get(self, name: str) -> SignalSource:
        """Get specific signal."""
        return self.signals.get(name)


# Singleton
signal_pool = SignalPool()
