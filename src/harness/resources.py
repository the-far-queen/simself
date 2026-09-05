from typing import Dict, Any

# Note: The original code imported `StateVector` from `core.state_vector`,
# but that module is not part of this package. The Resources class is
# duck-typed against anything that exposes `resource_pools` (a dict with
# 'agency_budget' and 'cognitive_friction' entries). The `__main__` block
# below demonstrates usage with a MockStateVector.

class Resources:
    """
    Manages the agent's internal resources such as 'stamina' and 'cognitive load',
    as described in fieldcore-code.md ("Agency budget, stamina, cognitive load").
    These resources are now integrated with the agent's central StateVector.
    """
    def __init__(self, state_vector: 'StateVector'):
        self._state_vector = state_vector
        
        # Initialize from StateVector's resource_pools, or use defaults
        agency_budget = self._state_vector.resource_pools['agency_budget']
        cognitive_friction = self._state_vector.resource_pools['cognitive_friction']
        
        self.max_stamina = agency_budget.get('max', 100.0)
        # Stamina is now directly represented by agency_budget current
        
        self.max_cognitive_load = cognitive_friction.get('max', 1.0) * 100 # Scale for easier use (0-100)
        # Cognitive load is now directly represented by cognitive_friction current (scaled)
        
        print(f"Resources: Initialized. StateVector Stamina (Agency Budget)={self._state_vector.resource_pools['agency_budget']['current']:.1f}, Cognitive Load={self._state_vector.resource_pools['cognitive_friction']['current'] * 100:.1f}.")

    def consume_stamina(self, amount: float) -> bool:
        """
        Decreases stamina (agency budget) in the StateVector.
        Returns True if stamina was sufficient, False otherwise.
        """
        current_stamina = self._state_vector.resource_pools['agency_budget']['current']
        if current_stamina >= amount:
            self._state_vector.resource_pools['agency_budget']['current'] = max(0.0, current_stamina - amount)
            print(f"Resources: Consumed {amount:.1f} stamina. Remaining: {self._state_vector.resource_pools['agency_budget']['current']:.1f}.")
            return True
        print(f"Resources: Insufficient stamina to consume {amount:.1f}. Current: {self._state_vector.resource_pools['agency_budget']['current']:.1f}.")
        return False

    def regenerate_stamina(self, amount: float):
        """
        Increases stamina (agency budget) in the StateVector, up to max_stamina.
        """
        current_stamina = self._state_vector.resource_pools['agency_budget']['current']
        self._state_vector.resource_pools['agency_budget']['current'] = min(self.max_stamina, current_stamina + amount)
        print(f"Resources: Regenerated {amount:.1f} stamina. Current: {self._state_vector.resource_pools['agency_budget']['current']:.1f}.")

    def increase_cognitive_load(self, amount: float):
        """
        Increases cognitive load (cognitive friction) in the StateVector, up to max_cognitive_load.
        High cognitive load can impair decision-making. (Scaled 0-100 internally for direct StateVector use 0-1)
        """
        current_load = self._state_vector.resource_pools['cognitive_friction']['current'] * 100
        new_load = min(self.max_cognitive_load, current_load + amount)
        self._state_vector.resource_pools['cognitive_friction']['current'] = new_load / 100 # Store as 0-1
        print(f"Resources: Increased cognitive load by {amount:.1f}. Current: {new_load:.1f}.")

    def decrease_cognitive_load(self, amount: float):
        """
        Decreases cognitive load (cognitive friction) in the StateVector, down to 0.0.
        """
        current_load = self._state_vector.resource_pools['cognitive_friction']['current'] * 100
        new_load = max(0.0, current_load - amount)
        self._state_vector.resource_pools['cognitive_friction']['current'] = new_load / 100 # Store as 0-1
        print(f"Resources: Decreased cognitive load by {amount:.1f}. Current: {new_load:.1f}.")

if __name__ == '__main__':
    print("--- Running Resources module simulation (with Mock StateVector) ---")
    
    class MockStateVector:
        def __init__(self):
            self.resource_pools = {
                "agency_budget": {"current": 100.0, "max": 100.0, "recharge_rate": 10.0, "description": "Action points available"},
                "cognitive_friction": {"current": 0.0, "max": 1.0, "recharge_rate": 0.0, "description": "Mental fatigue — higher = more exhausted"},
                "somatic_load": {"current": 0.0, "max": 1.0, "recharge_rate": 0.0, "description": "System stress — higher = strained"},
                "snr_reserve": {"current": 1.0, "max": 1.0, "recharge_rate": 0.0, "description": "Signal-to-noise ratio capacity"}
            }

    mock_state_vector = MockStateVector()
    resources = Resources(state_vector=mock_state_vector)
    
    print("\nInitial State:")
    print(f"  Stamina: {mock_state_vector.resource_pools['agency_budget']['current']:.1f}")
    print(f"  Cognitive Load: {mock_state_vector.resource_pools['cognitive_friction']['current'] * 100:.1f}")

    print("\n1. Consume stamina for an action.")
    resources.consume_stamina(20.0)
    resources.consume_stamina(50.0)
    
    print("\n2. Attempt to consume more stamina than available.")
    resources.consume_stamina(40.0) # Should fail
    
    print("\n3. Regenerate stamina.")
    resources.regenerate_stamina(30.0)
    
    print("\n4. Increase cognitive load from a complex task.")
    resources.increase_cognitive_load(30.0)
    resources.increase_cognitive_load(60.0)
    
    print("\n5. Decrease cognitive load after reflection.")
    resources.decrease_cognitive_load(40.0)
    
    print("\n--- Final Resource Status (from StateVector) ---")
    print(f"  Stamina: {mock_state_vector.resource_pools['agency_budget']['current']:.1f}")
    print(f"  Cognitive Load: {mock_state_vector.resource_pools['cognitive_friction']['current'] * 100:.1f}")
