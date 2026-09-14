"""
Minimal Demo: Invariant Formation in Godot

Shows:
- Field sampling (LocalSampleOperator)
- Recursion (CentroidOperator)
- Governance (StabilityFilterOperator)
- Persistence (invariant creation)

30 cubes moving → persistent cluster → invariant node
"""

import random
import time
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
import math


@dataclass
class Packet:
    """Field packet (equivalent to Godot node)."""
    id: str
    position: Tuple[float, float, float]
    velocity: Tuple[float, float, float]
    salience: float = 1.0
    is_ghost: bool = False
    age: int = 0


class LocalSampleOperator:
    """Query packets within radius."""
    
    def __init__(self, radius: float = 2.0):
        self.radius = radius
    
    def query(self, packets: List[Packet], center: Tuple[float, float, float]) -> List[Packet]:
        """Get packets within radius of center."""
        results = []
        for p in packets:
            dist = self._distance(center, p.position)
            if dist < self.radius:
                results.append(p)
        return results
    
    def _distance(self, a: Tuple, b: Tuple) -> float:
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


class CentroidOperator:
    """Calculate cluster centroid."""
    
    def compute(self, packets: List[Packet]) -> Tuple[float, float, float]:
        """Get centroid of packet cluster."""
        if not packets:
            return (0.0, 0.0, 0.0)
        
        n = len(packets)
        cx = sum(p.position[0] for p in packets) / n
        cy = sum(p.position[1] for p in packets) / n
        cz = sum(p.position[2] for p in packets) / n
        
        return (cx, cy, cz)


class StabilityFilterOperator:
    """Filter for stable (low velocity variance) packets."""
    
    def __init__(self, velocity_threshold: float = 0.1):
        self.velocity_threshold = velocity_threshold
        self.history: Dict[str, List[Tuple]] = {}
        self.max_history = 10
    
    def is_stable(self, packet: Packet) -> bool:
        """Check if packet velocity is stable over time."""
        # Add to history
        if packet.id not in self.history:
            self.history[packet.id] = []
        
        self.history[packet.id].append(packet.velocity)
        
        # Trim history
        if len(self.history[packet.id]) > self.max_history:
            self.history[packet.id] = self.history[packet.id][-self.max_history:]
        
        # Check variance
        if len(self.history[packet.id]) < 3:
            return True  # Not enough data yet
        
        velocities = self.history[packet.id]
        mean = tuple(sum(x[i] for x in velocities) / len(velocities) for i in range(3))
        
        variance = sum(
            sum((v[i] - mean[i]) ** 2 for i in range(3))
            for v in velocities
        ) / len(velocities)
        
        return variance < self.velocity_threshold


class InvariantDetector:
    """Detect and create invariants."""
    
    def __init__(self, min_persistence: int = 10, cluster_radius: float = 2.0):
        self.min_persistence = min_persistence
        self.cluster_radius = cluster_radius
        
        # Track cluster persistence
        self.cluster_ticks: Dict[frozenset, int] = {}
        
        # Created invariants
        self.invariants: Dict[str, Packet] = {}
    
    def check_and_create(self, packets: List[Packet]) -> List[Packet]:
        """Check for new invariants."""
        new_invariants = []
        
        # Find clusters
        clusters = self._find_clusters(packets)
        
        # Check persistence
        for cluster in clusters:
            cluster_key = frozenset(c.id for c in cluster)
            
            if cluster_key not in self.cluster_ticks:
                self.cluster_ticks[cluster_key] = 0
            
            self.cluster_ticks[cluster_key] += 1
            
            # Create invariant if persistent enough
            if (self.cluster_ticks[cluster_key] >= self.min_persistence 
                and cluster_key not in self.invariants):
                
                # Create invariant packet
                centroid = self._centroid(cluster)
                invariant = Packet(
                    id=f"invariant_{len(self.invariants)}",
                    position=centroid,
                    velocity=(0.0, 0.0, 0.0),
                    salience=1.0,
                    is_ghost=False
                )
                self.invariants[cluster_key] = invariant
                new_invariants.append(invariant)
        
        return new_invariants
    
    def _find_clusters(self, packets: List[Packet]) -> List[List[Packet]]:
        """Find clusters of nearby packets."""
        clusters = []
        assigned: Set[str] = set()
        
        for packet in packets:
            if packet.id in assigned:
                continue
            
            # BFS to find cluster
            cluster = [packet]
            assigned.add(packet.id)
            queue = [packet]
            
            while queue:
                current = queue.pop(0)
                
                for other in packets:
                    if other.id in assigned:
                        continue
                    
                    dist = self._distance(current.position, other.position)
                    if dist < self.cluster_radius:
                        cluster.append(other)
                        assigned.add(other.id)
                        queue.append(other)
            
            if len(cluster) >= 3:  # Min cluster size
                clusters.append(cluster)
        
        return clusters
    
    def _distance(self, a: Tuple, b: Tuple) -> float:
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    
    def _centroid(self, packets: List[Packet]) -> Tuple[float, float, float]:
        n = len(packets)
        cx = sum(p.position[0] for p in packets) / n
        cy = sum(p.position[1] for p in packets) / n
        cz = sum(p.position[2] for p in packets) / n
        return (cx, cy, cz)


class WorldSimulator:
    """Simulates Godot world with moving packets."""
    
    def __init__(self, num_packets: int = 30, bounds: float = 10.0):
        self.num_packets = num_packets
        self.bounds = bounds
        
        # Create packets
        self.packets: List[Packet] = []
        for i in range(num_packets):
            pos = (
                random.uniform(-bounds, bounds),
                random.uniform(-bounds, bounds),
                random.uniform(-bounds, bounds)
            )
            vel = (
                random.uniform(-0.5, 0.5),
                random.uniform(-0.5, 0.5),
                random.uniform(-0.5, 0.5)
            )
            self.packets.append(Packet(
                id=f"Packet_{i}",
                position=pos,
                velocity=vel
            ))
    
    def step(self, delta: float = 0.1):
        """Update all packets."""
        for packet in self.packets:
            # Update position
            px = packet.position[0] + packet.velocity[0] * delta
            py = packet.position[1] + packet.velocity[1] * delta
            pz = packet.position[2] + packet.velocity[2] * delta
            
            # Bounce off bounds
            if abs(px) > self.bounds:
                packet.velocity = (-packet.velocity[0], packet.velocity[1], packet.velocity[2])
            if abs(py) > self.bounds:
                packet.velocity = (packet.velocity[0], -packet.velocity[1], packet.velocity[2])
            if abs(pz) > self.bounds:
                packet.velocity = (packet.velocity[0], packet.velocity[1], -packet.velocity[2])
            
            packet.position = (px, py, pz)
            packet.age += 1


def run_demo(ticks: int = 100):
    """Run invariant formation demo."""
    print("=== Invariant Formation Demo ===")
    
    # Create world
    world = WorldSimulator(num_packets=30)
    
    # Create operators
    local_sample = LocalSampleOperator(radius=2.0)
    centroid = CentroidOperator()
    stability = StabilityFilterOperator(velocity_threshold=0.1)
    invariant_detector = InvariantDetector(min_persistence=10, cluster_radius=2.0)
    
    print(f"Created {len(world.packets)} packets")
    
    # Run simulation
    for tick in range(ticks):
        world.step()
        
        # Check for invariants
        new_invariants = invariant_detector.check_and_create(world.packets)
        
        if new_invariants:
            print(f"\nTick {tick}: NEW INVARIANT CREATED!")
            for inv in new_invariants:
                print(f"  - {inv.id} at {inv.position}")
        
        if tick % 20 == 0:
            print(f"Tick {tick}: {len(world.packets)} packets, "
                  f"{len(invariant_detector.invariants)} invariants")
    
    print(f"\n=== Final State ===")
    print(f"Total invariants: {len(invariant_detector.invariants)}")
    for key, inv in invariant_detector.invariants.items():
        print(f"  {inv.id}: {inv.position}")
    
    return invariant_detector.invariants


if __name__ == "__main__":
    run_demo()
