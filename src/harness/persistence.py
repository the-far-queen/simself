import json
import os
from typing import TYPE_CHECKING, Dict, Any

# Type checking for SimSelfAgent to avoid circular imports at runtime
if TYPE_CHECKING:
    from main import SimSelfAgent
    from core.governor import Governor
    from core.ledger import Ledger
    from reuse_game.resources import Resources

class PersistenceManager:
    """
    Manages saving and loading the complete state of the SimSelf agent,
    referred to as "soul-file snapshots" in fieldcore-code.md.
    """
    def __init__(self, snapshot_dir: str = "data/snapshots"):
        self.snapshot_dir = snapshot_dir
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)
        print(f"PersistenceManager: Snapshots will be stored in '{self.snapshot_dir}'.")

    def save_agent_state(self, agent: 'SimSelfAgent', filename: str = "latest_snapshot.json"):
        """
        Saves the current state of the SimSelfAgent to a JSON file.
        """
        file_path = os.path.join(self.snapshot_dir, filename)
        
        # Collect state from various components
        agent_state = {
            "step_count": agent.step_count,
            "coherence": agent.coherence,
            "governor_state": agent.governor.get_state_summary(),
            "resources_state": agent.resources.get_status(), # Assuming resources module is integrated
            "ledger_db_path": agent.ledger.db_path, # Only save the path, not the whole DB
            # Add other component states as needed (e.g., metrics, memory)
        }

        try:
            with open(file_path, 'w') as f:
                json.dump(agent_state, f, indent=4)
            print(f"PersistenceManager: Agent state saved to '{file_path}'.")
        except IOError as e:
            print(f"PersistenceManager Error: Could not save state. {e}")

    def load_agent_state(self, agent: 'SimSelfAgent', filename: str = "latest_snapshot.json"):
        """
        Loads the agent's state from a JSON file and reconstructs the agent's components.
        NOTE: This is a simplified load. In a real system, the agent's components
        would need to be re-initialized with the loaded data, or existing components
        updated. This current implementation directly modifies the agent's attributes
        and those of its sub-components.
        """
        file_path = os.path.join(self.snapshot_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"PersistenceManager Warning: Snapshot file '{file_path}' not found. Cannot load state.")
            return

        try:
            with open(file_path, 'r') as f:
                agent_state = json.load(f)
            
            # Apply loaded state to agent components
            agent.step_count = agent_state.get("step_count", agent.step_count)
            agent.coherence = agent_state.get("coherence", agent.coherence)
            
            governor_state = agent_state.get("governor_state")
            if governor_state:
                # Update individual axes in the existing governor
                for axis, value in governor_state.items():
                    agent.governor.agency_axes[axis] = value
            
            resources_state = agent_state.get("resources_state")
            if resources_state:
                # Update individual resource levels in the existing resources manager
                agent.resources.stamina = resources_state.get("stamina", agent.resources.stamina)
                agent.resources.cognitive_load = resources_state.get("cognitive_load", agent.resources.cognitive_load)
            
            ledger_path = agent_state.get("ledger_db_path")
            if ledger_path and agent.ledger.db_path != ledger_path:
                print(f"PersistenceManager: Ledger DB path changed from {agent.ledger.db_path} to {ledger_path}. Reconnecting.")
                # Closing existing connection and re-initializing with the new path
                from core.ledger import Ledger # Local import to avoid circular dependency at top
                agent.ledger.close()
                agent.ledger = Ledger(ledger_path)

            print(f"PersistenceManager: Agent state loaded from '{file_path}'.")
        except (IOError, json.JSONDecodeError) as e:
            print(f"PersistenceManager Error: Could not load state from '{file_path}'. {e}")

if __name__ == '__main__':
    print("--- Running Persistence module simulation ---")
    
    # Mock classes to simulate the SimSelfAgent and its components for testing.
    class MockGovernor:
        def __init__(self): self.agency_axes = {"agency_will": 0.5, "focus": 0.7}
        def get_state_summary(self): return self.agency_axes
    
    class MockLedger:
        def __init__(self, db_path): self.db_path = db_path
        def close(self): print(f"MockLedger: Closing connection to {self.db_path}")
    
    class MockResources:
        def __init__(self): self.stamina = 100.0; self.cognitive_load = 0.0
        def get_status(self): return {"stamina": self.stamina, "cognitive_load": self.cognitive_load}
    
    class MockSimSelfAgent:
        def __init__(self):
            self.step_count = 0
            self.coherence = 1.0
            self.governor = MockGovernor()
            self.ledger = MockLedger("data/mock_ledger.db")
            self.resources = MockResources()

    # Ensure a 'data' directory for the snapshot_dir
    if not os.path.exists('data'):
        os.makedirs('data')
    
    persistence = PersistenceManager(snapshot_dir="data/mock_snapshots")
    mock_agent = MockSimSelfAgent()

    print("1. Saving initial agent state.")
    persistence.save_agent_state(mock_agent, "initial_state.json")

    # Simulate some changes in the agent's state
    mock_agent.step_count = 10
    mock_agent.coherence = 0.8
    mock_agent.governor.agency_axes['agency_will'] = 0.6
    mock_agent.resources.stamina = 80.0
    mock_agent.resources.cognitive_load = 30.0
    mock_agent.ledger.db_path = "data/new_mock_ledger.db" # Simulate ledger path change

    print("2. Saving modified agent state.")
    persistence.save_agent_state(mock_agent, "modified_state.json")

    # Create a new agent and load the initial state
    new_mock_agent = MockSimSelfAgent()
    print("3. Loading initial state into a new agent.")
    persistence.load_agent_state(new_mock_agent, "initial_state.json")

    print("Loaded Agent State Summary (from initial_state.json):")
    print(f"  Step Count: {new_mock_agent.step_count}")
    print(f"  Coherence: {new_mock_agent.coherence}")
    print(f"  Agency Will: {new_mock_agent.governor.get_state_summary()['agency_will']}")
    print(f"  Stamina: {new_mock_agent.resources.get_status()['stamina']}")
    print(f"  Cognitive Load: {new_mock_agent.resources.get_status()['cognitive_load']}")
    print(f"  Ledger DB Path: {new_mock_agent.ledger.db_path}")

    # Create another new agent and load the modified state
    another_mock_agent = MockSimSelfAgent()
    print("4. Loading modified state into another new agent.")
    persistence.load_agent_state(another_mock_agent, "modified_state.json")

    print("Loaded Agent State Summary (from modified_state.json):")
    print(f"  Step Count: {another_mock_agent.step_count}")
    print(f"  Coherence: {another_mock_agent.coherence}")
    print(f"  Agency Will: {another_mock_agent.governor.get_state_summary()['agency_will']}")
    print(f"  Stamina: {another_mock_agent.resources.get_status()['stamina']}")
    print(f"  Cognitive Load: {another_mock_agent.resources.get_status()['cognitive_load']}")
    print(f"  Ledger DB Path: {another_mock_agent.ledger.db_path}")

    # Cleanup mock snapshot directory (optional)
    # import shutil
    # if os.path.exists("data/mock_snapshots"):
    #     shutil.rmtree("data/mock_snapshots")
