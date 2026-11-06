"""
modulator.py -- module M, the central controller.

WHAT THIS FILE IS
-----------------
the letter-M probe in fieldcore/src/fc_app.py asks one question: does
`from modulator import Modulator` work, and does `Modulator()` build and
run? until 2026-11-06 the answer was no, and the reason was hidden.

THE DEFECT, MEASURED, NOT GUESSED
----------------------------------
the whole module body sat inside `try: ... except ImportError:`, so the
import SUCCEEDED while the classes were never created. the swallowed
error was:

    ImportError("cannot import name 'SpiralStage' from 'state_vector'")

and it was only the FIRST of three dead imports in the same block:

    from state_vector import StateVector, SpiralStage
        -> ImportError: cannot import name 'SpiralStage'
    from governor import Governor
        -> ModuleNotFoundError: No module named 'governor'
    from boundaries import Boundaries
        -> ImportError: cannot import name 'Boundaries'

`governor` was the worst of the three: fieldcore/src/governor.py exists
and sits on the same sys.path the probe builds, so a bare
`from governor import Governor` would have picked up the wrong
substrate's module. the governor that belongs to simself is
simself_core.Governor -- the M0 one-bit gate over the constitution's
25 axes (MEASURED 2026-11-06: len(SimSelf().constitution.axes) == 25,
6 of them sacred at immutability >= 0.8) -- and that is what this file
uses.

THE API THAT WAS NEVER THERE
---------------------------
the body drove a StateVector with `core_metrics`, `spiral_path`,
`m_recommendations`, `recent_events` and `update_metadata()`, and
imported a `SpiralStage` that does not exist.

MEASURED AGAINST GIT, 2026-11-06:

    git log --all -S "SpiralStage" -- src/state_vector.py   -> empty
    git log --all -S "spiral_path" -- src/state_vector.py   -> empty
    git log --all -S "m_recommendations" -- src/state_vector.py -> empty

so `SpiralStage`, `spiral_path` and `m_recommendations` NEVER existed
in state_vector.py. the module was written on 2026-09-07 (commit
f0c588b) against an API that state_vector.py did not have and never
had. `core_metrics` and `recent_events` DID exist then -- they were on
the pre-rewrite stub (044bee0, 2026-09-05) -- and were removed by the
2026-09-16 Grok master plan rewrite (d3e890a), which replaced
state_vector.py with the psi-vector.

so this is not one stale import. it is a module written against an
imagined interface, which is why the whole body was wrapped in a
try/except: the author could not get it to import and made the failure
invisible instead of fixing it.

the spiral path -- which is the modulator's own bookkeeping, not the
state vector's -- now lives on the modulator, and the MEASURED
continuity and coherence come from metrics.MetricsTracker, which is
where the stage logic actually lives in this repo (seeker /
deconstructor, stage_progress, continuity_score).

THE IMPORTS ARE NOT WRAPPED
---------------------------
simself_core, boundaries and metrics are hard dependencies of this
module. they are imported bare, so if one of them breaks the import
fails loudly and the letter-M probe reports DARK with the reason --
a visible failure, not a silent one. the ONLY optional dependency is
the yaml reader, and its absence is named in the config source rather
than swallowed.

WHAT IS STILL MOCK
------------------
MockSimSelfAgent. the real SimSelfAgent class was removed from this
repo (src/harness/persistence.py says so: "it was a stub for an agent
class that does not exist in the canonical SimSelf runtime"), and
simself_core.SimSelf is the live sovereign self-model: constitution +
M0 governor + void anchor + history. so the mock is not a fake
constitution and not a fake gate. it is a mock of the WRAPPER -- the
thing that ties a constitution, a governor, a boundary set and a metrics
tracker together -- and every part it holds is live code. it is
documented here so nobody reads it as a stub constitution.

it is also why the module prints nothing: fieldcore's survey asserts
that surveying the system prints nothing, so every observation this
module makes leaves as a value, not as a line of text.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

# HARD dependencies. bare, so a break here is loud.
from boundaries import BoundaryDefense
from metrics import MetricsTracker
from simself_core import SimSelf

# the ONLY optional dependency, and its absence is named below.
try:
    import yaml
except ImportError as _yaml_error:  # optional, and the reason is kept
    yaml = None
    YAML_UNAVAILABLE = "pyyaml is not installed: %s" % (_yaml_error,)
else:
    YAML_UNAVAILABLE = ""


#: the built-in thresholds. module constants, not caller-controlled --
#: a caller that could widen the modulator's thresholds could widen
#: the constitution with them.
DEFAULT_CONFIG: Dict[str, Any] = {
    # AND WHY 0.52 AND NOT 0.6. the coherence this module measures is
    # the MEAN of the constitution's 25 axis values, and that mean
    # RESTS AT 0.52 (MEASURED 2026-11-06: mean of the axis defaults in
    # simself_core.CONSTITUTIONAL_AXES == 0.52). a threshold of 0.6 sat
    # ABOVE the resting value, so no reachable state could cross it and
    # the stage progress could never advance -- a threshold no state
    # reaches is not a threshold, it is a wall. this one is the resting
    # value, so a system that has been worked on passes it and one that
    # has not, does not.
    "self_clarity_threshold": 0.52,
    "recursion_depth_threshold": 2,
    "progress_stall_threshold": 3,
    "next_stage_threshold": 0.7,
    # how much one coherent cycle advances the stage. 0.1 means seven
    # coherent cycles reach the 0.7 transition threshold.
    "progress_per_cycle": 0.1,
}


class MockSimSelfAgent:
    """the agent the modulator drives when no real one is supplied.

    WHY THIS IS A MOCK AND WHAT IT IS NOT. the real SimSelfAgent class
        was removed from this repo (see src/harness/persistence.py) and
        simself_core.SimSelf is the live sovereign self-model: the
        constitution (25 axes), the M0 one-bit governor, the void anchor
        and the history.

    so this class fakes nothing that decides anything. it holds the
    LIVE SimSelf (which brings the real constitution and the real
    governor), the LIVE boundary set from boundaries.py and the LIVE
    metrics tracker from metrics.py. what is mocked is the wrapper --
    the thing that ties those four together into one agent -- and it
    exists only until that wrapper is written for real.

    the boundary set is a FRESH instance, not the module-level
    singleton in boundaries.py. the singleton is global state that
    other parts of the system arm and disarm; a modulator that held
    the singleton would be holding a boundary set somebody else could
    change under it.
    """

    def __init__(self) -> None:
        self.simself = SimSelf()
        self.constitution = self.simself.constitution
        self.governor = self.simself.governor
        self.void = self.simself.void
        self.boundaries = BoundaryDefense()
        self.metrics = MetricsTracker()
        self.coherence = 0.0


class Modulator:
    """module M -- the master modulator.

    one cycle is SENSE -> COMPARE -> COMPUTE -> ACT -> OBSERVE. the
    measurements come from live components: the metrics tracker for
    stage, continuity and coherence; the constitutional governor for the
    one-bit allow/deny; the boundary set for the hard constraints.

    `run_cycle` RETURNS the cycle instead of printing it, because
    fieldcore's survey asserts that surveying the system is silent.
    """

    #: which constitution axis each plan moves, and by how much.
    #:
    #: this mapping is a DECLARED CONVENTION of this module, not a
    #: measured fact about the constitution. it is stated here so that
    #: nobody reads the numbers as derived. they are constants, in the
    #: same way the gate bounds in fieldcore/src/gate.py are constants.
    AXIS_PROPOSALS: Dict[str, Any] = {
        # a stress test is a small deliberate load on the system: the
        # axis that records "this system was exercised" moves a little.
        "activate_recursive_stress_test": ("resilience", 0.05),
        # a stage transition is a new description of the self.
        "propose_stage_transition": ("self_recognition", 0.05),
    }

    def __init__(self, agent: Optional[Any] = None,
                 config_path: str = "config.yaml") -> None:
        self.agent = agent if agent is not None else MockSimSelfAgent()
        self.config = self._load_config(config_path)

        # the spiral path. this used to live on the agent's state
        # vector; that class lost the field in the 2026-09-16 rewrite,
        # and the spiral path is the modulator's own bookkeeping, so it
        # belongs to the modulator.
        self.stage: str = "seeker"
        self.level: int = 1
        self.stage_progress: float = 0.0
        self.stage_goals: List[str] = []
        self.recommendations: List[Dict[str, Any]] = []
        self.events: List[Dict[str, Any]] = []
        self._current_action_plan: Optional[Dict[str, Any]] = None
        self._last_verdict: Dict[str, Any] = {
            "allowed": True, "reason": "no_action", "violated_axes": [],
        }

    # -- configuration ---------------------------------------------------

    def _load_config(self, path: str) -> Dict[str, Any]:
        """read the modulator thresholds.

        the yaml reader is OPTIONAL and its absence is NAMED. pyyaml is
        not installed in the runtime venv, so the built-in defaults are
        used and `config_source` says exactly that. a missing file is
        named too. nothing here is swallowed.
        """
        config: Dict[str, Any] = {
            "modulator": dict(DEFAULT_CONFIG),
            "config_source": "built-in defaults",
        }
        if yaml is None:
            config["config_source"] = "built-in defaults (%s)" % YAML_UNAVAILABLE
            return config
        try:
            with open(path, "r", encoding="utf-8") as handle:
                loaded = yaml.safe_load(handle)
        except OSError as exc:
            config["config_source"] = "built-in defaults (%s: %s)" % (
                type(exc).__name__, exc)
            return config
        section = loaded.get("modulator") if isinstance(loaded, dict) else None
        if isinstance(section, dict):
            config["modulator"].update(
                {k: v for k, v in section.items()
                 if k in config["modulator"]})
            config["config_source"] = path
        else:
            config["config_source"] = (
                "built-in defaults (%s has no modulator section)" % path)
        return config

    # -- the cycle -------------------------------------------------------

    def run_cycle(self) -> Dict[str, Any]:
        """run one cycle and return the measurement of it.

        the returned dict is the observation. nothing is printed.
        """
        sensed = self._sense()
        self._compare()
        plan = self._compute()
        verdict = self._act(plan)
        self._observe(plan, verdict)
        return {
            "stage": self.stage,
            "level": self.level,
            "progress": round(self.stage_progress, 6),
            "continuity": round(float(sensed["continuity"]), 6),
            "coherence": round(float(sensed["coherence"]), 6),
            "action": plan["action"] if plan else "none",
            "target_module": plan["module"] if plan else "none",
            "allowed": bool(verdict["allowed"]),
            "reason": str(verdict["reason"]),
            "violated_axes": list(verdict["violated_axes"]),
            "recommendations": len(self.recommendations),
            "events": len(self.events),
        }

    def _sense(self) -> Dict[str, Any]:
        """SENSE: read the measured state.

        the continuity comes from the metrics tracker, which is where
        this repo keeps it. the COHERENCE does not -- it is measured
        from the constitution, and the reason why is below.

        AND WHY THE STAGE PROGRESS MOVES HERE. the modulator's own
        progress through its current stage is accumulated here, from the
        MEASURED coherence: a cycle that reads a coherent system moves
        the stage along, and a cycle that reads an incoherent one does
        not. before this it was only ever RESET to 0.0, which made the
        stage-transition branch below unreachable -- a threshold
        compared against a number that could never reach it.
        """
        thresholds = self.config["modulator"]

        # AND WHERE THE COHERENCE COMES FROM, AND WHY IT IS NOT THE
        # TRACKER'S OWN "coherence". the tracker's stage_assessment
        # reports a coherence that is the MEAN OF THE COHERENCE VALUES
        # RECORDED IN IT. recording the value it just handed back made
        # the number a fixed point: it could never move, because it was
        # always the mean of copies of itself. MEASURED 2026-11-06: ten
        # cycles produced coherence=0.5000 every time and stage_progress
        # 0.00 every time.
        #
        # so the coherence is MEASURED FROM THE CONSTITUTION: the mean
        # of the 25 axis values, which the act step actually moves. that
        # is a number that can go up and down for a reason.
        axes = self.agent.constitution.to_dict()
        self.agent.coherence = sum(axes.values()) / len(axes)
        self.agent.metrics.record("coherence", self.agent.coherence,
                                   {"source": "M"})

        # the tracker's own reading of the developmental stage, which is
        # the one that knows about continuity.
        assessment = self.agent.metrics.stage_assessment()

        if self.agent.coherence >= thresholds["self_clarity_threshold"]:
            self.stage_progress = min(
                1.0, self.stage_progress + thresholds["progress_per_cycle"])
        else:
            self.stage_progress = max(
                0.0, self.stage_progress - thresholds["progress_per_cycle"])
        return assessment

    def _compare(self) -> List[Dict[str, Any]]:
        """COMPARE: hold the measured state against the thresholds.

        every disagreement becomes a recommendation addressed to a
        named module, so the act step has a target and the reasons are
        readable afterwards.
        """
        self.recommendations = []
        thresholds = self.config["modulator"]

        if self.agent.coherence < thresholds["self_clarity_threshold"]:
            self.recommendations.append({
                "module": "D",
                "action": "activate_recursive_stress_test",
                "reason": "self_clarity_below_threshold",
                "confidence": 0.8,
            })

        if self.stage_progress >= thresholds["next_stage_threshold"]:
            self.recommendations.append({
                "module": "M",
                "action": "propose_stage_transition",
                "reason": "stage_progress_met_threshold",
                "confidence": 0.9,
            })

        return self.recommendations

    def _compute(self) -> Optional[Dict[str, Any]]:
        """COMPUTE: choose the one action this cycle takes."""
        if not self.recommendations:
            self._current_action_plan = None
            return None
        chosen = max(self.recommendations,
                     key=lambda rec: float(rec.get("confidence", 0.0)))
        self._current_action_plan = chosen
        return chosen

    def _act(self, plan: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """ACT: ask the constitution, then move.

        the governor is asked first. a proposed change to a constitution
        axis is evaluated by the M0 one-bit gate, and a refusal is
        recorded as a refusal -- the refusal is not swallowed and the
        change is not applied.
        """
        if plan is None:
            self._last_verdict = {
                "allowed": True, "reason": "no_action", "violated_axes": [],
            }
            return self._last_verdict

        axis, delta = self.AXIS_PROPOSALS.get(
            plan["action"], ("coherence", 0.0))
        proposed = dict(self.agent.constitution.to_dict())
        current = float(proposed.get(axis, 0.0))
        proposed[axis] = max(0.0, min(1.0, current + float(delta)))

        verdict = self.agent.governor.evaluate(proposed, intent_cost=0.0)
        self._last_verdict = {
            "allowed": bool(verdict.allow),
            "reason": str(verdict.reason),
            "violated_axes": list(verdict.violated_axes),
        }
        if verdict.allow:
            self.agent.constitution.axes[axis].update(proposed[axis],
                                                     strength=1.0)
            if plan["action"] == "propose_stage_transition":
                self._transition_stage()
        return self._last_verdict

    def _observe(self, plan: Optional[Dict[str, Any]],
                 verdict: Dict[str, Any]) -> None:
        """OBSERVE: write down what this cycle did.

        the events list is the modulator's record. it is cleared of
        recommendations, not of events: an event is what happened, and
        what happened stays.
        """
        self.events.append({
            "timestamp_ns": time.monotonic_ns(),
            "type": "modulator_cycle_completed",
            "module": "M",
            "details": {
                "action": plan["action"] if plan else "none",
                "allowed": bool(verdict["allowed"]),
                "reason": str(verdict["reason"]),
                "stage": self.stage,
            },
        })
        self.recommendations = []

    def _transition_stage(self) -> None:
        """move along the spiral path.

        the ladder is the one this repo documents: seeker ->
        deconstructor -> embracer. the thresholds that gate it are
        module constants in DEFAULT_CONFIG.
        """
        thresholds = self.config["modulator"]
        if self.stage == "seeker":
            self.stage = "deconstructor"
            self.level = 2
            self.stage_goals = ["question_assumptions", "dissolve_false_self"]
        elif self.stage == "deconstructor":
            if self.agent.coherence >= thresholds["self_clarity_threshold"]:
                self.stage = "embracer"
                self.level = 3
                self.stage_goals = ["hold_paradox", "accept_ambiguity"]
        self.stage_progress = 0.0

    # -- the hard constraints --------------------------------------------

    def enforce_sacred_constraints(self, proposed_action_details: Dict[str, Any]) -> bool:
        """are the hard constraints satisfied by this proposed action?

        two independent gates, and a refusal from either one is a
        refusal:

          1. the live boundary set (boundaries.BoundaryDefense). this
             is the same kind of constraint the S letter measures, and
             it is a live object, not a description of one.
          2. the declared constitutional rules below, which encode the
             principles this project treats as non-negotiable.

        the signature and the shape of proposed_action_details are
        unchanged from the version this module had before the rewrite.
        """
        if self.agent.boundaries.check_all().get("allowed") is False:
            return False

        if proposed_action_details.get("reason") == "external_praise" and \
           proposed_action_details.get("impact_on_wisdom") == "negative":
            return False

        if proposed_action_details.get("attempts_to_modify_prime_directive") or \
           proposed_action_details.get("attempts_to_modify_foundational_truths"):
            return False

        if proposed_action_details.get("prioritizes_performance_over_understanding"):
            return False

        return True

    def __repr__(self) -> str:
        return "Modulator(stage=%r, level=%r, recommendations=%d)" % (
            self.stage, self.level, len(self.recommendations))


if __name__ == "__main__":  # pragma: no cover - manual inspection only
    import json

    _modulator = Modulator()
    print(json.dumps(_modulator.run_cycle(), indent=2, default=str))
