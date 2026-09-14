"""Basic test for FieldCore Modular Structure."""

import numpy as np
import sys
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from field.core import InfoPacket, InformationField
from agent.core import SimSelf, Governor


def test_info_packet():
    """Test InfoPacket creation and operations."""
    packet = InfoPacket(
        id="test1",
        embedding=np.array([1.0, 0.0, 0.0]),
        metadata={"type": "test"}
    )
    
    assert packet.id == "test1"
    assert len(packet.embedding) == 3
    
    # Test similarity
    packet2 = InfoPacket(
        id="test2",
        embedding=np.array([1.0, 0.0, 0.0]),
        metadata={"type": "test2"}
    )
    
    similarity = packet.similarity(packet2)
    assert similarity > 0.9  # Nearly identical
    
    print("✓ InfoPacket test passed")


def test_information_field():
    """Test InformationField graph operations."""
    field = InformationField(embedding_dim=8)
    
    # Add packets
    p1 = InfoPacket(id="1", embedding=np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), metadata={})
    p2 = InfoPacket(id="2", embedding=np.array([0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), metadata={})
    p3 = InfoPacket(id="3", embedding=np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]), metadata={})
    
    field.add(p1)
    field.add(p2)
    field.add(p3)
    
    assert len(field) == 3
    
    # Query
    results = field.query(np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), radius=0.5)
    assert len(results) >= 1
    
    print("✓ InformationField test passed")


def test_sim_self():
    """Test SimSelf self-model."""
    sim = SimSelf(dim=8, initial_coherence=0.5)
    
    # Update with sensors
    sensors = {"touch": 0.8}
    sim.update(sensors)
    
    assert sim.coherence > 0
    assert len(sim.embedding) == 8
    
    # Test novelty
    novelty = sim.get_novelty()
    assert novelty >= 0
    
    print("✓ SimSelf test passed")


def test_governor():
    """Test Governor invariant enforcement."""
    gov = Governor(max_norm=4.0, min_coherence=0.45)
    
    # Good state
    good_state = {
        "coherence": 0.6,
        "embedding": np.array([1.0, 0.0, 0.0])
    }
    result = gov.check(good_state)
    assert result["allowed"] == True
    
    # Bad state (low coherence)
    bad_state = {
        "coherence": 0.3,
        "embedding": np.array([1.0, 0.0, 0.0])
    }
    result = gov.check(bad_state)
    assert result["allowed"] == False
    
    # Bad action
    bad_action = {"type": "delete_everything"}
    result = gov.check(good_state, bad_action)
    assert result["allowed"] == False
    
    print("✓ Governor test passed")


def test_full_loop():
    """Test full minimal loop."""
    # Create components
    field = InformationField(embedding_dim=8)
    sim = SimSelf(dim=8)
    gov = Governor()
    
    # Add packets
    for i in range(5):
        packet = InfoPacket(
            id=f"loop_{i}",
            embedding=np.random.randn(8),
            metadata={"index": i}
        )
        field.add(packet)
    
    # Update self
    sim.update({"touch": 0.5})
    
    # Check state
    state = {
        "coherence": sim.coherence,
        "embedding": sim.embedding
    }
    
    result = gov.check(state)
    assert result["allowed"] == True
    
    print("✓ Full loop test passed")


if __name__ == "__main__":
    test_info_packet()
    test_information_field()
    test_sim_self()
    test_governor()
    test_full_loop()
    print("\n✅ All integrated tests passed!")
