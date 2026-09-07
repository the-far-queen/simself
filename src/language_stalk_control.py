"""
Language Stalk + Robot Control Loop - FieldCore v1

Full language→vision→motor pipeline with asynchronous gluing.

Based on docs/fieldcore/docs/stalk-gluing1.txt
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time


# === LANGUAGE STALK ===

class LanguageStalk:
    """
    Language stalk that learns projection φ_L: ℱ_L → Z
    Freezes LLM backbone, trains only projection head.
    """
    
    def __init__(self, llm_backbone: nn.Module = None, z_dim: int = 64):
        # Frozen LLM for language understanding (or mock)
        self.llm = llm_backbone
        if self.llm is not None:
            for param in self.llm.parameters():
                param.requires_grad = False
        
        # Output dim (or default)
        self.output_dim = 512  # Default LLM embedding size
        
        # Learnable projection head
        self.projection_head = nn.Sequential(
            nn.Linear(self.output_dim, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Linear(128, z_dim),
            nn.Tanh()  # Bounded output for safety
        )
        
        # Eligibility trace for delayed credit assignment
        self.eligibility_trace: Dict[str, torch.Tensor] = {}
        
        # Physical invariants learned through gluing
        self.learned_invariants = {
            "mass_implies_force": True,
            "liquid_implies_container": True,
            "fragile_implies_gentle": True
        }
        
        # Tracking
        self.projection_updates = 0
        self.z_dim = z_dim
        
        # Current command
        self.current_command: Optional[str] = None
    
    def parse_and_project(self, text: str) -> Tuple[torch.Tensor, Dict]:
        """
        Parse text and project to shared space Z.
        """
        # 1. Get LLM embedding (or mock)
        if self.llm is not None:
            with torch.no_grad():
                llm_embedding = self.llm.encode(text)
        else:
            # Mock embedding for testing
            llm_embedding = torch.randn(self.output_dim)
        
        # 2. Apply learnable projection
        z_projection = self.projection_head(llm_embedding)
        
        # 3. Extract physical constraints
        constraints = self._extract_constraints(text)
        
        self.current_command = text
        
        return z_projection, constraints
    
    def update_from_gluing(self, 
                           glue_outcome: Dict, 
                           other_stalk_z: torch.Tensor):
        """
        Learn from gluing outcome (endogenous supervision).
        REINFORCE-style update without backprop through physics.
        """
        if glue_outcome["success"]:
            reward = self._calculate_glue_reward(glue_outcome)
            self._reinforce_projection(reward, other_stalk_z)
            self._update_invariants_from_success(glue_outcome)
        else:
            penalty = -self._calculate_failure_penalty(glue_outcome)
            self._penalize_projection(penalty, other_stalk_z)
            self._record_failure_pattern(glue_outcome)
    
    def _reinforce_projection(self, reward: float, other_z: torch.Tensor):
        """REINFORCE        # Store eligibility-style update"""
        
 trace
        trace_key = f"trace_{hash(other_z.cpu().numpy().tobytes())}"
        if trace_key not in self.eligibility_trace:
            self.eligibility_trace[trace_key] = self._get_current_projection().detach()
        
        # Update with delayed reward
        projection_at_time = self.eligibility_trace[trace_key]
        
        # Policy gradient update
        current_projection = self._get_current_projection()
        
        # Cosine similarity as policy
        similarity = torch.cosine_similarity(
            current_projection.unsqueeze(0), 
            projection_at_time.unsqueeze(0)
        ).squeeze()
        
        loss = -reward * similarity
        loss.backward()
        
        # Update projection head only
        optimizer = torch.optim.Adam(self.projection_head.parameters(), lr=1e-4)
        optimizer.step()
        optimizer.zero_grad()
        
        self.projection_updates += 1
        
        # Clear old trace
        if trace_key in self.eligibility_trace:
            del self.eligibility_trace[trace_key]
    
    def _penalize_projection(self, penalty: float, other_z: torch.Tensor):
        """Penalize failed gluing"""
        self._reinforce_projection(penalty, other_z)
    
    def _get_current_projection(self) -> torch.Tensor:
        """Get current projection (requires grad for training)"""
        dummy = torch.randn(1, self.output_dim)
        return self.projection_head(dummy).squeeze()
    
    def _calculate_glue_reward(self, outcome: Dict) -> float:
        """Calculate reward from successful glue"""
        base = 1.0
        if outcome.get("reason") == "vision_match":
            base += 0.5
        return min(base, 1.0)
    
    def _calculate_failure_penalty(self, outcome: Dict) -> float:
        """Calculate penalty from failed glue"""
        return 0.5
    
    def _update_invariants_from_success(self, outcome: Dict):
        """Update learned invariants"""
        self.learned_invariants["glue_success"] = True
    
    def _record_failure_pattern(self, outcome: Dict):
        """Record failure for future avoidance"""
        reason = outcome.get("reason", "unknown")
        self.learned_invariants[f"failure_{reason}"] = True
    
    def _extract_constraints(self, text: str) -> Dict:
        """Extract physical constraints from language"""
        
        constraints = {
            "force_bounds": [0.0, 1.0],
            "velocity_bounds": [0.0, 1.0],
            "precision_required": 0.5,
            "safety_critical": False
        }
        
        # Keyword-based constraint extraction
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["gently", "careful", "soft", "fragile"]):
            constraints["force_bounds"] = [0.0, 0.3]
            constraints["safety_critical"] = True
        
        if any(w in text_lower for w in ["fast", "quick", "rapid"]):
            constraints["velocity_bounds"] = [0.5, 1.0]
        
        if any(w in text_lower for w in ["precise", "exact", "accurate"]):
            constraints["precision_required"] = 0.9
        
        return constraints
    
    def receive_command(self, command: str):
        """Receive and process command"""
        z, constraints = self.parse_and_project(command)
        self.current_z = z
        self.current_constraints = constraints
    
    def get_z_projection(self) -> torch.Tensor:
        """Get current Z projection"""
        if hasattr(self, 'current_z'):
            return self.current_z
        return torch.zeros(self.z_dim)


# === VISION STALK ===

class VisionStalk:
    """Vision stalk for perception"""
    
    def __init__(self, z_dim: int = 64):
        self.z_dim = z_dim
        self.current_features: Optional[torch.Tensor] = None
        self.current_constraints: Dict = {}
    
    def process(self, image) -> Tuple[torch.Tensor, Dict]:
        """Process image and extract features"""
        # Mock: random features
        features = torch.randn(self.z_dim)
        self.current_features = features
        
        constraints = {
            "spatial_bounds": [-1.0, 1.0],
            "confidence": 0.85
        }
        self.current_constraints = constraints
        
        return features, constraints
    
    def get_z_projection(self) -> torch.Tensor:
        return self.current_features or torch.zeros(self.z_dim)


# === MOTOR STALK ===

class MotorStalk:
    """Motor stalk for action execution"""
    
    def __init__(self, z_dim: int = 64):
        self.z_dim = z_dim
        self.current_state: Optional[Dict] = None
    
    def process_state(self, state: Dict) -> Tuple[torch.Tensor, Dict]:
        """Process proprioceptive state"""
        # Mock: encode state
        features = torch.randn(self.z_dim)
        
        constraints = {
            "joint_limits": [-np.pi, np.pi],
            "force_limits": [0.0, 1.0]
        }
        
        self.current_state = state
        return features, constraints
    
    def execute(self, action: Dict) -> bool:
        """Execute action"""
        print(f"  Executing: {action}")
        return True
    
    def get_z_projection(self) -> torch.Tensor:
        if self.current_state:
            return torch.randn(self.z_dim)
        return torch.zeros(self.z_dim)


# === PHYSICAL VERIFIER ===

class PhysicalVerifier:
    """
    Safety-critical physical verification.
    Runs only when lift is triggered (expensive).
    """
    
    def __init__(self):
        self.safety_margins = {
            "torque": 0.8,
            "velocity": 0.7,
            "collision": 0.05,
            "stability": 0.3
        }
        
        # Mock robot limits
        self.max_torque = np.array([1.0, 1.0, 1.0])
        self.max_velocity = np.array([1.0, 1.0, 1.0])
    
    async def check_torque_limits(self, action: Dict) -> bool:
        """Check torque limits with safety margin"""
        required = action.get("torque", np.array([0.5, 0.5, 0.5]))
        max_allowed = self.max_torque * self.safety_margins["torque"]
        
        return all(r <= m for r, m in zip(required, max_allowed))
    
    async def check_reachability(self, action: Dict) -> bool:
        """Check if target is reachable"""
        target = action.get("target_position")
        if target is None:
            return True
        
        # Mock: check if in bounds
        return all(-10 <= t <= 10 for t in target)
    
    async def check_collision(self, action: Dict) -> bool:
        """Collision checking"""
        trajectory = action.get("trajectory", [])
        
        for pose in trajectory:
            # Mock SDF check
            if np.random.random() < 0.01:  # 1% collision chance
                return False
        
        return True
    
    async def verify_action(self, action: Dict) -> Tuple[bool, str]:
        """Full physical verification"""
        checks = [
            (await self.check_torque_limits(action), "torque"),
            (await self.check_reachability(action), "reachability"),
            (await self.check_collision(action), "collision")
        ]
        
        for passed, name in checks:
            if not passed:
                return False, name
        
        return True, "all_passed"


# === CONFLICT ARBITRATOR ===

class ConflictArbitrator:
    """
    Choose between multiple physically viable actions.
    Multi-objective optimization.
    """
    
    def __init__(self):
        self.weights = {
            "energy": 0.4,
            "time": 0.3,
            "safety": 0.2,
            "precision": 0.1
        }
    
    def arbitrate(self, viable_actions: List[Dict]) -> Optional[Dict]:
        """Choose best action"""
        if not viable_actions:
            return None
        
        if len(viable_actions) == 1:
            return viable_actions[0]
        
        scores = []
        for action in viable_actions:
            score = (
                -action.get("energy_estimate", 0.5) * self.weights["energy"] +
                -action.get("time_estimate", 0.5) * self.weights["time"] +
                action.get("safety_margin", 0.5) * self.weights["safety"] +
                action.get("precision", 0.5) * self.weights["precision"]
            )
            scores.append((score, action))
        
        best = max(scores, key=lambda x: x[0])
        return best[1]


# === ASYNC STALK CONTROLLER ===

class AsyncStalkController:
    """
    Asynchronous controller for stalk coordination.
    No central planner - only local gluing attempts.
    """
    
    def __init__(self):
        self.stalks: Dict[str, Any] = {}
        self.narrowed_frame: Optional[Dict] = None
        self.constraint_propagation = ConstraintPropagator()
        self.governor = Governor()
        self.physical_verifier = PhysicalVerifier()
        self.arbitrator = ConflictArbitrator()
        
        self.cycle_count = 0
    
    def add_stalk(self, stalk, name: str):
        """Add a stalk to the controller"""
        self.stalks[name] = stalk
        print(f"Added stalk: {name}")
    
    async def run_control_cycle(self):
        """Run one control cycle"""
        self.cycle_count += 1
        
        # 1. Attempt local glues
        glue_results = await self._attempt_local_glues()
        
        # 2. Propagate constraints
        self.narrowed_frame = self.constraint_propagation.propagate(
            self.stalks, glue_results
        )
        
        # 3. Check if should trigger lift
        if self._should_trigger_lift(self.narrowed_frame):
            physical_ok = await self._verify_physically(self.narrowed_frame)
            
            if physical_ok:
                await self._execute_action(self.narrowed_frame)
            else:
                await self._handle_physical_rejection(self.narrowed_frame)
        
        # Maintain real-time constraints
        await asyncio.sleep(0.001)
    
    async def _attempt_local_glues(self) -> Dict:
        """Attempt pairwise stalk gluing"""
        
        results = {"successful": [], "failed": []}
        
        # Language ↔ Vision
        lang = self.stalks.get("language")
        vision = self.stalks.get("vision")
        
        if lang and vision:
            can_glue, reason = self.governor.can_glue(lang, vision)
            
            if can_glue:
                try:
                    # Simulate glue success
                    success = True
                    results["successful"].append({
                        "stalks": ["language", "vision"],
                        "success": success,
                        "reason": "vision_match" if success else "failed"
                    })
                    
                    # Update language from gluing
                    lang.update_from_gluing(
                        {"success": success, "reason": "vision_match"},
                        vision.get_z_projection()
                    )
                except Exception as e:
                    results["failed"].append({"reason": str(e)})
        
        # Vision ↔ Motor
        motor = self.stalks.get("motor")
        
        if vision and motor:
            can_glue, reason = self.governor.can_glue(vision, motor)
            if can_glue:
                results["successful"].append({
                    "stalks": ["vision", "motor"],
                    "success": True
                })
        
        return results
    
    def _should_trigger_lift(self, frame: Dict) -> bool:
        """Trigger expensive recovery/lift only when necessary"""
        
        if frame is None:
            return False
        
        # Check if we have required stalks
        stalk_types = list(self.stalks.keys())
        required = {"language", "vision", "motor"}
        
        if not required.issubset(set(stalk_types)):
            return False
        
        # Check action candidates
        actions = frame.get("action_candidates", [])
        if len(actions) > 10:
            return False
        
        # Check spatial uncertainty
        uncertainty = frame.get("spatial_uncertainty", 1.0)
        if uncertainty > 0.3:
            return False
        
        return True
    
    async def _verify_physically(self, frame: Dict) -> bool:
        """Physical verification"""
        
        actions = frame.get("action_candidates", [])
        
        viable = []
        for action in actions:
            passed, reason = await self.physical_verifier.verify_action(action)
            if passed:
                viable.append(action)
        
        # Arbitrate if multiple viable
        if len(viable) > 1:
            best = self.arbitrator.arbitrate(viable)
            viable = [best] if best else []
        
        frame["viable_actions"] = viable
        
        return len(viable) > 0
    
    async def _execute_action(self, frame: Dict):
        """Execute selected action"""
        viable = frame.get("viable_actions", [])
        
        if viable:
            action = viable[0]
            motor = self.stalks.get("motor")
            if motor:
                motor.execute(action)
    
    async def _handle_physical_rejection(self, frame: Dict):
        """Handle physical rejection"""
        print(f"  Physical rejection - constraints too tight")


# === CONSTRAINT PROPAGATOR ===

class ConstraintPropagator:
    """Propagate constraints through gluing"""
    
    def __init__(self):
        self.narrowed_frame: Optional[Dict] = None
    
    def propagate(self, stalks: Dict, glue_results: Dict) -> Dict:
        """Propagate constraints from stalks through glues"""
        
        frame = {
            "action_candidates": self._generate_action_candidates(stalks),
            "spatial_uncertainty": self._calculate_uncertainty(stalks),
            "semantic_ambiguity": self._calculate_ambiguity(stalks),
            "stalk_types": list(stalks.keys())
        }
        
        # Propagate force bounds through glues
        frame = self._propagate_force_bounds(frame, glue_results)
        
        self.narrowed_frame = frame
        return frame
    
    def _generate_action_candidates(self, stalks: Dict) -> List[Dict]:
        """Generate action candidates from constraints"""
        
        candidates = []
        
        # Get language constraints
        lang = stalks.get("language")
        if lang and hasattr(lang, 'current_constraints'):
            constraints = lang.current_constraints
            
            # Generate candidate based on constraints
            for force in np.linspace(
                constraints.get("force_bounds", [0, 1])[0],
                constraints.get("force_bounds", [0, 1])[1],
                3
            ):
                candidates.append({
                    "force": force,
                    "velocity": 0.5,
                    "target_position": [0.5, 0.5, 0.0],
                    "trajectory": [[0, 0, 0], [0.5, 0.5, 0.0]],
                    "energy_estimate": force * 0.5,
                    "time_estimate": 1.0,
                    "safety_margin": 0.8,
                    "precision": constraints.get("precision_required", 0.5)
                })
        
        # Default candidates if no language
        if not candidates:
            candidates = [
                {"force": 0.5, "velocity": 0.5, "target_position": [0, 0, 0],
                 "energy_estimate": 0.5, "time_estimate": 1.0, "safety_margin": 0.8, "precision": 0.5}
            ]
        
        return candidates
    
    def _calculate_uncertainty(self, stalks: Dict) -> float:
        """Calculate spatial uncertainty"""
        # Simplified: higher uncertainty without vision
        if "vision" in stalks:
            return 0.15
        return 0.8
    
    def _calculate_ambiguity(self, stalks: Dict) -> float:
        """Calculate semantic ambiguity"""
        if "language" in stalks:
            return 0.2
        return 0.5
    
    def _propagate_force_bounds(self, frame: Dict, glue: Dict) -> Dict:
        """Propagate force constraints through system"""
        
        # Simplified: just pass through
        return frame


# === GOVERNOR ===

class Governor:
    """Decision gate for gluing"""
    
    def can_glue(self, stalk_a, stalk_b) -> Tuple[bool, str]:
        """Check if two stalks can glue"""
        
        # Simplified: always allow
        return True, "approved"


# === USAGE EXAMPLE ===

async def test_complete_system():
    """Test the integrated sheaf-theoretic control system"""
    
    print("=== Language Stalk + Robot Control Demo ===\n")
    
    # 1. Initialize system
    controller = AsyncStalkController()
    
    # 2. Add stalks
    controller.add_stalk(LanguageStalk(z_dim=64), "language")
    controller.add_stalk(VisionStalk(z_dim=64), "vision")
    controller.add_stalk(MotorStalk(z_dim=64), "motor")
    
    # 3. Send command
    print("\n--- Sending Command ---")
    controller.stalks["language"].receive_command("Pick up the red cup gently")
    print(f"Constraints: {controller.stalks['language'].current_constraints}")
    
    # 4. Process vision
    controller.stalks["vision"].process(None)
    
    # 5. Run control cycles
    print("\n--- Running Control Cycles ---")
    for i in range(3):
        await controller.run_control_cycle()
        
        if controller.narrowed_frame:
            frame = controller.narrowed_frame
            print(f"Cycle {i}: Actions={len(frame.get('action_candidates', []))}, "
                  f"Uncertainty={frame.get('spatial_uncertainty', 0):.2f}")
    
    # 6. Check learning
    lang = controller.stalks["language"]
    print(f"\n--- Language Stalk Learning ---")
    print(f"  Projection updates: {lang.projection_updates}")
    print(f"  Learned invariants: {lang.learned_invariants}")
    
    # 7. Test physical verifier
    print("\n--- Physical Verification ---")
    verifier = PhysicalVerifier()
    test_action = {
        "torque": np.array([0.3, 0.3, 0.3]),
        "target_position": [0.5, 0.5, 0.0],
        "trajectory": [[0,0,0], [0.5, 0.5, 0.0]]
    }
    passed, reason = await verifier.verify_action(test_action)
    print(f"  Action verified: {passed} ({reason})")
    
    # 8. Test conflict arbitrator
    print("\n--- Conflict Arbitration ---")
    arbitrator = ConflictArbitrator()
    actions = [
        {"energy_estimate": 0.3, "time_estimate": 0.5, "safety_margin": 0.9, "precision": 0.7},
        {"energy_estimate": 0.5, "time_estimate": 0.3, "safety_margin": 0.7, "precision": 0.8},
    ]
    best = arbitrator.arbitrate(actions)
    print(f"  Best action: energy={best['energy_estimate']}, time={best['time_estimate']}")
    
    print("\n=== Demo Complete ===")


if __name__ == '__main__':
    asyncio.run(test_complete_system())
