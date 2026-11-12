"""
_project_python.py -- THE INTERPRETER A CHECK MUST RUN UNDER, AND WHY
IT CANNOT BE THE ONE THAT LAUNCHED IT.

MEASURED 2026-11-12, on `tools/check_robot_wiring.py`:

    hermes venv  (python 3.11, no numpy)   ModuleNotFoundError: No
                                            module named 'numpy'
    project venv (python 3.14, numpy 2.5.3) GREEN

**AND THAT IS THE DEFECT CLASS QUEUE ITEM 59 CLOSED**, in a different
repo: *"the same probe read ABSENT under the hermes venv and ABSORBED
under the project venv -- the measurer was part of the measurement."*

**AND WHY THE DEPENDENCY IS REAL AND NOT A BUG IN THE CHECK.** The
check compares the body's drive against the fc's OWN kernel --
`fieldcore/src/tiniest_core/tiniest_core.py` -- and that module does
`import numpy as np` at module level. So the check cannot run without
numpy, and a copy of the fc's step written in plain python would be a
LOOKALIKE and not the fc's own function. **THE DEPENDENCY STAYS; WHAT
CHANGES IS THE INTERPRETER THE CHECK FINDS FOR ITSELF.**

**SO A CHECK RE-RUNS ITSELF UNDER THE PROJECT VENV** when the
interpreter that launched it has no numpy. Three rules:

  1. **THE RE-RUN IS ONCE.** An environment marker stops the loop, so
     a venv without numpy cannot send the check into a re-run that
     re-runs.
  2. **THE INTERPRETER IS PRINTED.** A number whose instrument is
     invisible is a number nobody can trust, and item 59's whole
     lesson was that the measurer must be visible.
  3. **THE PROJECT VENV IS NAMED, NOT GUESSED.** It sits beside the
     repo, and the path is derived from THIS FILE's location -- so the
     rule is a property of the tree, not of a machine's PATH.

Run:
    python -c "import _project_python as p; print(p.describe())"
"""
from __future__ import annotations

import os
import pathlib
import sys
from typing import Optional

#: THE MARKER, and it is what stops a re-run that re-runs.
REEXEC_MARKER = "FC_SIMSELF_CHECK_REEXEC"

#: THE PROJECT VENV, and it is found by WALKING UP from this file until
#: a `.venv` sits beside a `work_repos`-shaped tree. The hermes home
#: holds `work_repos/`, so the venv is at `work_repos/.venv`.
def project_venv() -> Optional[pathlib.Path]:
    """The project venv's interpreter, or None if it is not there."""
    here = pathlib.Path(__file__).resolve()
    for up in here.parents:
        cand = up / ".venv" / "Scripts" / "python.exe"
        if cand.exists():
            return cand
        posix = up / ".venv" / "bin" / "python"
        if posix.exists():
            return posix
    return None


def has_numpy() -> bool:
    """Can THIS interpreter import numpy? And which version?"""
    try:
        import numpy  # noqa: F401
    except Exception:                                   # noqa: BLE001
        return False
    return True


def numpy_version() -> str:
    try:
        import numpy
    except Exception:                                   # noqa: BLE001
        return "none"
    return getattr(numpy, "__version__", "unknown")


def describe() -> str:
    """ONE LINE ABOUT THE INSTRUMENT, and it goes in the check's
    output -- because a check that does not say what measured it is a
    check whose numbers cannot be compared with anything."""
    venv = project_venv()
    return ("the interpreter: %s (numpy %s); the project venv: %s"
            % (sys.executable, numpy_version(),
               venv if venv else "NOT FOUND"))


def reexec_under_project_python() -> Optional[int]:
    """Re-run THIS script under the project venv, if numpy is missing.

    **AND IT RETURNS None WHEN NO RE-RUN IS NEEDED**, so the caller
    simply continues. When it DOES re-run, it returns the exit code
    the child produced -- so the parent's verdict IS the child's
    verdict, and the parent does not decide anything of its own.

    **AND IT REFUSES TO RE-RUN TWICE.** The marker is set in the
    child's environment, and a child that finds the marker has already
    tried, so it runs in place and lets the import error surface with
    its own name -- which is the honest outcome for a tree whose venv
    has no numpy.
    """
    if has_numpy():
        return None
    if os.environ.get(REEXEC_MARKER):
        # The re-run already happened and the venv still has no numpy.
        # Continuing here lets the real ImportError name the module.
        return None
    venv = project_venv()
    if venv is None:
        return None
    env = dict(os.environ)
    env[REEXEC_MARKER] = "1"
    import subprocess
    script = pathlib.Path(sys.argv[0]).resolve()
    proc = subprocess.run([str(venv), str(script)] + list(sys.argv[1:]),
                          env=env)
    return proc.returncode
