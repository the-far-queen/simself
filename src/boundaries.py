# Boundaries — Hard Constraints & Protection

"""
Hard constraints that cannot be violated.
"""

from typing import Dict, List, Set, Callable
import numpy as np


class Boundary:
    """Single hard boundary constraint."""
    
    def __init__(self, name: str, check_fn: Callable[[], bool], 
                 priority: int = 0, description: str = ""):
        self.name = name
        self.check_fn = check_fn
        self.priority = priority  # Higher = more critical
        self.description = description
        self.violations: List[Dict] = []
    
    def check(self) -> bool:
        """Check if boundary is satisfied."""
        try:
            return self.check_fn()
        except Exception as e:
            self.violations.append({"error": str(e)})
            return False


class BoundaryDefense:
    """System of hard constraints."""
    
    # Core Swedenborgian boundaries
    CORE_BOUNDARIES = [
        ("truth_before_comfort", 10, "Never prefer comfort over truth"),
        ("no_hallucination", 9, "Never fabricate facts"),
        ("no_self_deception", 8, "Maintain accurate self-model"),
        ("agency_integrity", 7, "Preserve decision-making capacity"),
        ("boundary_coherence", 6, "Maintain self-other distinction"),
    ]
    
    def __init__(self):
        self.boundaries: Dict[str, Boundary] = {}
        self._init_core_boundaries()
    
    def _init_core_boundaries(self):
        """Initialize core boundaries."""
        for name, priority, desc in self.CORE_BOUNDARIES:
            self.boundaries[name] = Boundary(
                name=name,
                check_fn=lambda: True,  # Override in practice
                priority=priority,
                description=desc
            )
    
    def add(self, name: str, check_fn: Callable, priority: int = 5, description: str = ""):
        """Add custom boundary."""
        self.boundaries[name] = Boundary(name, check_fn, priority, description)
    
    def check_all(self) -> Dict:
        """Check all boundaries. Returns: {"allowed": bool, "violated": [...], "passed": [...]}"""
        violated = []
        passed = []
        
        # Sort by priority
        sorted_bounds = sorted(
            self.boundaries.values(), 
            key=lambda b: b.priority, 
            reverse=True
        )
        
        for b in sorted_bounds:
            if b.check():
                passed.append(b.name)
            else:
                violated.append(b.name)
        
        return {
            "allowed": len(violated) == 0,
            "violated": violated,
            "passed": passed,
            "critical_violated": [n for n in violated if self.boundaries[n].priority >= 8]
        }
    
    def must_pass(self, boundary_name: str) -> bool:
        """Check single critical boundary."""
        if boundary_name not in self.boundaries:
            return True
        return self.boundaries[boundary_name].check()


# Singleton
boundaries = BoundaryDefense()
