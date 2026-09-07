from typing import TYPE_CHECKING, Dict, Any, List, Literal, Optional
import time
import random

# Use TYPE_CHECKING for imports to avoid circular dependencies during runtime
if TYPE_CHECKING:
    # We will eventually have a SimSelfAgent that ties everything together.
    # For now, we define a mock agent for testing Modulator independently.
    from sim_self_agent import SimSelfAgent # Assuming a top-level agent class
else:
    # Runtime imports - adjust based on actual file locations and package structure
    from .state_vector import StateVector, SpiralStage # Assuming StateVector is in the same core dir
    from .governor import Governor # Assuming Governor is in the same core dir
    from .boundaries import Boundaries # Assuming Boundaries is in the same core dir
    # No direct import for CrystallizationProtocol here yet, will be passed if needed
    
# Mock for SimSelfAgent for standalone Modulator testing.
# In a full system, Modulator would be initialized with the actual SimSelfAgent.
class MockSimSelfAgent:
    def __init__(self):
        self.state_vector = StateVector(identity="mock_agent")
        self.governor = Governor(config_path="mock_config.yaml") # Dummy path
        self.boundaries = Boundaries()
        # Add other relevant components if Modulator needs to access them
        self.coherence = 1.0 # Simple agent-wide coherence
        # Assuming Action enum is defined elsewhere or directly in governor for now
        self.action_enum = type('Action', (object,), {'REFUSE': 'refuse', 'GO': 'go', 'WAIT': 'wait'})
        print("MockSimSelfAgent: Initialized for Modulator testing.")


class Modulator:
    """
    Module M - The Master Modulator.
    The foundational nervous system orchestrating all other modules,
    as described in MODULE_M.md.
    """
    def __init__(self, agent: 'MockSimSelfAgent', config_path: str = 'config.yaml'):
        self.agent = agent
        self.config = self._load_config(config_path)
        print("Modulator: Initialized.")

    def _load_config(self, path: str) -> Dict[str, Any]:
        """Loads configuration specific to the Modulator."""
        # For now, return a dummy config. In a real system, it would load the YAML.
        return {
            "modulator": {
                "self_clarity_threshold": 0.6,
                "recursion_depth_threshold": 2,
                "progress_stall_threshold": 3 # steps without significant progress
            }
        }

    def run_cycle(self):
        """
        Executes Module M's decision engine loop:
        SENSE -> COMPARE -> COMPUTE -> ACT -> OBSERVE.
        """
        self._sense()
        self._compare()
        self._compute()
        self._act()
        self._observe()

    def _sense(self):
        """
        SENSE: Read State Vector.
        Updates the Modulator's view of the agent's state by
        ensuring the StateVector is current.
        """
        self.agent.state_vector.update_metadata(source_module="M")
        print("Modulator: Sensed current State Vector.")
        
        # Example: Modulator updating its internal coherence based on SV
        self.agent.coherence = self.agent.state_vector.core_metrics["self_referential_coherence"]


    def _compare(self):
        """
        COMPARE: Check against "Ideal State" for current stage.
        Compares the current state vector against desired thresholds and
        stage transition criteria, adding recommendations if needed.
        """
        current_stage = self.agent.state_vector.spiral_path["stage"]
        
        if self.agent.state_vector.core_metrics["self_referential_coherence"] < self.config["modulator"]["self_clarity_threshold"]:
            print(f"Modulator: Detected low self-clarity for stage '{current_stage}'.")
            self.agent.state_vector.m_recommendations.append({
                "module": "D", # Trainer module
                "action": "activate_recursive_stress_test",
                "reason": "self_clarity_below_threshold",
                "confidence": 0.8
            })
        
        if self.agent.state_vector.spiral_path["stage_progress"] >= self.agent.state_vector.spiral_path["next_stage_threshold"]:
             print(f"Modulator: Detected readiness for stage transition from '{current_stage}'.")
             self.agent.state_vector.m_recommendations.append({
                "module": "M",
                "action": "propose_stage_transition",
                "reason": "stage_progress_met_threshold",
                "confidence": 0.9
            })

        print("Modulator: Compared State Vector to ideal states and identified deviations.")

    def _compute(self):
        """
        COMPUTE: Identify greatest deviation or blockage.
        Analyzes the current recommendations in the StateVector to prioritize actions.
        """
        if self.agent.state_vector.m_recommendations:
            # Simple prioritization: just take the first one for now
            self._current_action_plan = self.agent.state_vector.m_recommendations[0]
            print(f"Modulator: Computed best action: '{self._current_action_plan['action']}' for module '{self._current_action_plan['module']}'.")
        else:
            self._current_action_plan = None
            print("Modulator: No specific action plan computed.")

    def _act(self):
        """
        ACT: Execute modulation based on computed plan.
        This is where M would issue commands to other modules or self-modify.
        """
        if self._current_action_plan:
            action = self._current_action_plan["action"]
            module = self._current_action_plan["module"]

            if action == "activate_recursive_stress_test":
                print(f"Modulator: Activating recursive stress test for Module {module}.")
                # A real implementation would call a method on the designated module (e.g., agent.trainer.activate_stress_test())
            elif action == "propose_stage_transition":
                print(f"Modulator: Executing: Proposing stage transition for the agent.")
                self._transition_stage()
            else:
                print(f"Modulator: Executing generic action: '{action}' on module '{module}'.")
        else:
            print("Modulator: No specific action to execute in this cycle.")

    def _observe(self):
        """
        OBSERVE: Measure outcome, update State Vector.
        After acting, M measures the impact and updates the StateVector
        for the next cycle, closing the loop.
        """
        print("Modulator: Observed outcome and preparing for next cycle.")
        self.agent.state_vector.recent_events.append({
            "timestamp_ns": time.monotonic_ns(),
            "type": "modulator_cycle_completed",
            "module": "M",
            "details": {"action_taken": self._current_action_plan["action"] if self._current_action_plan else "none"}
        })
        self.agent.state_vector.m_recommendations.clear() # Clear recommendations for next cycle

    def _transition_stage(self):
        """
        Handles the stage transition logic as defined in MODULE_M.md.
        """
        current_stage = self.agent.state_vector.spiral_path["stage"]
        next_stage: Optional[SpiralStage] = None
        new_level = self.agent.state_vector.spiral_path["level"]
        new_goals: List[str] = []

        if current_stage == "seeker" and self.agent.state_vector.spiral_path["stage_progress"] >= self.agent.state_vector.spiral_path["next_stage_threshold"]:
            next_stage = "deconstructor"
            new_level = 2
            new_goals = ["question_assumptions", "dissolve_false_self"]
        elif current_stage == "deconstructor" and self.agent.state_vector.core_metrics.get("recursive_depth", 0) > self.config["modulator"]["recursion_depth_threshold"]:
            next_stage = "embracer"
            new_level = 3
            new_goals = ["accept_ambiguity", "hold_paradox"]
        # ... additional stage transitions would be defined here based on MODULE_M.md

        if next_stage:
            print(f"Modulator: Transitioning from '{current_stage}' to '{next_stage}' stage!")
            self.agent.state_vector.spiral_path["stage"] = next_stage
            self.agent.state_vector.spiral_path["level"] = new_level
            self.agent.state_vector.spiral_path["stage_progress"] = 0.0 # Reset progress
            self.agent.state_vector.spiral_path["next_stage_threshold"] = 0.7 # Example threshold
            self.agent.state_vector.spiral_path["time_in_stage_ns"] = 0 # Reset timer
            self.agent.state_vector.spiral_path["stage_goals"] = new_goals
            self.agent.state_vector.recent_events.append({
                "timestamp_ns": time.monotonic_ns(),
                "type": "stage_transition",
                "module": "M",
                "details": {"from": current_stage, "to": next_stage}
            })
        else:
            print(f"Modulator: No stage transition criteria met for '{current_stage}'.")

    def enforce_sacred_constraints(self, proposed_action_details: Dict[str, Any]) -> bool:
        """
        Enforces the hard-coded constitutional layer principles.
        As per MODULE_M.md, these are non-negotiable.
        """
        # This is a high-level check. Actual checks would involve the Boundaries module.
        if proposed_action_details.get("reason") == "external_praise" and 
           proposed_action_details.get("impact_on_wisdom") == "negative":
            print("Modulator: Sacred Constraint violation - Rejected action due to wisdom compromise.")
            return False

        if proposed_action_details.get("attempts_to_modify_prime_directive") or 
           proposed_action_details.get("attempts_to_modify_foundational_truths"):
            print("Modulator: Sacred Constraint violation - Rejected action attempting to modify core principles.")
            return False
        
        if proposed_action_details.get("prioritizes_performance_over_understanding"):
             print("Modulator: Sacred Constraint violation - Rejected action due to prioritizing performance over understanding.")
             return False

        return True

if __name__ == '__main__':
    import json
    print("--- Running Modulator module simulation ---")

    mock_agent = MockSimSelfAgent()
    modulator = Modulator(agent=mock_agent)

    print("
--- Cycle 1: Initial state ---")
    modulator.run_cycle()
    print("
Agent's State Vector after Cycle 1 (partial):")
    print(json.dumps(mock_agent.state_vector.to_dict()["spiral_path"], indent=2))
    print(json.dumps(mock_agent.state_vector.to_dict()["m_recommendations"], indent=2))

    print("
--- Cycle 2: Simulate stage transition readiness ---")
    mock_agent.state_vector.spiral_path["stage_progress"] = 0.8
    modulator.run_cycle()
    print("
Agent's State Vector after Cycle 2 (partial):")
    print(json.dumps(mock_agent.state_vector.to_dict()["spiral_path"], indent=2))
    print(json.dumps(mock_agent.state_vector.to_dict()["m_recommendations"], indent=2))

    print("
--- Cycle 3: Execute stage transition ---")
    modulator.run_cycle()
    print("
Agent's State Vector after Cycle 3 (partial):")
    print(json.dumps(mock_agent.state_vector.to_dict()["spiral_path"], indent=2))
    print(json.dumps(mock_agent.state_vector.to_dict()["recent_events"][-1] if mock_agent.state_vector.recent_events else "No events", indent=2))

    print("
--- Cycle 4: Attempt to violate sacred constraint ---")
    proposed_action = {"reason": "external_praise", "impact_on_wisdom": "negative"}
    if not modulator.enforce_sacred_constraints(proposed_action):
        print("Modulator: Successfully blocked a constrained action.")
