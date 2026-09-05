# Planner — Task Decomposition

"""
Break goals into subgoals.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Goal:
    """Goal representation."""
    description: str
    subgoals: List['Goal']
    completed: bool = False
    
    def is_leaf(self) -> bool:
        return len(self.subgoals) == 0


class Planner:
    """Simple goal planner."""
    
    def __init__(self):
        self.current_goal: Optional[Goal] = None
        self.goal_stack: List[Goal] = []
    
    def set_goal(self, description: str):
        """Set new top-level goal."""
        self.current_goal = Goal(description, [])
        self.goal_stack = [self.current_goal]
    
    def decompose(self, goal: Goal, decomposition_fn: callable) -> Goal:
        """Decompose goal into subgoals."""
        subgoals = decomposition_fn(goal.description)
        goal.subgoals = [Goal(sg, []) for sg in subgoals]
        return goal
    
    def next_action(self) -> Optional[str]:
        """Get next action from current goal."""
        if not self.goal_stack:
            return None
        
        # Find next incomplete leaf
        def find_next(g: Goal) -> Optional[str]:
            if g.is_leaf() and not g.completed:
                return g.description
            for sg in g.subgoals:
                result = find_next(sg)
                if result:
                    return result
            return None
        
        return find_next(self.goal_stack[-1])
    
    def complete_action(self, action: str):
        """Mark action as complete."""
        if not self.goal_stack:
            return
        
        # Find and mark complete
        def mark_complete(g: Goal) -> bool:
            if g.is_leaf() and g.description == action:
                g.completed = True
                return True
            for sg in g.subgoals:
                if mark_complete(sg):
                    return True
            return False
        
        mark_complete(self.goal_stack[-1])


# Example: Decompose "get water"
def decompose_get_water(goal: str) -> List[str]:
    """Decompose get water goal."""
    return [
        "find water source",
        "approach water",
        "grasp container",
        "bring to target"
    ]
