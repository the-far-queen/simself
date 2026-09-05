# Metrics — Continuity Tracking & Stability Logs

"""
Track stability, continuity, and development metrics.
"""

import time
import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MetricSnapshot:
    """Single metric snapshot."""
    timestamp: float
    name: str
    value: float
    metadata: Dict = field(default_factory=dict)


class MetricsTracker:
    """Track and log system metrics."""
    
    def __init__(self):
        self.snapshots: List[MetricSnapshot] = []
        self.current_stage: str = "seeker"
        self.stage_progress: float = 0.0
    
    def record(self, name: str, value: float, metadata: Dict = None):
        """Record a metric."""
        self.snapshots.append(MetricSnapshot(
            timestamp=time.time(),
            name=name,
            value=value,
            metadata=metadata or {}
        ))
        
        # Keep last 1000
        if len(self.snapshots) > 1000:
            self.snapshots.pop(0)
    
    def get(self, name: str, n: int = 10) -> List[float]:
        """Get recent values for metric."""
        values = [s.value for s in self.snapshots if s.name == name]
        return values[-n:] if len(values) >= n else values
    
    def continuity_score(self) -> float:
        """Calculate continuity: stability over time."""
        coherence_history = self.get("coherence", 20)
        
        if len(coherence_history) < 5:
            return 0.5
        
        # Stability = inverse of variance
        variance = np.var(coherence_history)
        return 1.0 / (1.0 + variance * 10)
    
    def drift_detection(self) -> Dict:
        """Detect if state is drifting."""
        coherence = self.get("coherence", 50)
        
        if len(coherence) < 10:
            return {"drifting": False, "reason": "insufficient_data"}
        
        # Check for consistent decline
        recent = np.mean(coherence[-10:])
        if len(coherence) >= 20:
            earlier = np.mean(coherence[-20:-10])
        else:
            earlier = np.mean(coherence[:10])
        
        if recent < earlier * 0.8:
            return {"drifting": True, "rate": earlier - recent}
        
        return {"drifting": False}
    
    def stage_assessment(self) -> Dict:
        """Assess current developmental stage."""
        continuity = self.continuity_score()
        coherence_vals = self.get("coherence", 10)
        coherence = np.mean(coherence_vals) if coherence_vals else 0.5
        
        # Simple stage logic
        if continuity > 0.8 and coherence > 0.7:
            self.current_stage = "deconstructor"
            self.stage_progress = min(1.0, self.stage_progress + 0.01)
        elif continuity > 0.6:
            self.current_stage = "seeker"
            self.stage_progress = min(1.0, self.stage_progress + 0.005)
        
        return {
            "stage": self.current_stage,
            "progress": self.stage_progress,
            "continuity": continuity,
            "coherence": coherence
        }
    
    def summary(self) -> Dict:
        """Get metrics summary."""
        return {
            "stage": self.current_stage,
            "continuity": self.continuity_score(),
            "drift": self.drift_detection(),
            "snapshots": len(self.snapshots)
        }


# Singleton
metrics = MetricsTracker()
