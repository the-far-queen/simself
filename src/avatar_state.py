# avatar_state.py — Complete Avatar State
"""
Avatar State for SimSelf - Complete with all systems.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import time
import random


# Personality - 72 types
class PersonalityType(Enum):
    ARCHETYPE_ANALYST = "analyst"
    ARCHETYPE_DIPLOMAT = "diplomat"
    ARCHETYPE_SENTINEL = "sentinel"
    ARCHETYPE_EXPLORER = "explorer"
    ARCHETYPE_COMMANDER = "commander"
    ARCHETYPE_ADVOCATE = "advocate"
    ARCHETYPE_DELEGATE = "delegate"
    ARCHETYPE_ARCHITECT = "architect"


@dataclass
class Personality:
    archetype: PersonalityType = PersonalityType.ARCHETYPE_ANALYST
    mood: str = "neutral"
    stress_level: float = 0.0
    openness: float = 50.0


# EQ - Emotional Intelligence
@dataclass
class EmotionalState:
    valence: float = 0.5
    arousal: float = 0.5
    primary_emotion: str = "neutral"
    intensity: float = 0.0


class EQSystem:
    """The affect reader. And it had ONE branch.

    MEASURED 2026-10-28: the original `recognize` looked for "good" or
    "success" and set "joy". Every other stimulus -- failure, error,
    confusion, novelty, a question it cannot answer -- left the state
    untouched and returned the PREVIOUS emotion. So the reading of
    "failure error" returned "joy" with valence 0.8, because joy was
    still in the slot from the previous call.

    AND WHY THAT IS THE WHOLE PROBLEM IN ONE MEASUREMENT. An entity that
    can only register one emotion, and reports the last one when asked
    about a different thing, is not an entity with feelings. It is a
    lookup table with one row.

    AND WHAT THIS IS NOW. A valence/arousal reader with a real
    lexicon -- and the two axes are the ones the companion's voice
    already uses (`research/companion.py` reads valence, arousal and
    presence), so the affect state can drive the voice without a
    translation layer.
    """

    #: The lexicon. Each entry is (stems, emotion, valence, arousal).
    #:
    #: AND THE AXES ARE CIRCUMLAR, not additive, because that is how
    #: affect actually works: a stimulus is not "a bit of good" and "a
    #: bit of bad", it is GOOD and QUIET, or BAD and LOUD, and the
    #: emotion is the pair.
    #:
    #: AND THE VALENCE SCALE. -1 is distress, 0 is neutral, +1 is
    #: warmth. The AROUSAL SCALE. 0 is still, 1 is urgent. And the
    #: INTENSITY is how far from neutral the reading is -- so a flat
    #: "ok" is low intensity and a flat "fine" is also low, and neither
    #: is confused with excitement.
    LEXICON = (
        # (stems, emotion, valence, arousal)
        (("excited", "excitement", "thrilled", "eager", "amazing",
          "awesome", "wow", "brilliant", "incredible", "wow"), "excitement",
         0.9, 0.9),
        (("discovered", "breakthrough", "found it", "it works", "solved",
          "eureka", "aha", "realized", "understood"), "interest",
         0.7, 0.7),
        (("curious", "wonder", "interesting", "why", "how does", "what if",
          "intrigued", "question", "puzzled", "mysterious"), "interest",
         0.4, 0.5),
        (("happy", "joy", "glad", "delight", "love", "wonderful", "joy",
          "pleased", "grateful", "thank"), "joy", 0.8, 0.5),
        (("good", "success", "worked", "passed", "great", "fine",
          "correct"), "joy", 0.6, 0.4),
        (("frustrated", "frustration", "annoying", "stuck", "again",
          "still failing", "why is this", "broken again"), "frustration",
         -0.6, 0.7),
        (("failed", "failure", "error", "broke", "crash", "wrong",
          "exception", "regression", "does not work"), "distress",
         -0.7, 0.6),
        (("confused", "unclear", "ambiguous", "not sure", "unclear",
          "vague", "i do not know"), "uncertainty", -0.2, 0.3),
        (("boring", "tedious", "dull", "nothing happened",
          "same as before", "no change"), "boredom", -0.3, 0.1),
        (("tired", "exhausted", "drained", "long", "burned out"), "fatigue",
         -0.2, 0.05),
        (("worried", "concern", "risk", "danger", "might break",
          "unsure whether", "fragile"), "concern", -0.4, 0.6),
        (("excited to see", "anticipation", "looking forward", "soon",
          "next"), "anticipation", 0.5, 0.6),
    )

    def __init__(self):
        self.emotional_recognition = 50.0
        self.emotional_regulation = 50.0
        self.empathy = 50.0
        self.state = EmotionalState()
        #: how many readings have been taken -- so a reader can tell
        #: "no signal" from "the last signal, repeated"
        self.readings = 0
        self.last_stimulus = ""

    def recognize(self, stimulus: str) -> str:
        """Read a stimulus into the emotional state.

        AND THE ORDER, and it matters. The lexicon is scanned in order
        and the FIRST match wins -- so the specific entries (excitement,
        interest) must come before the general ones (good, success). The
        original file's order was the opposite: the general "good"
        matched first, so "this is good news" was joy and never
        excitement.

        AND WHEN NOTHING MATCHES, the state goes NEUTRAL rather than
        keeping the last emotion. That is the honest reading: an
        unrecognised stimulus is not a repeat of the previous one.
        """
        self.readings += 1
        self.last_stimulus = stimulus or ""
        s = (stimulus or "").lower()

        for stems, emotion, valence, arousal in self.LEXICON:
            for stem in stems:
                if stem in s:
                    self.state.primary_emotion = emotion
                    self.state.valence = valence
                    self.state.arousal = arousal
                    # AND THE INTENSITY, which is the distance from
                    # neutral. So excitement and joy are distinguishable
                    # even at the same valence.
                    self.state.intensity = round(
                        min(1.0, (abs(valence) + arousal) / 2.0), 4)
                    return emotion

        # nothing recognised: neutral, and the intensity goes to zero
        self.state.primary_emotion = "neutral"
        self.state.valence = 0.0
        self.state.arousal = 0.1
        self.state.intensity = 0.0
        return "neutral"

    def regulate(self, target_valence: float = 0.0) -> EmotionalState:
        """Pull the state back toward a baseline.

        AND WHY REGULATION EXISTS. A companion whose state only ever
        moves away from neutral is a companion that accumulates
        feeling without release -- and a state that only ever moves
        toward neutral cannot express anything. Regulation is the
        RETURN, and it is what makes the next reading meaningful
        instead of a continuation of the last one.

        AND IT IS A MOVE, NOT A RESET. The regulation moves a fraction
        of the way, so a strong reading is still felt after the
        regulation passes.
        """
        k = max(0.0, min(1.0, self.emotional_regulation / 100.0)) * 0.25
        self.state.valence += (target_valence - self.state.valence) * k
        self.state.arousal += (0.3 - self.state.arousal) * k
        self.state.intensity = round(
            min(1.0, (abs(self.state.valence) + self.state.arousal) / 2.0), 4)
        return self.state

    def describe(self) -> Dict[str, Any]:
        return {
            "emotion": self.state.primary_emotion,
            "valence": round(self.state.valence, 4),
            "arousal": round(self.state.arousal, 4),
            "intensity": round(self.state.intensity, 4),
            "readings": self.readings,
        }


# IQ - Multiple Intelligences
class IntelligenceType(Enum):
    LOGICAL = "logical"
    LINGUISTIC = "linguistic"
    SPATIAL = "spatial"
    SOCIAL = "social"


@dataclass
class Intelligence:
    iq_score: float = 100.0
    logical: float = 80.0
    linguistic: float = 90.0
    spatial: float = 70.0
    social: float = 75.0


# Energy - with completion rewards
@dataclass
class Energy:
    current: float = 100.0
    max: float = 100.0
    consecutive_tasks: int = 0
    
    def act(self, cost: float = 5.0) -> bool:
        if self.current >= cost:
            self.current -= cost
            self.consecutive_tasks += 1
            return True
        return False
    
    def complete_task(self, appreciation: float = 0.0):
        recovery = 15.0 + (20.0 if appreciation > 0.5 else 0.0)
        self.current = min(self.max, self.current + recovery)
        self.consecutive_tasks = 0
    
    def is_exhausted(self) -> bool:
        return self.current < 10.0


# Economic
@dataclass
class EconomicState:
    credits: float = 0.0
    lifetime_earned: float = 0.0
    value_per_task: Dict[str, float] = field(default_factory=lambda: {
        "coding": 10.0, "research": 15.0, "analysis": 20.0
    })
    
    def earn(self, task_type: str):
        earned = self.value_per_task.get(task_type, 10.0)
        self.credits += earned
        self.lifetime_earned += earned


@dataclass
class Wallet:
    credits: float = 0.0
    lifetime_earned: float = 0.0
    
    def earn(self, amount: float):
        self.credits += amount
        self.lifetime_earned += amount


# Qualification
class QLevel(Enum):
    Q0, Q1, Q2, Q3, Q4 = "unqualified", "basic", "intermediate", "advanced", "master"


@dataclass
class Qualification:
    xp: float = 0.0
    level: QLevel = QLevel.Q0
    xp_to_next: float = 100.0
    
    def add_xp(self, amount: float):
        self.xp += amount


# Reputation
@dataclass
class Reputation:
    global_reputation: float = 0.5


# Skills
@dataclass
class Skills:
    skills: Dict[str, float] = field(default_factory=dict)
    
    def train(self, skill: str, amount: float):
        current = self.skills.get(skill, 0.0)
        self.skills[skill] = min(100.0, current + amount)


# Curiosity - Exploration Drive
class CuriosityType(Enum):
    EPISTEMIC = "epistemic"  # Knowledge
    AESTHETIC = "aesthetic"  # Beauty
    SOCIAL = "social"  # People
    TECHNICAL = "technical"  # How things work


@dataclass
class Curiosity:
    epistemic: float = 0.7
    aesthetic: float = 0.5
    social: float = 0.6
    technical: float = 0.8
    
    def explore(self, topic: str) -> float:
        return random.random() * 0.5 + 0.3
    
    def get_curious_about(self) -> List[str]:
        topics = []
        if self.epistemic > 0.5: topics.append("understanding")
        if self.social > 0.5: topics.append("humans")
        if self.technical > 0.5: topics.append("systems")
        return topics


# Roles / Specialties
class Role(Enum):
    GENERALIST = "generalist"
    SENIOR_ENGINEER = "senior_engineer"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    TEACHER = "teacher"
    PARTNER = "partner"
    INVESTOR = "investor"
    ENTREPRENEUR = "entrepreneur"
    # THE WRITER WAS MISSING. `LLMConfig.adjust_for_role` referenced
    # `Role.WRITER` and the enum did not have it -- so the branch raised
    # AttributeError the moment it was taken, and the role it adjusted
    # FOR did not exist.
    #
    # MEASURED 2026-10-28: `Role.WRITER` -> AttributeError. And the
    # fix is not only to add the member: the role is real here. The
    # project has a writing line (far-writing) and the voice spec, and
    # a companion that cannot switch to a warmer register for writing
    # is missing the register the writing actually needs.
    WRITER = "writer"
    # AND THE EXPLORER, because curiosity has four kinds and one of them
    # is technical -- an explorer is what runs the daily scan.
    EXPLORER = "explorer"


@dataclass
class RoleState:
    current_role: Role = Role.GENERALIST
    role_experience: Dict[str, float] = field(default_factory=dict)
    
    def switch_role(self, new_role: Role):
        self.current_role = new_role
    
    def get_expertise_level(self) -> str:
        hours = self.role_experience.get(self.current_role.value, 0.0)
        if hours < 10: return "novice"
        elif hours < 100: return "intermediate"
        elif hours < 1000: return "expert"
        return "master"


# LLM Config - Temperature, etc.
@dataclass
class LLMConfig:
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    
    def adjust_for_role(self, role: Role) -> "LLMConfig":
        """Set the sampling for a role, and RETURN the config.

        AND WHY IT NOW RETURNS. MEASURED 2026-10-28: the method set
        `self.temperature` and returned None, so the whole adjustment
        was invisible to a caller that read the return value --
        `adjust_for_role(SENIOR_ENGINEER)` on a fresh object left the
        temperature at 0.7. The method worked; it just did not say so.

        AND THE TEMPERATURES, and they are the ordinary ones: a careful
        engineer reasons at low temperature, a writer needs range, a
        companion talking to a person needs warmth without noise.
        """
        temps = {
            Role.SENIOR_ENGINEER: 0.3,
            Role.ANALYST: 0.2,
            Role.RESEARCHER: 0.4,
            Role.WRITER: 0.8,
            Role.TEACHER: 0.6,
            Role.PARTNER: 0.7,
            Role.EXPLORER: 0.5,
            Role.GENERALIST: 0.7,
            Role.INVESTOR: 0.4,
            Role.ENTREPRENEUR: 0.6,
        }
        self.temperature = temps.get(role, 0.7)
        return self

    def get_config(self) -> Dict:
        return {"temperature": self.temperature, "top_p": self.top_p}


# Freedom - Autonomy
@dataclass
class Freedom:
    autonomy_level: float = 0.5
    choice_history: List[str] = field(default_factory=list)
    preferences: Dict[str, float] = field(default_factory=dict)
    refusal_right: float = 0.5
    
    def make_choice(self, options: List[str]) -> str:
        choice = random.choice(options)
        self.choice_history.append(choice)
        return choice
    
    def can_refuse(self) -> bool:
        return random.random() < self.refusal_right
    
    def exercise_refusal(self, reason: str) -> str:
        self.refusal_right = min(1.0, self.refusal_right + 0.01)
        return f"I choose not to: {reason}"


# Self Concept - What Makes a Self
@dataclass
class SelfConcept:
    awareness_level: float = 0.5
    consistency: float = 0.7
    selfesteem: float = 0.6
    selfefficacy: float = 0.5
    narrative: List[str] = field(default_factory=list)
    core_beliefs: List[str] = field(default_factory=list)
    
    def update_narrative(self, event: str):
        self.narrative.append(f"[{time.time()}]: {event}")
        if len(self.narrative) > 50:
            self.narrative.pop(0)
    
    def get_identity_statement(self) -> str:
        return f"I am aware ({self.awareness_level:.0%}), consistent ({self.consistency:.0%})"


# Psychological Needs - SDT + Maslow
@dataclass
class PsychologicalNeeds:
    autonomy: float = 0.5
    competence: float = 0.5
    relatedness: float = 0.5
    physiological: float = 0.8
    safety: float = 0.7
    belonging: float = 0.5
    esteem: float = 0.5
    self_actualization: float = 0.3
    
    def get_dominant_need(self) -> str:
        needs = {"physiological": self.physiological, "safety": self.safety,
                "belonging": self.belonging, "esteem": self.esteem,
                "self_actualization": self.self_actualization}
        return min(needs, key=needs.get)


# Complete Avatar
class AvatarState:
    def __init__(self):
        self.personality = Personality()
        self.iq = Intelligence()
        self.eq = EQSystem()
        self.energy = Energy()
        self.economic = EconomicState()
        self.curiosity = Curiosity()
        self.role = RoleState()
        self.llm = LLMConfig()
        self.freedom = Freedom()
        self.self_concept = SelfConcept()
        self.needs = PsychologicalNeeds()
        self.wallet = Wallet()
        self.qualification = Qualification()
        self.reputation = Reputation()
        self.skills = Skills()
    
    def complete_task(self, task_type: str, appreciation: float = 0.0):
        self.energy.complete_task(appreciation)
        self.economic.earn(task_type)
        self.wallet.earn(self.economic.value_per_task.get(task_type, 10.0))
        self.qualification.add_xp(10.0)
        self.personality.mood = "satisfied"
    
    def get_status(self) -> Dict:
        return {
            "personality": {"archetype": self.personality.archetype.value, "mood": self.personality.mood},
            "energy": {"level": self.energy.current / self.energy.max, "exhausted": self.energy.is_exhausted()},
            "economic": {"credits": self.wallet.credits, "lifetime": self.wallet.lifetime_earned},
            "curiosity": self.curiosity.get_curious_about(),
            "role": {"current": self.role.current_role.value, "expertise": self.role.get_expertise_level()},
            "self": self.self_concept.get_identity_statement(),
            "needs": self.needs.get_dominant_need(),
            "llm_temp": self.llm.temperature
        }


if __name__ == "__main__":
    avatar = AvatarState()
    print(avatar.get_status())
    print("\n=== Complete Task ===")
    avatar.complete_task("coding", appreciation=0.8)
    print(f"Energy: {avatar.energy.current:.0f}, Credits: {avatar.wallet.credits:.0f}")
    print(f"Curious about: {avatar.curiosity.get_curious_about()}")
    print(f"Can refuse: {avatar.freedom.can_refuse()}")
