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
from .simself import SimSelf
from .harness import Harness
from .atlas_exam import AtlasExam

# The frequency kernel is intentionally NOT imported at package level.
# It is opt-in: callers must `import constitutional.frequency` explicitly.
# This is the architectural guarantee that the constitutional core stays
# free of any frequency / Schumann / 432 / 963 / etc. dependencies.

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
