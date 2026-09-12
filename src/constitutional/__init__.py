"""
constitutional — The 20-axis constitutional core, modular.

Source: `grok-self.txt` (56 KB, single file, 1258 lines) pasted by Bobby
on 2026-08-08. Original author: Grok. M3 split into per-concern modules
per the "SimSelf as wardrobe" principle in FieldCore.md §3.

Public surface (re-exported below):
- Constitution, ConstitutionalAxis, AXES_DEFINITIONS, CONSTRAINT_WORDS
- embed_text, project_to_constitution, cosine, PHI, ALPHA, DIM
- ResolutionOperator
- EntityRecognition
- RelationalMemory
- ConstitutionalDreaming
- GroundIntegration, ReadinessCheck
- SimSelf
- Harness
- AtlasExam
- FrequencyChannel, FrequencyDynamics, ResonanceChannel (frequency kernel)
"""
from .constitution import (
    Constitution,
    ConstitutionalAxis,
    AXES_DEFINITIONS,
    AXIS_KEYWORDS,
    CONSTRAINT_WORDS,
    CONSTRAINT_PATTERN,
    embed_text,
    project_to_constitution,
    cosine,
    PHI,
    ALPHA,
    DIM,
    TWIN_PRIME_PAIRS,
    SEIFERT_GENERA,
    FREQ_RATIOS,
    N_SHEAVES,
    TEXT_EMBED_DIM,
)
from .resolution import ResolutionOperator
from .entity import EntityRecognition
from .memory import RelationalMemory
from .dreaming import ConstitutionalDreaming
from .ground import GroundIntegration, ReadinessCheck
from .consolidation_filter import (
    StabilityConsolidationFilter,
    STASIS, DENIED, DUPLICATE, CONSOLIDATED,
    DEFAULT_GROUNDING_MAP,
)
from .simself import SimSelf
from .harness import Harness
from .atlas_exam import AtlasExam

# The frequency kernel is intentionally NOT imported into the constitutional
# core (simself.py, constitution.py). The core stays free of any
# Schumann / 432 / 963 / etc. dependencies. Wiring frequency into the
# update loop is a per-deployment decision.
#
# The kernel IS exported here at the package level — callers can do
#   from constitutional import FrequencyChannel, ResonanceChannel, ...
# without an explicit `import constitutional.frequency` path. The kernel
# is *available* without being *required*. See frequency-architecture-2026-09-12.md.
from .frequency import (
    FrequencyChannel,
    FrequencyDynamics,
    ResonanceChannel,
    harmonic_sum,
    DEFAULT_FREQUENCY_HYPOTHESES,
)

__all__ = [
    # constitution
    "Constitution", "ConstitutionalAxis", "AXES_DEFINITIONS", "AXIS_KEYWORDS",
    "CONSTRAINT_WORDS", "CONSTRAINT_PATTERN",
    "embed_text", "project_to_constitution", "cosine",
    "PHI", "ALPHA", "DIM", "TWIN_PRIME_PAIRS", "SEIFERT_GENERA",
    "FREQ_RATIOS", "N_SHEAVES", "TEXT_EMBED_DIM",
    # modules
    "ResolutionOperator", "EntityRecognition", "RelationalMemory",
    "ConstitutionalDreaming", "GroundIntegration", "ReadinessCheck",
    "SimSelf", "Harness", "AtlasExam",
    # Frequency kernel is NOT in the public surface. Import it explicitly:
    #   from constitutional.frequency import FrequencyChannel, FrequencyDynamics, ResonanceChannel
    #   from constitutional.frequency import DEFAULT_FREQUENCY_HYPOTHESES
]
