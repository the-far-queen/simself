"""
simself — identity layer + harness + governance.

Canonical entry points:
- SimSelf: `from simself.src.constitutional.simself import SimSelf`
- Constitution: `from simself.src.constitutional.constitution import Constitution`
- Ground: `from simself.src.constitutional.ground import Ground`
- AtlasExam: `from simself.src.constitutional.atlas_exam import AtlasExam`
- Harness: `from simself.src.constitutional.harness import Harness`

Re-exports at package level so callers can do:
- `from simself import SimSelf`
- `from simself import AtlasExam`
- `from simself import Constitution`

Legacy modules (simself_core, simself_v6_2_unified, aif_being, etc.) live in
`simself/legacy/` and are not re-exported here. Use the constitutional path.
"""

from .constitutional.simself import SimSelf
from .constitutional.constitution import Constitution, ConstitutionalAxis
from .constitutional.ground import Ground
from .constitutional.atlas_exam import AtlasExam
from .constitutional.harness import Harness

__version__ = "2026-09-16"

__all__ = [
    "SimSelf",
    "Constitution",
    "ConstitutionalAxis",
    "Ground",
    "AtlasExam",
    "Harness",
]
