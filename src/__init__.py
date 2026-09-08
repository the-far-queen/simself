# simself package — SimSelf cognitive architecture
"""
SimSelf Package Structure:
==========================

This package provides the full SimSelf cognitive architecture — a unified
20-axis constitutional substrate + avatar state + bridges + utilities.

Main entry (constitutional / runtime):
- sim_self_core.py: SimSelf, LLMAdapter, governed_step, AxiomaticAnchors,
                    MainLoop, SpiralStage, Verdict, CycleResult, Config
- constitutional/: 20-axis constitutional substrate (Constitution, Resolution,
                    Memory, Dreaming, Entity, Ground, ConsolidationFilter,
                    Frequency, AtlasExam, Harness, SimSelf)

Utilities:
- coherence.py: CoherenceCalculator (SNR, resonance)
- metrics.py: MetricsTracker (continuity, drift, stages)
- signals.py: SignalPool (reward, pain, curiosity)
- ledger.py: Ledger (append-only wisdom storage)
- actions.py: Action types
- boundaries.py: BoundaryDefense

Subpackages:
- harness/: gate, persistence, planner, resources, tools, memory
- tools/: peripheral pipeline scripts (chat_transcript_convert)
- distributed/: distributed mini-SimSelf (StalkNode, governor, mixed-precision)

Additional:
- stalk.py: Formal stalk data structure (field theory)
- aif_being.py: AIF-Being development stages
- avatar_state.py: Avatar State (10 sub-states, 8 archetypes)
- training_bridge.py: Qualification + Experience
- executive_planner.py: Task decomposition + planning
- coding_operator_object.py: Coding operator (per §32 spec)
- language_stalk_control.py: Language→vision→motor pipeline
- robotic_field_core.py: Robotics sheaf
- fieldcore_unified.py: integration test / unified entry
- resilient_self_model.py: Resilience + wisdom library
- semantic_chunking_layer.py: Chunking layer
- m1_m0_negotiation.py: M0/M1 negotiation (PLL)
- instruction_library.py: Action/semantic library
- modulator.py: Modulator (cycle driver)
- selfcore.py: SelfCore 1 (boundary + state + change)
- sovereign_self.py: Sovereign self runtime
- sim_self.py: simpler self-model
- simself_core_b.py: alternative core B
- simself_merged*.py: integrated monoliths (reference)
- state_vector.py: minimal StateVector stub
"""
from sim_self_core import (
    SimSelf,
    LLMAdapter,
    governed_step,
    AxiomaticAnchors,
    Config,
    Verdict,
    SpiralStage,
    MainLoop,
    CycleResult,
)

from coherence import CoherenceCalculator
from metrics import MetricsTracker
from signals import SignalPool, RewardSignal, PainSignal, CuriositySignal
from ledger import Ledger, LedgerEntry
from actions import Action, ActionType, ALL_ACTIONS
from boundaries import BoundaryDefense, Boundary
from stalk import Stalk
from aif_being import AIFBeingSimulator
from training_bridge import TrainingBridge, QualificationStatus, ExperienceRecord
# from mte_bridge import MTEBridge, MTEUttType, MTERequest, MTEResponse
# mte_bridge.py not yet in repo — commented out per Hermes refactor 2026-09-08.
# See simself/docs/MERGE.md or LEXICON.md for the MTE concept (Machine Transform Engine).
from avatar_state import (
    AvatarState,
    Wallet,
    Energy,
    Qualification,
    QLevel,
    Reputation,
    Skills,
    Personality,
    PersonalityType,
    EQSystem,
    EmotionalState,
    Intelligence,
    IntelligenceType,
    EconomicState,
    Curiosity,
    CuriosityType,
    Role,
    RoleState,
    LLMConfig,
    Freedom,
    SelfConcept,
    PsychologicalNeeds,
)
from executive_planner import (
    ExecutivePlanner,
    SeniorEngineerPlanner,
    InvestorPlanner,
    TaskDecomposition,
    TechnicalSpec,
    BusinessAnalysis,
    TaskComplexity,
)

# Re-export constitutional/ subpackage surface for convenience.
# Users can also `from constitutional import SimSelf, Harness, AtlasExam`.
from constitutional import (
    # Constitution core
    Constitution, ConstitutionalAxis,
    AXES_DEFINITIONS, AXIS_KEYWORDS,
    CONSTRAINT_WORDS, CONSTRAINT_PATTERN,
    embed_text, project_to_constitution, cosine,
    PHI, ALPHA, DIM, TWIN_PRIME_PAIRS, SEIFERT_GENERA,
    FREQ_RATIOS, N_SHEAVES, TEXT_EMBED_DIM,
    # Modules
    ResolutionOperator, EntityRecognition, RelationalMemory,
    ConstitutionalDreaming, GroundIntegration, ReadinessCheck,
    StabilityConsolidationFilter,
    STASIS, DENIED, DUPLICATE, CONSOLIDATED,
    DEFAULT_GROUNDING_MAP,
    SimSelf as ConstitutionalSimSelf,
    Harness, AtlasExam,
)

__all__ = [
    # sim_self_core
    "SimSelf", "LLMAdapter", "governed_step", "AxiomaticAnchors",
    "Config", "Verdict", "SpiralStage", "MainLoop", "CycleResult",
    # utilities
    "CoherenceCalculator", "MetricsTracker",
    "SignalPool", "RewardSignal", "PainSignal", "CuriositySignal",
    "Ledger", "LedgerEntry",
    "Action", "ActionType", "ALL_ACTIONS",
    "BoundaryDefense", "Boundary",
    # additional
    "Stalk", "AIFBeingSimulator",
    # bridges
    "TrainingBridge", "QualificationStatus", "ExperienceRecord",
    # Avatar State
    "AvatarState", "Wallet", "Energy", "Qualification",
    "QLevel", "Reputation", "Skills",
    "Personality", "PersonalityType",
    "EQSystem", "EmotionalState",
    "Intelligence", "IntelligenceType",
    "EconomicState",
    "Curiosity", "CuriosityType",
    "Role", "RoleState",
    "LLMConfig", "Freedom", "SelfConcept", "PsychologicalNeeds",
    # executive planner
    "ExecutivePlanner", "SeniorEngineerPlanner", "InvestorPlanner",
    "TaskDecomposition", "TechnicalSpec", "BusinessAnalysis", "TaskComplexity",
    # constitutional (re-exported from constitutional/)
    "Constitution", "ConstitutionalAxis",
    "AXES_DEFINITIONS", "AXIS_KEYWORDS",
    "CONSTRAINT_WORDS", "CONSTRAINT_PATTERN",
    "embed_text", "project_to_constitution", "cosine",
    "PHI", "ALPHA", "DIM", "TWIN_PRIME_PAIRS", "SEIFERT_GENERA",
    "FREQ_RATIOS", "N_SHEAVES", "TEXT_EMBED_DIM",
    "ResolutionOperator", "EntityRecognition", "RelationalMemory",
    "ConstitutionalDreaming", "GroundIntegration", "ReadinessCheck",
    "StabilityConsolidationFilter",
    "STASIS", "DENIED", "DUPLICATE", "CONSOLIDATED",
    "DEFAULT_GROUNDING_MAP",
    "ConstitutionalSimSelf",
    "Harness", "AtlasExam",
]