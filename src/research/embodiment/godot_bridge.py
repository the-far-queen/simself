"""
Godot Bridge — Python ↔ Godot Communication

Protocol: JSON over WebSocket or stdin/stdout
Godot = body + environment, Python = brain + governance
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time


class MessageType(Enum):
    # Godot → Python
    SENSOR_PACKET = "sensor_packet"
    ENTITY_STATE = "entity_state"
    PHYSICS_TICK = "physics_tick"
    ACTION_RESULT = "action_result"
    
    # Python → Godot
    ACTION = "action"
    SPAWN_PACKET = "spawn_packet"
    SET_MODE = "set_mode"
    RESET = "reset"


class EntityMode(Enum):
    REAL = "real"
    GHOST = "ghost"
    PLANNED = "planned"


@dataclass
class SensorPacket:
    """Sensory data from Godot."""
    entity_id: str
    position: List[float]
    velocity: List[float]
    salience: float
    timestamp: float


@dataclass
class Action:
    """Action to execute in Godot."""
    action_id: str
    mode: str  # ghost or real
    params: Dict[str, Any]


class GodotBridge:
    """
    Bridge between Python Field Core and Godot.
    
    Responsibilities:
    - Receive sensor packets from Godot
    - Send actions to Godot
    - Manage ghost/real workflow
    """
    
    def __init__(self):
        self.sensor_callbacks: List[Callable] = []
        self.entity_states: Dict[str, Dict] = {}
        self.ghost_scene: Dict[str, Dict] = {}
        self.last_tick: float = 0
    
    # === Receiving (Godot → Python) ===
    
    def receive(self, message: Dict):
        """Process incoming message from Godot."""
        msg_type = message.get("type")
        
        if msg_type == MessageType.SENSOR_PACKET.value:
            self._handle_sensor_packet(message)
        elif msg_type == MessageType.ENTITY_STATE.value:
            self._handle_entity_state(message)
        elif msg_type == MessageType.PHYSICS_TICK.value:
            self._handle_physics_tick(message)
        elif msg_type == MessageType.ACTION_RESULT.value:
            self._handle_action_result(message)
    
    def _handle_sensor_packet(self, msg: Dict):
        """Handle incoming sensor packet."""
        packet = SensorPacket(
            entity_id=msg["entity_id"],
            position=msg["pos"],
            velocity=msg["vel"],
            salience=msg["salience"],
            timestamp=msg["timestamp"]
        )
        
        # Store state
        self.entity_states[packet.entity_id] = {
            "position": packet.position,
            "velocity": packet.velocity,
            "salience": packet.salience,
            "timestamp": packet.timestamp
        }
        
        # Notify callbacks
        for callback in self.sensor_callbacks:
            callback(packet)
    
    def _handle_entity_state(self, msg: Dict):
        """Handle entity state update."""
        entity_id = msg["entity_id"]
        self.entity_states[entity_id] = msg["state"]
    
    def _handle_physics_tick(self, msg: Dict):
        """Handle physics tick notification."""
        self.last_tick = msg["timestamp"]
    
    def _handle_action_result(self, msg: Dict):
        """Handle action execution result."""
        # Placeholder for action feedback
        pass
    
    # === Sending (Python → Godot) ===
    
    def send_action(self, action_id: str, params: Dict, 
                   mode: str = "ghost") -> Dict:
        """
        Send action to Godot.
        
        Workflow:
        1. Send in ghost mode
        2. Evaluate result
        3. Promote to real if approved
        """
        message = {
            "type": MessageType.ACTION.value,
            "action_id": action_id,
            "mode": mode,
            "params": params,
            "timestamp": time.time()
        }
        
        return message  # In practice, send over WebSocket
    
    def spawn_packet(self, packet_id: str, position: List[float],
                    mode: str = "real") -> Dict:
        """Spawn a packet in Godot."""
        message = {
            "type": MessageType.SPAWN_PACKET.value,
            "packet_id": packet_id,
            "position": position,
            "mode": mode,
            "timestamp": time.time()
        }
        return message
    
    def set_mode(self, entity_id: str, mode: str) -> Dict:
        """Change entity mode (real/ghost/planned)."""
        message = {
            "type": MessageType.SET_MODE.value,
            "entity_id": entity_id,
            "mode": mode,
            "timestamp": time.time()
        }
        return message
    
    def reset(self) -> Dict:
        """Reset Godot scene."""
        message = {
            "type": MessageType.RESET.value,
            "timestamp": time.time()
        }
        return message
    
    # === Ghost Workflow ===
    
    def ghost_action(self, action_id: str, params: Dict,
                   governor_approve: Callable) -> tuple[bool, Dict]:
        """
        Execute action in ghost mode, evaluate, possibly promote.
        
        Returns: (success, result)
        """
        # 1. Execute in ghost mode
        result = self.send_action(action_id, params, mode="ghost")
        
        # 2. Wait for ghost result (simulated)
        ghost_result = self._simulate_ghost_result(action_id, params)
        
        # 3. Get Governor approval
        approved = governor_approve(ghost_result)
        
        if approved:
            # 4. Promote to real
            real_result = self.send_action(action_id, params, mode="real")
            return True, real_result
        else:
            return False, ghost_result
    
    def _simulate_ghost_result(self, action_id: str, params: Dict) -> Dict:
        """Simulate ghost action result (placeholder)."""
        return {
            "action_id": action_id,
            "mode": "ghost",
            "result": "simulated",
            "projected_outcome": params
        }
    
    # === Queries ===
    
    def get_entity(self, entity_id: str) -> Optional[Dict]:
        """Get current entity state."""
        return self.entity_states.get(entity_id)
    
    def get_all_entities(self) -> Dict[str, Dict]:
        """Get all entity states."""
        return self.entity_states.copy()
    
    def get_ghosts(self) -> Dict[str, Dict]:
        """Get all ghost entities."""
        return {k: v for k, v in self.entity_states.items() 
                if v.get("mode") == "ghost"}
    
    def on_sensor(self, callback: Callable[[SensorPacket], None]):
        """Register sensor packet callback."""
        self.sensor_callbacks.append(callback)


# === Operators ===

class MoveNodeOperator:
    """Move a node in Godot."""
    
    def __init__(self, bridge: GodotBridge):
        self.bridge = bridge
    
    def apply(self, node_id: str, delta: List[float],
             ghost: bool = True) -> Dict:
        """Move node by delta."""
        mode = "ghost" if ghost else "real"
        return self.bridge.send_action(
            "move_node",
            {"node_id": node_id, "delta": delta},
            mode=mode
        )


class SpawnPacketOperator:
    """Spawn a new packet in Godot."""
    
    def __init__(self, bridge: GodotBridge):
        self.bridge = bridge
    
    def apply(self, packet_id: str, position: List[float],
             energy: float = 1.0, ghost: bool = False) -> Dict:
        """Spawn packet at position."""
        mode = "ghost" if ghost else "real"
        return self.bridge.spawn_packet(packet_id, position, mode)


class ArmOperator:
    """Control robot arm (up/down/stop)."""
    
    def __init__(self, bridge: GodotBridge):
        self.bridge = bridge
    
    def up(self, ghost: bool = True) -> Dict:
        return self.bridge.send_action(
            "move_arm",
            {"direction": "up", "speed": 1.0},
            mode="ghost" if ghost else "real"
        )
    
    def down(self, ghost: bool = True) -> Dict:
        return self.bridge.send_action(
            "move_arm",
            {"direction": "down", "speed": 1.0},
            mode="ghost" if ghost else "real"
        )
    
    def stop(self, ghost: bool = True) -> Dict:
        return self.bridge.send_action(
            "move_arm",
            {"action": "stop"},
            mode="ghost" if ghost else "real"
        )


# === Demo: Invariant Formation ===

class InvariantDetector:
    """Detect invariant formations in Godot world."""
    
    def __init__(self, bridge: GodotBridge):
        self.bridge = bridge
        self.clusters: Dict[str, List[str]] = {}
        self.persistence: Dict[str, int] = {}
    
    def check(self, entity_id: str, position: List[float],
             radius: float = 2.0, min_ticks: int = 10) -> bool:
        """
        Check if entity is part of persistent cluster.
        
        Returns True if invariant formed.
        """
        # Find nearby entities
        nearby = []
        for other_id, state in self.bridge.get_all_entities().items():
            if other_id == entity_id:
                continue
            
            pos = state.get("position", [0, 0, 0])
            dist = ((position[0] - pos[0])**2 + 
                   (position[1] - pos[1])**2 + 
                   (position[2] - pos[2])**2) ** 0.5
            
            if dist < radius:
                nearby.append(other_id)
        
        # Track persistence
        cluster_key = "_".join(sorted(nearby))
        
        if cluster_key not in self.persistence:
            self.persistence[cluster_key] = 0
        
        self.persistence[cluster_key] += 1
        
        # Invariant formed?
        return self.persistence[cluster_key] >= min_ticks


if __name__ == "__main__":
    # Test
    bridge = GodotBridge()
    
    # Receive sample packet
    bridge.receive({
        "type": "sensor_packet",
        "entity_id": "Packet_42",
        "pos": [1.0, 2.0, 3.0],
        "vel": [0.1, 0.0, 0.0],
        "salience": 0.73,
        "timestamp": 123.45
    })
    
    print(f"Entities: {bridge.get_all_entities()}")
    
    # Test operators
    arm = ArmOperator(bridge)
    print(arm.up(ghost=True))
