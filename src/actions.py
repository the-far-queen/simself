# Actions — Discrete Action Space

"""
Available actions for the embodied agent.
"""

from enum import Enum
from typing import Dict, Tuple


class ActionType(Enum):
    """Available action types."""
    MOVE = "move"
    GRASP = "grasp"
    RELEASE = "release"
    PUSH = "push"
    LOOK = "look"
    WAIT = "wait"
    REFUSE = "refuse"
    COMMUNICATE = "communicate"


class Action:
    """Action representation."""
    
    def __init__(self, action_type: ActionType, params: Dict = None):
        self.type = action_type
        self.params = params or {}
    
    def to_dict(self) -> Dict:
        return {"type": self.type.value, "params": self.params}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Action':
        return cls(ActionType(data["type"]), data.get("params", {}))


# Action creators
def move(direction: Tuple[float, float, float]) -> Action:
    """Move in direction."""
    return Action(ActionType.MOVE, {"direction": direction})


def grasp(target: str) -> Action:
    """Grasp object."""
    return Action(ActionType.GRASP, {"target": target})


def release() -> Action:
    """Release held object."""
    return Action(ActionType.RELEASE)


def push(target: str, force: float) -> Action:
    """Push object."""
    return Action(ActionType.PUSH, {"target": target, "force": force})


def look(direction: Tuple[float, float, float]) -> Action:
    """Look in direction."""
    return Action(ActionType.LOOK, {"direction": direction})


def wait() -> Action:
    """Wait/do nothing."""
    return Action(ActionType.WAIT)


def refuse(reason: str) -> Action:
    """Refuse action (agency boundary)."""
    return Action(ActionType.REFUSE, {"reason": reason})


def communicate(message: str) -> Action:
    """Communicate with human."""
    return Action(ActionType.COMMUNICATE, {"message": message})


# All actions as list (for policy)
ALL_ACTIONS = [
    move((1, 0, 0)), move((-1, 0, 0)), move((0, 1, 0)), move((0, -1, 0)),
    grasp("any"), release(), push("any", 1.0), look((1, 0, 0)),
    wait(), refuse("boundary"), communicate("hello")
]
