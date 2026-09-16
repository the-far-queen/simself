"""
constitutional — identity layer + governance + qualification exam.

Modules:
- constitution: Constitution, ConstitutionalAxis, embed_text, project_to_constitution.
- ground: write-protect API for ψ₀. One-shot install, versioned revisions.
- resolution: projected gradient step on F(ψ) = (1/2) ||ψ - ψ₀||².
- atlas_exam: 5-item qualification exam.
- simself: canonical SimSelf class.
- harness: harness loop.
- frequency: parallel state. ψ untouched.
- psb_primitives: 6 types, coverage().
- adversarial: 21 protocol stubs.
- axes_v2: legacy 20-axis module (functional, not algebra-derived).
- memory: store of constitutional memory items.
- geometric_memory: geometric addressing.
- consolidation_filter / confabulation_filter: gating helpers.
- operators: identity operators (project_ball, step, commit_radius).
- mini_llm: stub (per the project-scope).
- temporal_control: phase 1 stub.
- lexicon.ingest: language intake. Same gate as kernel + harness.
"""

from .constitution import (
    Constitution,
    ConstitutionalAxis,
    DEFAULT_AXES,
    embed_text,
    project_to_constitution,
)
from .ground import Ground
from .coherence import CoherenceScore, check_coherence, cross_axis_coherence
from .sacred_library import SacredLibraryManager
from .boot_sequence import cold_boot
from .resolution import project_ball, step, resolve
from .atlas_exam import AtlasExam
from .simself import SimSelf
from .harness import Harness
from .frequency import FrequencyCoupler, PARAMS
from .psb_primitives import (
    UnitType,
    PRIM,
    classify_span,
    coverage,
    embed_bag,
)
from .adversarial import (
    ProtocolResult,
    run_protocol,
    PROTOCOL_STUBS,
)
from .axes_v2 import AxesV2
from .memory import ConstitutionalMemory, MemoryItem
from .geometric_memory import GeometricMemory, MemoryPacket
from .consolidation_filter import should_consolidate, DEFAULT_COMMIT_RADIUS
from .confabulation_filter import is_confabulation
from .operators import (
    project_ball as op_project_ball,
    step as op_step,
    commit_radius as op_commit_radius,
    is_within_commit_radius,
    DEFAULT_R as OP_DEFAULT_R,
    DEFAULT_ETA as OP_DEFAULT_ETA,
    DEFAULT_COMMIT_RADIUS as OP_DEFAULT_COMMIT_RADIUS,
)
from .lexicon.ingest import (
    Unit, Verdict, Status,
    gate_m0, ingest, embed_bag as ingest_embed_bag,
)

__all__ = [
    "Constitution", "ConstitutionalAxis", "DEFAULT_AXES",
    "embed_text", "project_to_constitution",
    "Ground", "project_ball", "step", "resolve",
    "AtlasExam", "SimSelf", "Harness",
    "FrequencyCoupler", "PARAMS",
    "UnitType", "PRIM", "classify_span", "coverage",
    "ProtocolResult", "run_protocol", "PROTOCOL_STUBS",
    "AxesV2", "ConstitutionalMemory", "MemoryItem",
    "GeometricMemory", "MemoryPacket",
    "should_consolidate", "is_confabulation",
    "op_project_ball", "op_step", "op_commit_radius", "is_within_commit_radius",
    "OP_DEFAULT_R", "OP_DEFAULT_ETA", "OP_DEFAULT_COMMIT_RADIUS",
    "Unit", "Verdict", "Status", "gate_m0", "ingest", "ingest_embed_bag",
]
