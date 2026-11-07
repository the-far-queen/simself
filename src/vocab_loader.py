"""
vocab_loader.py -- LOAD THE VOCABULARY LEARNER WITHOUT THE PACKAGE.

THE DEFECT THIS FIXES
---------------------
MEASURED 2026-11-07: the vocabulary bench could not be run by the
interpreter the cron uses.

    $ python src/bench_canon_vocab.py
    ModuleNotFoundError: No module named 'numpy'
    exit 1

**AND THE MODULE IT WANTS DOES NOT USE NUMPY.** `learned_vocab.py`
imports only hashlib, json, os, re and dataclasses. The dependency
came in through the PACKAGE: `from constitutional import learned_vocab`
executes `constitutional/__init__.py`, which imports `constitution.py`,
which imports numpy at module level.

**SO THE MEASUREMENT THAT DECIDES THE VOCABULARY'S QUALITY WAS
HOSTAGE TO A LIBRARY IT DOES NOT USE.** And the consequence is not
cosmetic: a measurement that runs on one interpreter and not on
another is a measurement the next session cannot reproduce. The
verifier for this file is the vocabulary artifact's own digest, and
the artifact is committed -- so the check that matters has to be
runnable wherever the artifact is checked.

**AND THE FALLBACK IS NOT A COPY.** The loader tries the ordinary
import first, so on a machine with numpy the module identity is
exactly what it always was -- one `learned_vocab`, one `Vocabulary`
class. Only when the package import fails does it load the file
directly, and it registers the result under `constitutional.learned_vocab`
in `sys.modules` so that a later import of the same name finds the
SAME module object rather than a second copy of it.

**AND THAT IDENTITY MATTERS.** `Vocabulary` is a frozen dataclass, and
a test that does `isinstance(x, lv.Vocabulary)` against a different
copy of the class would be comparing against a class that is not the
one the object was built from. So the loader registers, and the
loader is the only way the vocabulary is imported from now on.

Run:
    python src/vocab_loader.py
"""
from __future__ import annotations

import importlib.util
import os
import sys
from typing import Any

_SRC = os.path.dirname(os.path.abspath(__file__))
_MODULE_NAME = "constitutional.learned_vocab"
_PATH = os.path.join(_SRC, "constitutional", "learned_vocab.py")


def load_learned_vocab() -> Any:
    """the vocabulary learner, with or without numpy on this machine.

    Returns the module. The ordinary import is tried FIRST, so the
    module identity is unchanged wherever the package import works.
    """
    existing = sys.modules.get(_MODULE_NAME)
    if existing is not None:
        return existing
    try:
        from constitutional import learned_vocab as lv
        return lv
    except ImportError:
        # The package __init__ needs numpy; the learner does not.
        pass
    if _SRC not in sys.path:
        sys.path.insert(0, _SRC)
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _PATH)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load %s" % _PATH)
    module = importlib.util.module_from_spec(spec)
    # REGISTERED BEFORE EXECUTION: a dataclass resolves its own
    # module in sys.modules at class-creation time, and an unregistered
    # module makes that lookup fail with
    # "AttributeError: 'NoneType' object has no attribute '__dict__'".
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    lv = load_learned_vocab()
    print("loaded %s" % lv.__name__)
    print("  file    %s" % os.path.abspath(lv.__file__))
    print("  numpy imported by this load: %s"
          % ("numpy" in sys.modules))
    print("  verbs/nouns in the artifact: %d / %d"
          % (len(lv.load_vocabulary().verbs),
             len(lv.load_vocabulary().nouns)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
