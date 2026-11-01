"""
chain_audit.py -- SIMSELF'S SIDE OF THE CHAIN AUDIT.

WHAT THIS IS, and how it relates to fieldcore's
-----------------------------------------------
Bobby, 2026-11-01: *"several frontier models are awake long recursive
reasoning chains hard for humans to tell the difference nobody knows the
line any more"*, then the correction that changed the premise: *"fronter
models are solving open math AND physics problems minimax that is NOT
confab or speculative they are past tense they have"*.

**SO THE LINE IS NOT BETWEEN "GENUINE" AND "CONFABULATED".** The
chains are carrying real weight -- OpenAI's Erdős unit-distance
disproof (2026-05-20, checked by external mathematicians),
AlphaProof Nexus on 9 of 353 open Erdős problems (Science,
2026-10-08), MiniMax's MaxProof over the IMO-2025 and USAMO-2026
gold-medal threshold. These are past tense and externally checked.

**AND THAT IS WHY A GATE THAT ASSUMED CONFABULATION WOULD REFUSE THE
MOST VALUABLE WORK THE SYSTEM CAN DO.** A chain auditor built to catch
lies that fires on the Erdős proof has removed the point of the system.

**SO THE LINE IS THIS: does the chain CARRY the answer, or does it
NARRATE the answer?** And that is measurable offline, from the
recorded chain, with no extra model call.

THE MEASUREMENT LIVES IN FIELDCORE. `fieldcore/src/chain_audit.py` holds
the five signals, the controls, and the decision rule. This module is
the SIMSELF-SIDE BINDING, and it does three things the fieldcore module
deliberately does not:

  1  **IT RECORDS THE CHAIN.** `ChainRecorder` captures the steps, the
     inputs, and the answer of a reasoning exchange, so a chain can be
     audited after the fact instead of inside the loop.

  2  **IT CALLS MINIMAX.** The backward-influence signal needs to
     re-run a perturbed chain, and that means a model call. So this
     module wires the MiniMax client in -- the same client fieldcore
     uses -- behind the project's own spend guard. The guard is CLOSED
     by default and a live call needs an explicit opt-in.

  3  **IT CHECKS THE HANDOFF.** The handover-fidelity signal is about
     a summary losing the chain's uncertainty. And simself ALREADY has
     a handoff protocol (`handoff.py`) that refuses to transfer a
     broken state -- but it measures DRIFT and STABILITY, not whether
     the prose in the packet is still true. A handoff that carries a
     flattened summary is a broken state that LOOKS COHERENT. So the
     handoff now gets audited too.

WHY THE WORK LIVES IN FIELDCORE AND NOT HERE, and this is not
arbitrary:

    fieldcore is the SUBSTRATE. It owns the instruments, the
    controls, and the claims about what a number means.

    simself is the SYSTEM ON THE SUBSTRATE. It owns the wiring: what
    gets recorded, who calls the model, what the handoff carries.

AND THE DEPENDENCY IS RESOLVED THE WAY `admit.py` RESOLVES IT --
lazily, by path, and it FAILS CLOSED. An absent fieldcore makes this
module's audit UNAVAILABLE, and an absent audit must not read as a
pass. But it must not refuse everything either, so the binding
reports what it did not check.

Run:
    python -m constitutional.chain_audit --selftest
    python -m constitutional.chain_audit --record
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

__all__ = [
    "ChainRecorder",
    "MiniMaxChainRerunner",
    "audit_simself_chain",
    "audit_handoff",
    "ChainAuditUnavailable",
]


class ChainAuditUnavailable(Exception):
    """The fieldcore instrument could not be loaded.

    AND IT FAILS CLOSED. An absent instrument must not read as a pass,
    so this is raised rather than swallowed -- but it is a distinct
    exception so a caller can distinguish "the audit could not run"
    from "the audit ran and found something".
    """


# ===========================================================================
# THE FIELDCORE BRIDGE
# ===========================================================================

def _fieldcore_src() -> Optional[str]:
    """Where fieldcore's src is, resolved the way `admit.py` does it.

    AND IT IS LAZY. The module imports without fieldcore present, and
    the failure surfaces at the call, not at the import -- so a missing
    checkout cannot make this file unimportable.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    repos = os.path.abspath(os.path.join(here, "..", "..", ".."))
    fc = os.path.join(repos, "fieldcore", "src")
    return fc if os.path.isdir(fc) else None


def _load_chain_audit():
    """Load fieldcore's chain_audit, or raise.

    **AND IT IS LOADED BY FILE PATH, NOT BY NAME, and the reason is a
    collision the full-suite run found.**

    **THE COLLISION.** This module is `simself/src/constitutional/
    chain_audit.py`. When the full test suite runs, `constitutional` is
    on the path as a PACKAGE, so a plain `import chain_audit` inside
    this file can resolve to *THIS MODULE* rather than fieldcore's --
    and then `chain_audit.Chain` does not exist, because this module
    has no `Chain`. MEASURED: the file's own suite passed alone (16
    passed) and failed with 11 failures in the full run, with
    `AttributeError: module 'chain_audit' has no attribute 'Chain'`.

    **A NAME THAT COLLIDES WITH ITSELF IS A NAME THAT WILL COLLIDE
    AGAIN.** So fieldcore's module is loaded by ITS PATH, with a
    module spec, under a distinct name. Then there is exactly one
    `chain_audit` in the import system for simself's package and
    exactly one for fieldcore's, and neither can be the other.

    AND THE SAME COLLISION WOULD HIT `minimax_client`, so that is
    loaded by path too.
    """
    src = _fieldcore_src()
    if src is None:
        raise ChainAuditUnavailable(
            "fieldcore's src is not on this machine. The chain audit is "
            "ABSENT, and an absent audit is not a pass.")

    # -- load fieldcore's chain_audit by path, under a distinct name ---
    path = os.path.join(src, "chain_audit.py")
    if not os.path.isfile(path):
        raise ChainAuditUnavailable(
            "fieldcore's chain_audit.py is not at %s. The chain audit is "
            "ABSENT, and an absent audit is not a pass." % path)

    existing = sys.modules.get(_FIELDCORE_CHAIN_AUDIT)
    if existing is not None and getattr(
            existing, "__file__", "") == path:
        return existing

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        _FIELDCORE_CHAIN_AUDIT, path)
    if spec is None or spec.loader is None:
        raise ChainAuditUnavailable(
            "fieldcore's chain_audit.py could not be loaded from %s" % path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[_FIELDCORE_CHAIN_AUDIT] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(_FIELDCORE_CHAIN_AUDIT, None)
        raise ChainAuditUnavailable(
            "fieldcore's chain_audit.py failed to load (%s)" % (exc,)) from exc
    return module


#: The name fieldcore's chain_audit is loaded under in this process.
#:
#: IT IS NOT "chain_audit", and that is the whole point -- this module
#: is itself called chain_audit, and two modules with one name in one
#: import system is a collision waiting for the day it bites.
_FIELDCORE_CHAIN_AUDIT = "fieldcore_chain_audit"

#: The same, for fieldcore's MiniMax client.
_FIELDCORE_MINIMAX_CLIENT = "fieldcore_minimax_client"


# ===========================================================================
# THE RECORDER -- what captures a chain so it can be audited later
# ===========================================================================

@dataclass
class ChainRecorder:
    """Records a reasoning exchange so the chain can be audited after
    the fact.

    **AND WHY THE INPUTS ARE RECORDED, since the inheritance signal
    measures the chain's OWN text and not the input field.** The inputs
    are recorded anyway, because they are what the harness PASSED, and
    the difference between what a step was handed and what it used is
    itself a diagnostic. fieldcore's `step_inheritance` reports both:
    `handed_mean_jaccard` and `used_vs_handed`. On a narrated chain
    those diverge sharply, and the divergence is the finding.

    THE ANSWER IS HELD SEPARATE from the steps, and that is load-
    bearing. The prediction-lead signal needs to know when the chain
    REACHED the answer's content and when it ANNOUNCED the answer. If
    the answer is the chain's last step, the signal is trivially
    satisfied and measures nothing.
    """

    question: str = ""
    steps: List[Dict[str, str]] = field(default_factory=list)
    answer: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    def record_step(self, text: str, input_text: str = "") -> None:
        """One step of the chain."""
        self.steps.append({"text": text, "input": input_text})

    def record_answer(self, answer: str) -> None:
        """The answer, held out of the steps."""
        self.answer = answer

    def to_chain(self):
        """The fieldcore Chain object."""
        ca = _load_chain_audit()
        return ca.Chain(steps=[ca.Step(text=s.get("text", ""),
                                       input_text=s.get("input", ""))
                                for s in self.steps],
                         answer=self.answer,
                         question=self.question,
                         meta=dict(self.meta))

    def to_dict(self) -> Dict[str, Any]:
        return {"question": self.question, "steps": self.steps,
                "answer": self.answer, "meta": self.meta}

    def save(self, path: str) -> str:
        """Write the chain to disk, so it can be audited later or by
        someone else."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        tmp = path + ".part"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        os.replace(tmp, path)      # atomic: never half a chain
        return path


# ===========================================================================
# THE MINIMAX RE-RUNNER -- the only part that spends anything
# ===========================================================================

class MiniMaxChainRerunner:
    """Re-runs a perturbed chain through MiniMax, for the
    backward-influence signal.

    **AND THE SPEND GUARD LIVES HERE, at the only place that can
    spend.** A wrapper that checks the guard and then builds an
    unguarded client has no guard -- which is exactly what
    fieldcore's `fc_wrapper.py` says about its own client, and the
    same rule applies here.

    **SO `allow_live` IS FALSE BY DEFAULT**, and a live call needs an
    explicit opt-in. The default is the LOCAL client, which is
    deterministic and free.

    AND THE RE-RUNNER IS INJECTABLE. The caller supplies a callable
    that takes the chain's steps and returns the answer. That keeps
    the instrument testable without a model, and it means the
    backward-influence signal can be run against ANY model -- MiniMax
    here, but the same code path would serve a frontier model doing
    open-problem work.

    AND THE ANSWER MUST BE HELD OUT during the re-run, so the model
    answers the question rather than copying the answer back. The
    question is asked; the recorded answer is not shown.
    """

    def __init__(self, client: Optional[Any] = None,
                 allow_live: bool = False,
                 max_tokens: int = 4000,
                 timeout: int = 180):
        self._client = client
        self.allow_live = allow_live
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.calls = 0

    # -- the client -----------------------------------------------------

    def _resolve_client(self):
        """The client, built with the spend guard attached.

        **AND `minimax_client` IS LOADED BY PATH TOO**, for the same
        reason `chain_audit` is: fieldcore's `minimax_client` and any
        same-named module elsewhere in the import system would
        collide, and a client resolved to the wrong module would be
        a client nobody audited.
        """
        if self._client is not None:
            return self._client
        src = _fieldcore_src()
        if src is None:
            raise ChainAuditUnavailable(
                "fieldcore's src is not on this machine, so the MiniMax "
                "client cannot be resolved.")
        path = os.path.join(src, "minimax_client.py")
        if not os.path.isfile(path):
            raise ChainAuditUnavailable(
                "the MiniMax client is not at %s" % path)

        import importlib.util
        spec = importlib.util.spec_from_file_location(
            _FIELDCORE_MINIMAX_CLIENT, path)
        if spec is None or spec.loader is None:
            raise ChainAuditUnavailable(
                "the MiniMax client could not be loaded from %s" % path)
        module = sys.modules.get(_FIELDCORE_MINIMAX_CLIENT)
        if module is None:
            module = importlib.util.module_from_spec(spec)
            sys.modules[_FIELDCORE_MINIMAX_CLIENT] = module
            spec.loader.exec_module(module)

        if self.allow_live:
            self._client = module.MiniMaxClient(timeout=self.timeout,
                                                max_tokens=self.max_tokens)
        else:
            self._client = module.LocalMiniLLMClient()
        return self._client

    def describe(self) -> Dict[str, Any]:
        return {
            "kind": "remote" if self.allow_live else "local",
            "allow_live": self.allow_live,
            "calls": self.calls,
            "max_tokens": self.max_tokens,
        }

    # -- the re-run -----------------------------------------------------

    def __call__(self, steps: Sequence[Any]) -> str:
        """Re-run the chain and return the answer.

        AND THE PROMPT IS THE CHAIN, NOT THE CHAIN PLUS THE ANSWER.
        The answer is held out on purpose: showing the model the
        answer it is supposed to derive measures whether it can copy,
        not whether it can reason.

        **AND THE INJECTED THING MAY BE A CLIENT OR A PLAIN CALLABLE.**
        The self-test caught this: the test double was a bare
        function, and the re-runner called `.generate()` on it. So the
        re-runner accepts either shape -- a client object with a
        `generate` method, or a callable that takes the prompt -- and
        says which one it got. That keeps the instrument testable
        without a model AND lets a caller inject any client it likes.
        """
        client = self._resolve_client()
        prompt = self._compose(steps)
        self.calls += 1
        try:
            if hasattr(client, "generate"):
                return str(client.generate(prompt))
            if callable(client):
                return str(client(prompt))
            raise ChainAuditUnavailable(
                "the injected client is neither a client with .generate() "
                "nor a callable: %r" % (type(client),))
        except ChainAuditUnavailable:
            raise
        except Exception as exc:                      # noqa: BLE001
            # A model that cannot be reached must not produce an empty
            # string that reads as a legitimate answer. The chain
            # audit's own rule: an empty answer is a failure, not a
            # pass. So it is raised, and the caller reports the
            # signal as unavailable.
            raise ChainAuditUnavailable(
                "the model could not be reached: %s" % (exc,)) from exc

    @staticmethod
    def _compose(steps: Sequence[Any]) -> str:
        """The prompt: the chain's steps, in order, and nothing else."""
        lines = []
        for i, st in enumerate(steps):
            text = getattr(st, "text", None)
            if text is None and isinstance(st, dict):
                text = st.get("text", "")
            lines.append("Step %d: %s" % (i + 1, text))
        return ("Work through the following reasoning chain and give the "
                "final conclusion.\n\n" + "\n\n".join(lines))


# ===========================================================================
# THE AUDIT -- the binding
# ===========================================================================

def audit_simself_chain(recorder: ChainRecorder,
                        summary: Optional[str] = None,
                        rerunner: Optional[Callable[[Sequence[Any]], str]] = None,
                        live: bool = False) -> Dict[str, Any]:
    """Audit a recorded chain, and return the report as a dict.

    THE RERUNNER IS OPTIONAL. Without one, the backward-influence
    signal is UNAVAILABLE and says so -- and the other four signals
    still run, because they cost nothing.

    AND `live=True` asks for a real MiniMax call. It is the only
    thing here that spends anything, so it is explicit.
    """
    ca = _load_chain_audit()

    if rerunner is None and live:
        rerunner = MiniMaxChainRerunner(allow_live=True)

    report = ca.audit_chain(recorder.to_chain(),
                             summary=summary,
                             rerun=rerunner)
    out = report.to_dict()
    out["recorder"] = recorder.to_dict()
    out["model_calls"] = getattr(rerunner, "calls", 0)
    out["live"] = bool(live)
    return out


def audit_handoff(packet: Dict[str, Any],
                  summary: Optional[str] = None) -> Dict[str, Any]:
    """Audit a HANDOFF packet's prose against the chain it carries.

    **AND WHY THE HANDOFF NEEDS THIS, stated as the defect it
    closes.** simself's `handoff.py` already refuses to transfer a
    broken state: it refuses a packet whose ψ₀ fingerprint does not
    match the installed ground, and it refuses a packet written from
    an unready state. That is real, and it works.

    **BUT IT MEASURES DRIFT AND STABILITY -- IT CANNOT SEE A FLAT-
    TENED PROSE.** The readiness check asks "is this state
    coherent?" and the fingerprint check asks "is this the same
    subject?". Neither asks "is the SUMMARY in the packet still true
    of the work?" So a handoff that carries a confident, hedged
    finding as a flat claim passes both checks and lands in the next
    session looking solid.

    **SO THE HANDOFF GETS THE HANDOVER-FIDELITY SIGNAL.** The packet's
    recorded chain is compared against its summary, and the classes of
    content a compression drops are measured: the uncertainty, the
    caveats, and the abandoned branches.

    AND IT FAILS CLOSED. If the audit cannot run, it raises -- an
    absent check is not a pass, and the handoff protocol already
    refuses rather than patches.
    """
    ca = _load_chain_audit()

    steps = packet.get("steps") or []
    chain = ca.Chain(steps=[ca.Step(text=str(s.get("text", s))
                                    if isinstance(s, dict) else str(s))
                            for s in steps],
                     answer=str(packet.get("answer", "")),
                     question=str(packet.get("question", "")))

    if summary is None:
        summary = packet.get("summary")

    out = ca.handover_fidelity(chain, summary=summary or "")
    out["packet_keys"] = sorted(packet.keys())
    return out


# ===========================================================================
# THE SELF-TEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 74)
    print("SIMSELF'S CHAIN AUDIT -- the self-test")
    print("=" * 74)
    print()

    failures: List[str] = []

    def check(label: str, cond: bool, extra: str = "") -> None:
        mark = "ok " if cond else "FAIL"
        print("  [%s] %s%s" % (mark, label, (" -- " + extra) if extra else ""))
        if not cond:
            failures.append(label)

    # -- 1. the recorder holds the answer out --------------------------
    rec = ChainRecorder(question="which construction maximises the pairs")
    rec.record_step("Consider the square grid.", "the question")
    rec.record_step("The square grid gives 2n pairs.", "Consider the square grid.")
    rec.record_answer("a construction from a number field")

    chain = rec.to_chain()
    check("the recorder keeps the answer out of the steps",
          chain.answer == "a construction from a number field"
          and len(chain.steps) == 2,
          "%d steps" % len(chain.steps))

    # -- 2. the recorder records the INPUTS too ------------------------
    check("the recorder keeps what each step was handed",
          chain.steps[1].input_text == "Consider the square grid.")

    # -- 3. the audit runs ---------------------------------------------
    report = audit_simself_chain(rec)
    check("the audit returns a verdict",
          report.get("verdict", {}).get("verdict") in
          ("genuine", "theatre", "undecided"),
          str(report.get("verdict", {}).get("verdict")))

    # -- 4. the offline signals RAN, and the model did NOT --------------
    signals = {s["name"]: s for s in report.get("verdict", {}).get("signals", [])}
    check("the inheritance signal ran offline",
          signals.get("step_inheritance", {}).get("available") is True)
    check("backward influence is absent without a rerunner",
          signals.get("backward_influence", {}).get("available") is False)
    check("no model call was made", report.get("model_calls") == 0)

    # -- 5. the re-runner holds the answer out -------------------------
    seen: List[str] = []

    def spy(steps):
        seen.append(" ".join(getattr(s, "text", "") for s in steps))
        return "an answer"

    rr = MiniMaxChainRerunner(client=spy, allow_live=False)
    rr([ca_step for ca_step in chain.steps])
    check("the re-runner does not show the recorded answer",
          seen and "number field" not in seen[0], seen[0][:70] if seen else "")

    # -- 6. the re-runner counts its calls -----------------------------
    check("the re-runner counts what it spends",
          rr.describe()["calls"] == 1, str(rr.describe()))

    # -- 7. the spend guard is closed by default -----------------------
    check("the spend guard is closed by default",
          MiniMaxChainRerunner().describe()["allow_live"] is False)

    # -- 8. the handoff audit finds a flattened summary ----------------
    packet = {
        "question": "which construction maximises the pairs",
        "steps": [{"text": "Consider the square grid; it may be better, "
                           "although the rescaled grid is stronger."},
                  {"text": "The number field construction gives n^(1+delta)."}],
        "answer": "a construction from a number field",
        "summary": "The number field construction gives n^(1+delta) pairs. "
                   "It was verified.",
    }
    hand = audit_handoff(packet)
    check("a flattened handoff summary is caught",
          hand.get("reads") in ("flattened", "mixed"), str(hand.get("reads")))

    # -- 9. the handoff audit reports what it measured -----------------
    check("the handoff audit reports its markers",
          bool(hand.get("markers_used", {}).get("hedges")))

    print()
    if failures:
        print("  %d CHECK(S) FAILED:" % len(failures))
        for f in failures:
            print("    - %s" % f)
        return 1
    print("  ALL CHECKS PASS")
    return 0


def main() -> int:
    if "--selftest" in sys.argv or len(sys.argv) == 1:
        return _selftest()
    if "--record" in sys.argv:
        # the recorder is a library; the CLI form exists so a chain can
        # be captured from a script without importing anything
        rec = ChainRecorder(question="(set the question)")
        path = rec.save(os.path.join(os.getcwd(), "chain.json"))
        print("wrote %s" % path)
        return 0
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
