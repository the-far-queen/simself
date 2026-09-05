"""
Stalk — Formal Data Structure

NOTE (2026-03-07):
- Nested stalks: Stalks within stalks - hierarchical structure for complex reasoning
- Atomic nodules: Granularized nodes within stalks - smallest update units
- Fail up: When sub-stalk fails, escalate to parent stalk instead of crashing
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Tuple
import uuid
import datetime

@dataclass
class Stalk:
    """
    Formal Stalk Data Structure — Executable Definition.
    As described in 'Formal Stalk Data Structure.md'.
    A stalk represents local information about a point in the latent manifold.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    # The 'value' of the stalk in its local vector space
    embedding: np.ndarray = field(default_factory=lambda: np.random.rand(128)) 
    # The 'precision' of the embedding (e.g., FP16, FP32, BitNet)
    precision: str = "FP32"  
    # Invariants are predicates that must hold true for this stalk's meaning
    invariants: Dict[str, Any] = field(default_factory=dict)
    # Contextual metadata (e.g., source, reliability, current attention)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # History for temporal coherence and debugging
    history: List[Tuple[datetime.datetime, np.ndarray]] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.embedding, np.ndarray):
            self.embedding = np.array(self.embedding)
        self.history.append((self.timestamp, self.embedding.copy()))

    def update_embedding(self, new_embedding: np.ndarray, new_precision: str = "FP32", new_invariants: Optional[Dict] = None, new_metadata: Optional[Dict] = None):
        """Updates the stalk's embedding and related attributes."""
        if not isinstance(new_embedding, np.ndarray):
            new_embedding = np.array(new_embedding)
        self.embedding = new_embedding
        self.precision = new_precision
        if new_invariants:
            self.invariants.update(new_invariants)
        if new_metadata:
            self.metadata.update(new_metadata)
        self.timestamp = datetime.datetime.now()
        self.history.append((self.timestamp, self.embedding.copy()))
        print(f"Stalk {self.id[:4]} updated. Coherence: {self.get_coherence():.2f}")

    def check_invariants(self, current_context: Optional[Dict] = None) -> Tuple[bool, List[str]]:
        """
        Checks if the stalk's invariants still hold true in the given context.
        Simplified: checks for non-negativity and sum property for some metadata.
        """
        violations = []
        if self.invariants.get("non_negative_embedding", False) and np.any(self.embedding < 0):
            violations.append("non_negative_embedding violated")
        sum_field = self.invariants.get("sum_to_one_metadata_field")
        if sum_field and abs(self.metadata.get(sum_field, 0.0) - 1.0) > 1e-6:
            violations.append("'{}' sum to one violated".format(sum_field))
        
        # More complex checks based on embedding properties would go here
        
        return len(violations) == 0, violations

    def get_coherence(self) -> float:
        """
        Calculates the internal coherence of the stalk.
        Simplified: Inverse of embedding variance, capped at 1.0.
        """
        if len(self.history) < 2:
            return 1.0 # Perfectly coherent if no history of change
        
        embeddings_over_time = np.array([h[1] for h in self.history])
        variance = np.var(embeddings_over_time, axis=0).mean()
        
        # Inverse relationship with variance, but bounded
        coherence = max(0.0, 1.0 - variance * 5.0) # Scale factor to make variance impact visible
        return coherence

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the stalk to a dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "embedding": self.embedding.tolist(),
            "precision": self.precision,
            "invariants": self.invariants,
            "metadata": self.metadata,
            "history": [(ts.isoformat(), emb.tolist()) for ts, emb in self.history]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Stalk':
        """Deserializes a stalk from a dictionary."""
        stalk = cls(
            id=data["id"],
            embedding=np.array(data["embedding"]),
            precision=data["precision"],
            invariants=data["invariants"],
            metadata=data["metadata"]
        )
        stalk.timestamp = datetime.datetime.fromisoformat(data["timestamp"])
        stalk.history = [(datetime.datetime.fromisoformat(ts), np.array(emb)) for ts, emb in data["history"]]
        return stalk

if __name__ == '__main__':
    print("--- Running Stalk module simulation ---")

    # 1. Create a basic stalk
    stalk1 = Stalk(embedding=np.array([0.1, 0.2, 0.3]), precision="FP16", metadata={"source": "sensor_fusion"})
    stalk1.invariants["non_negative_embedding"] = True
    print(f"Stalk 1 created: ID={stalk1.id[:4]}, Coherence={stalk1.get_coherence():.2f}")

    # 2. Update the stalk
    stalk1.update_embedding(np.array([0.15, 0.25, 0.35]), new_metadata={"sensor_id": "LIDAR"})
    print(f"Stalk 1 updated. Coherence={stalk1.get_coherence():.2f}")

    # 3. Check invariants
    is_valid, violations = stalk1.check_invariants()
    print(f"Stalk 1 invariants valid: {is_valid}, Violations: {violations}")

    # 4. Create another stalk that might violate an invariant
    stalk2 = Stalk(embedding=np.array([-0.1, 0.5, 0.2]), precision="FP32", metadata={"source": "LLM_embedding"})
    stalk2.invariants["non_negative_embedding"] = True # This one will fail
    is_valid2, violations2 = stalk2.check_invariants()
    print(f"Stalk 2 invariants valid: {is_valid2}, Violations: {violations2}")

    # 5. Test serialization/deserialization
    stalk1_dict = stalk1.to_dict()
    reconstructed_stalk = Stalk.from_dict(stalk1_dict)
    print("Reconstructed Stalk ID: {}, Coherence: {:.2f}".format(reconstructed_stalk.id[:4], reconstructed_stalk.get_coherence()))
    assert np.array_equal(stalk1.embedding, reconstructed_stalk.embedding)
    assert stalk1.precision == reconstructed_stalk.precision
    print("Serialization/Deserialization successful.")
