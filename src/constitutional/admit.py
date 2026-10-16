"""
admit.py — the seam where the model's proposals meet the only write path.

WHY THIS FILE EXISTS (2026-10-16, Hermes).

Two modules already existed and neither could reach the other:

  coding_operator_object.CodingOperatorObject.propose_span()
      the model's I/O surface. Calls harness.gate.gated_call, returns a
      verdict dict, records history. Never called by anything.

  constitutional.lexicon.ingest.ingest()
      documented as "the ONLY write path for language in the shell". Also
      never called by the operator.

So the system had a gate and a write path and no route between them. The
atlas exam called this "UNWIRED", which was correct in its own terms --
it counts callers, and there were none.

This module is that route, and it is deliberately the ONLY one. Everything
that wants to get a span into the lexicon goes through `admit()`. There is
no second import of ingest.py elsewhere in the runtime path.

WHY THE DOUBLE GATE, since both sides already check

  harness.gate.gated_call  and  ingest.gate_m0  are the SAME two
  inequalities (norm + cosine to psi_0). ingest.py's own docstring is
  explicit that divergence between them means "the policy has already
  split".

  They are both run anyway, on purpose. Not redundancy for its own sake:

    - gated_call is the PROPOSAL-time check. It runs before anything is
      embedded twice or allocated. It is cheap and it is the model's only
      sanctioned exit.
    - gate_m0 is the COMMIT-time check, inside ingest, against the live
      psi rather than psi_0 alone. Drift can open between the two.

  Running only one would leave a window where a span was checked against
  a ground that has since moved. Running both means the span must survive
  the same policy twice, at two different moments, and the second one is
  the stricter because it sees drift.

WHAT THIS DOES NOT ESTABLISH

That self-coding works. It establishes that a proposal can reach the write
path through a gate that can veto, and that the veto is real in both
directions. Sandbox execution, version comparison and rollback — the rest of
area 18 — are still absent, and the exam is right to say so.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from coding_operator_object import CodingOperatorObject  # noqa: E402
from constitutional.lexicon.ingest import Unit, Verdict, embed_bag, ingest  # noqa: E402


class Admitter:
    """The route from a model proposal to a committed lexicon unit.

    Construct once. `admit()` is the single entry point; there is no other
    supported way to get a span into the index.
    """

    def __init__(
        self,
        psi: Optional[np.ndarray] = None,
        psi0: Optional[np.ndarray] = None,
        embed=None,
        classify=None,
        **ingest_kwargs,
    ):
        from constitutional.lexicon.ingest import classify_span

        self.operator = CodingOperatorObject(embed_fn=embed or embed_bag,
                                             psi0=psi0)
        self.embed = self.operator.embed
        self.psi0 = np.asarray(self.operator.psi0, dtype=float)
        self.psi = np.asarray(psi if psi is not None else self.psi0, dtype=float)
        self.classify = classify or classify_span
        self.index: List[Unit] = []
        self.ingest_kwargs = ingest_kwargs
        # Every refusal, with the stage that produced it. A refused span that
        # looks accepted downstream is the failure this record exists to make
        # visible.
        self.refusals: List[Tuple[str, str, dict]] = []

    def admit(self, span: str) -> Tuple[Optional[Unit], Optional[Verdict]]:
        """Propose, gate, then ingest. Returns (unit_or_None, verdict_or_None).

        A refused span returns (None, None) — there is no Verdict to report
        because no commit was attempted. The reason is in `refuse_log()`,
        keyed by stage. `unit is None` means refused; there is no code path
        that returns a unit without both gates having allowed it.
        """
        span = " ".join(span.split())
        if not span:
            self.refusals.append(("<empty>", "pre_gate", {}))
            return None, None

        # 1. proposal-time gate. Cheapest, and the model's only exit.
        proposal = self.operator.propose_span(span)
        if not proposal.get("allow"):
            self.refusals.append((span, "propose", proposal))
            return None, None

        # 2. commit-time gate, inside ingest, against live psi.
        try:
            unit, verdict = ingest(
                span,
                self.psi0,
                self.psi,
                self.index,
                self.embed,
                self.classify,
                **self.ingest_kwargs,
            )
        except Exception as exc:  # noqa: BLE001
            # An exception must never read as an admission. Record and refuse.
            self.refusals.append((span, "ingest_error", {"error": str(exc)}))
            return None, None

        # CORRECTION 2026-10-16: read the verdict's own `allow` field.
        # This first read `verdict.status`, which does not exist on the
        # dataclass — getattr returned None, every ALLOWED span fell into
        # the refusal branch, and the admitter refused 100% of input while
        # looking like it was working. A gate that refuses everything is a
        # wall; this one was a wall with a docstring about gates.
        if not getattr(verdict, "allow", False):
            self.refusals.append((span, "ingest", {"verdict": str(verdict)}))
            return None, verdict

        # ingest() OWNS THE INDEX. It appends the unit itself in each of its three
        # return branches (admit / commit-with-support / commit). This module
        # passed its own `self.index` in, then appended AGAIN — so one admit()
        # produced a duplicated span, and the index grew at 2x. Duplicated
        # units silently corrupt nearest_committed() costs for every later
        # admission, which is the kind of drift that only shows up as "the
        # gate got stricter" weeks later.
        #
        # The unit is returned; that is the caller's signal. Do not re-append.
        return unit, verdict

    def refuse_log(self) -> List[Tuple[str, str, dict]]:
        """(span, stage, detail) for every refusal, in order."""
        return list(self.refusals)