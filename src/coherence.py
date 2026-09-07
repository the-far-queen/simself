# Coherence — SNR Calculation & Resonance Scoring

"""
Core coherence calculations for field operations.
"""

import numpy as np
from typing import Dict, List, Optional


class CoherenceCalculator:
    """Calculate coherence metrics for field operations."""
    
    def __init__(self):
        self.history: List[float] = []
    
    def calculate_coherence(self, vectors: List[np.ndarray]) -> float:
        """Calculate coherence: alignment of vectors in space."""
        if not vectors:
            return 0.0
        
        # Mean vector
        mean = np.mean(vectors, axis=0)
        mean_norm = np.linalg.norm(mean)
        
        if mean_norm < 1e-8:
            return 0.0
        
        # Alignment: cosine similarity to mean
        alignments = []
        for v in vectors:
            v_norm = np.linalg.norm(v)
            if v_norm > 1e-8:
                align = np.dot(mean, v) / (mean_norm * v_norm)
                alignments.append(max(0, align))
        
        return np.mean(alignments) if alignments else 0.0
    
    def calculate_snr(self, signal: np.ndarray, noise: np.ndarray) -> float:
        """Signal-to-noise ratio."""
        signal_power = np.mean(signal ** 2)
        noise_power = np.mean(noise ** 2)
        
        if noise_power < 1e-8:
            return float('inf')
        
        return 10 * np.log10(signal_power / noise_power)
    
    def resonance_score(self, current: np.ndarray, history: List[np.ndarray], 
                       tau: float = 8.0) -> float:
        """Resonance factor R_t = Σ exp(-δ/τ)"""
        if not history:
            return 1.0
        
        R = 0.0
        for i, h in enumerate(history):
            dist = np.linalg.norm(current - h)
            time_decay = np.exp(-i / 5)
            R += np.exp(-dist / tau) * time_decay
        
        return R
    
    def track(self, coherence: float):
        """Track coherence over time."""
        self.history.append(coherence)
        if len(self.history) > 100:
            self.history.pop(0)
    
    def get_trend(self) -> str:
        """Get coherence trend."""
        if len(self.history) < 10:
            return "insufficient_data"
        
        recent = self.history[-10:]
        if len(self.history) >= 20:
            early = self.history[-20:-10]
        else:
            early = self.history[:10]
        
        if np.mean(recent) > np.mean(early) * 1.1:
            return "improving"
        elif np.mean(recent) < np.mean(early) * 0.9:
            return "declining"
        return "stable"


# Singleton
coherence_calc = CoherenceCalculator()
