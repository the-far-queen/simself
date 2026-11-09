"""
coding_operator_object.py — model-as-engine, gated (per Grok master plan Step 5).

The model sits outside the diagram. It emits candidate spans. Ingest and the
gate decide whether those spans become units or acts. A wrapper intercepts both
directions: spans leave only as typed packets; replies return only as spans
offered to ingest.

Per Batch 1 K8: any path the model uses to act must go through
harness/gate.py:gated_call. If gated_call is unavailable, this module raises
on construction rather than silently bypassing the gate.
"""

from __future__ import annotations

import os
from typing import Any, Optional

import numpy as np

# IMPORT FIX 2026-10-16 (Hermes). This module lives at src/ top level and is
# consumed two different ways, which is why the relative import below could
# never succeed in either of them:
#
#   1. as a package member:      from src.coding_operator_object import ...
#                                 -> ".harness.gate" is correct
#   2. as a bare module:         sys.path.insert(0, "src"); import
#                                coding_operator_object
#                                 -> ".harness.gate" raises
#                                 "attempted relative import with no known
#                                 parent package"
#
# Every test in this repo uses form 2. So the module's own fail-closed guard
# fired on every construction attempt and area 18 of the atlas exam could
# never measure it — reported as UNWIRED when the truth was UNUSABLE.
#
# Try the relative form first (keeps the package form honest), then fall back
# to the absolute one. If BOTH fail, _GATE_AVAILABLE stays False and the
# constructor still refuses to build — fail-closed is preserved exactly.
try:  # form 1: imported as src.coding_operator_object
    from .harness.gate import gated_call
    _GATE_AVAILABLE = True
    _GATE_ERROR = ""
except ImportError as _rel_err:
    try:  # form 2: imported as a bare module with src/ on sys.path
        from harness.gate import gated_call  # type: ignore[no-redef]
        _GATE_AVAILABLE = True
        _GATE_ERROR = ""
    except ImportError as _abs_err:
        _GATE_AVAILABLE = False
        _GATE_ERROR = f"relative: {_rel_err}; absolute: {_abs_err}"


def _resolve_embed():
    """Default embedder, importable as a package member OR as a bare module.

    Same dual-form problem as the gate import above; same resolution.
    """
    try:
        from .constitutional.lexicon.ingest import embed_bag
        return embed_bag
    except ImportError:
        from constitutional.lexicon.ingest import embed_bag  # type: ignore[no-redef]
        return embed_bag


def _resolve_psi0():
    """Ground psi_0, same dual-form resolution."""
    try:
        from .constitutional.ground import Ground
        from .constitutional.constitution import Constitution
    except ImportError:
        from constitutional.ground import Ground  # type: ignore[no-redef]
        from constitutional.constitution import Constitution  # type: ignore[no-redef]
    return Ground(Constitution().psi_0.copy()).psi_0


def _resolve_cycle():
    """The self-coding cycle, and the SAME DUAL FORM as the gate above.

    AND WHY IT NEEDS IT: this module lives at `src/` top level and is
    consumed two ways -- as a package member (`from src.coding_operator
    _object import ...`) and as a bare module (`sys.path.insert(0,
    "src"); import coding_operator_object`). Every test in this repo
    uses the second form, and the cycle lives one level down in
    `src/autocode/`, so the bare form's path is `autocode.self_coding
    _cycle`. MEASURED: the first version of this used the relative form
    only, and it raised ImportError on every call in the bare form --
    the same defect the gate import above documents, one level down.
    """
    try:  # form 1: imported as src.coding_operator_object
        from .autocode.self_coding_cycle import GoalContract, run_cycle
        return GoalContract, run_cycle
    except ImportError:
        pass
    try:  # form 2: imported as a bare module with src/ on sys.path
        from autocode.self_coding_cycle import GoalContract, run_cycle
        return GoalContract, run_cycle
    except ImportError as exc:
        raise RuntimeError(
            "coding_operator_object: the self-coding cycle is not "
            "importable, so a candidate change cannot be tried in a "
            "sandbox, compared, or rolled back. Underlying error: %r"
            % (exc,)
        )


class CodingOperatorObject:
    """The model's I/O surface. Gated by the harness."""

    def __init__(self, embed_fn=None, psi0: Optional[np.ndarray] = None):
        if not _GATE_AVAILABLE:
            raise RuntimeError(
                "coding_operator_object: harness.gate.gated_call not importable. "
                "Per Grok master plan Step 5: every model path must be gated. "
                f"Underlying error: {_GATE_ERROR}"
            )
        if embed_fn is None:
            embed_fn = _resolve_embed()
        if psi0 is None:
            psi0 = _resolve_psi0()
        self.embed = embed_fn
        self.psi0 = psi0
        self.history = []

    def propose_span(self, span: str) -> dict:
        """Send a candidate span through the gate.

        Returns a verdict dict. The span does NOT become a unit until ingest
        commits it. This is the M1→ M0 hand-off.
        """
        verdict = gated_call(span, self.psi0, self.embed)
        verdict["span"] = span
        self.history.append(verdict)
        return verdict

    def is_allowed(self, span: str) -> bool:
        verdict = self.propose_span(span)
        return bool(verdict.get("allow"))

    def propose_change(self, diff_text: str, repo_root: str, *,
                       goal=None, tasks=None, max_rounds: int = 3,
                       checkpoint_dir: Optional[str] = None,
                       auto_commit: bool = True) -> dict:
        """Try a candidate CHANGE in the self-coding cycle, and land it
        only if it holds.

        **AND THIS IS THE MISSING HALF OF THE GATE.** The gate decides
        whether a candidate span may become a unit -- it does not run
        the candidate against the current system, and it cannot undo
        one. So the four shapes live in
        `autocode.self_coding_cycle`, and this method is the route
        INTO them.

        AND THE ORDER IS THE ORDER THE ATLAS EXAM'S AREA 18 STATES:
        "self-coding must run in a sandbox, compare against the current
        version, and roll back on invariant violation". So a candidate
        change is tried in a SANDBOX, COMPARED against the current
        version's own measurement, and ROLLED BACK if the verification
        fails -- and the goal's STOP RULE says when the loop ends.

        AND THE GATE STILL RUNS FIRST. A span that the gate refuses
        never reaches the cycle, so the cycle is a second line and not
        a replacement.
        """
        GoalContract, run_cycle = _resolve_cycle()

        if goal is None:
            goal = GoalContract(
                end_state="the change is landed",
                proof="the cycle's verification",
                boundaries=("the ground does not move",),
                loop="one round per candidate",
                stop_rule="adopted >= 1",
            )
        if tasks is None:
            tasks = ()
        history = []

        def candidate(round_no: int) -> str:
            history.append(diff_text)
            return diff_text

        result = run_cycle(goal, candidate, repo_root, tasks=tasks,
                           max_rounds=max_rounds,
                           checkpoint_dir=checkpoint_dir,
                           auto_commit=auto_commit)
        described = result.describe()
        described["candidate"] = diff_text
        return described

    def refuse_log(self) -> list:
        """Return the spans that were refused by the gate."""
        return [v for v in self.history if not v.get("allow")]
