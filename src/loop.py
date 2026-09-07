# Main Cycle — Observe → Decide → Act → Reflect

"""
Core loop: sense, decide, act, reflect.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from .environment import Environment
from .signals import signal_pool
from .actions import Action, ActionType, wait, refuse


@dataclass
class CycleResult:
    """Result of one cycle."""
    observation: Dict
    decision: Action
    action_taken: Action
    reflection: Dict
    metrics: Dict


class MainLoop:
    """Main agent cycle."""
    
    def __init__(self, environment: Environment, governor, controller):
        self.env = environment
        self.governor = governor
        self.controller = controller
        self.cycle_count = 0
    
    def cycle(self, external_input: Optional[Dict] = None) -> CycleResult:
        """Execute one complete cycle."""
        self.cycle_count += 1
        
        # 1. OBSERVE
        observation = self.env.step({"type": "wait"})  # Get current state
        if external_input:
            observation.update(external_input)
        
        # Get signals
        signals = signal_pool.sample_all(observation)
        
        # 2. DECIDE (via governor/controller)
        decision = self._decide(observation, signals)
        
        # Check boundary with governor
        boundary_check = self.governor.check_all()
        if not boundary_check["allowed"]:
            # Override with refuse if critical
            if boundary_check.get("critical_violated"):
                decision = refuse(boundary_check["violated"][0])
        
        # 3. ACT
        action_dict = decision.to_dict()
        result = self.env.step(action_dict)
        
        # 4. REFLECT
        reflection = self._reflect(observation, decision, result, signals)
        
        # 5. UPDATE METRICS
        metrics = {
            "cycle": self.cycle_count,
            "signals": signals,
            "decision_type": decision.type.value,
            "boundary_passed": boundary_check["allowed"]
        }
        
        return CycleResult(
            observation=observation,
            decision=decision,
            action_taken=decision,  # Could differ if refused
            reflection=reflection,
            metrics=metrics
        )
    
    def _decide(self, observation: Dict, signals: Dict) -> Action:
        """Make decision (placeholder - connect to actual controller)."""
        # This would call the actual governor/controller
        # For now: simple random
        from .actions import wait
        return wait()
    
    def _reflect(self, observation: Dict, decision: Action, 
                 result: Dict, signals: Dict) -> Dict:
        """Reflect on what happened."""
        return {
            "outcome": result,
            "signals_received": signals,
            "action_decided": decision.type.value,
            "coherence_impact": 0.0  # Would calculate
        }
    
    def run(self, n_cycles: int, external_input_fn=None):
        """Run for n cycles."""
        results = []
        for i in range(n_cycles):
            ext_in = external_input_fn(i) if external_input_fn else None
            result = self.cycle(ext_in)
            results.append(result)
            
            if i % 10 == 0:
                print(f"Cycle {i}: {result.decision.type.value}")
        
        return results


# Example usage
if __name__ == "__main__":
    from .environment import create_simple_env
    from .core.boundaries import boundaries
    
    env = create_simple_env()
    loop = MainLoop(env, boundaries, None)
    
    results = loop.run(10)
    print(f"Ran {len(results)} cycles")
