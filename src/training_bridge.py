# training_bridge.py — Controller ↔ Library ↔ SimSelf Bridge
"""
Bridge: Controller-Library-SimSelf for Training and Qualification

Flow:
1. Controller evaluates experience/action
2. If approved → passes to training_bridge
3. training_bridge checks qualification
4. If qualified → gates addition to Library
5. SimSelf may incorporate new knowledge

NOTE (2026-03-07):
- Mini-LLM runtime: Always-on local fast reasoning, no external API delay
- Nested stalks: Stalks within stalks - hierarchical structure
- Atomic nodules: Granularized nodes within stalks
- Fail up: When sub-stalk fails, escalate to parent
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import time


class QualificationStatus(Enum):
    """Qualification result for experience."""
    QUALIFIED = "qualified"
    PENDING = "pending"
    UNQUALIFIED = "unqualified"


@dataclass
class ExperienceRecord:
    """Record of an experience for library."""
    id: str
    timestamp: float
    source: str  # "controller", "external", "simulation"
    content: Any
    tags: List[str] = field(default_factory=list)
    coherence_score: float = 0.0
    qualification: QualificationStatus = QualificationStatus.PENDING


class TrainingBridge:
    """
    Bridge between Controller, SimSelf, and Sacred Library.
    
    Responsibilities:
    - Receive approved experiences from Controller
    - Run qualification checks
    - Gate additions to Library
    - Update SimSelf with new knowledge
    """
    
    def __init__(self, simself=None, library=None, qualification_manager=None):
        self.simself = simself
        self.library = library
        self.qualification_manager = qualification_manager
        self.pending_experiences: List[ExperienceRecord] = []
        self.qualified_experiences: List[ExperienceRecord] = []
    
    def receive_experience(self, experience: Dict[str, Any], source: str = "controller") -> ExperienceRecord:
        """
        Receive experience from Controller.
        
        Args:
            experience: The experience data
            source: Source of experience ("controller", "external", "simulation")
            
        Returns:
            ExperienceRecord with pending qualification
        """
        record = ExperienceRecord(
            id=f"exp_{time.time()}",
            timestamp=time.time(),
            source=source,
            content=experience,
            tags=experience.get("tags", []),
            coherence_score=experience.get("coherence", 0.0),
            qualification=QualificationStatus.PENDING
        )
        
        self.pending_experiences.append(record)
        return record
    
    def qualify_experience(self, record: ExperienceRecord) -> QualificationStatus:
        """
        Qualify an experience record.
        
        Args:
            record: The experience to qualify
            
        Returns:
            QualificationStatus
        """
        # Run qualification checks
        if self.qualification_manager:
            # Would run actual qualification logic
            # For now: simple coherence threshold
            if record.coherence_score >= 0.7:
                record.qualification = QualificationStatus.QUALIFIED
            else:
                record.qualification = QualificationStatus.UNQUALIFIED
        else:
            # Default: qualify if coherence > 0.5
            if record.coherence_score >= 0.5:
                record.qualification = QualificationStatus.QUALIFIED
            else:
                record.qualification = QualificationStatus.UNQUALIFIED
        
        return record.qualification
    
    def process_pending(self) -> List[ExperienceRecord]:
        """
        Process all pending experiences.
        
        Returns:
            List of qualified experiences added to library
        """
        added = []
        
        for record in self.pending_experiences:
            if record.qualification == QualificationStatus.PENDING:
                self.qualify_experience(record)
            
            if record.qualification == QualificationStatus.QUALIFIED:
                # Add to library
                if self.library:
                    self.library.add(
                        entry_type="experience",
                        content=record.content,
                        metadata={
                            "source": record.source,
                            "coherence": record.coherence_score,
                            "tags": record.tags
                        }
                    )
                
                # Update SimSelf if present
                if self.simself:
                    # SimSelf might incorporate new knowledge
                    pass
                
                self.qualified_experiences.append(record)
                added.append(record)
        
        # Clear processed
        self.pending_experiences = [
            r for r in self.pending_experiences 
            if r.qualification == QualificationStatus.PENDING
        ]
        
        return added
    
    def get_qualified_count(self) -> int:
        """Get count of qualified experiences."""
        return len(self.qualified_experiences)


# Example usage
if __name__ == "__main__":
    bridge = TrainingBridge()
    
    # Receive experiences from controller
    exp1 = bridge.receive_experience({
        "action": "grasp",
        "result": "success",
        "coherence": 0.85,
        "tags": ["robotics", "success"]
    }, source="controller")
    
    exp2 = bridge.receive_experience({
        "action": "fail_test",
        "result": "failed",
        "coherence": 0.3,
        "tags": ["robotics"]
    }, source="simulation")
    
    # Process and qualify
    added = bridge.process_pending()
    
    print("Training Bridge Test")
    print(f"Added to library: {len(added)}")
    for a in added:
        print(f"  - {a.id}: {a.qualification.value}")
