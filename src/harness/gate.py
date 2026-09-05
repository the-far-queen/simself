"""
Gate — All external tool calls pass through the Governor first.

Pattern from agent frameworks: a Gate sits between the agent's will and any
external action. The agent proposes a tool use, the Gate asks the Governor
for a decision (allow / refuse / defer), and only executes on approve.

The Governor is duck-typed: anything with a `decide(action: str, coherence: float) -> str`
method and an `apply_action_cost(decision: str)` method works. SimSelf's own
`sim_self_core.SimSelf` qualifies (its `evaluate_intent` returns a `Verdict`
dataclass; the Gate handles both shapes).
"""

from typing import Callable, Any, Dict, Optional


# Sentinel / standard refusal signal.
# We use a string constant rather than importing an Action enum so the Gate
# is decoupled from any specific module's enum design.
DECISION_REFUSE = "REFUSE"
DECISION_ALLOW = "ALLOW"
DECISION_DEFER = "DEFER"


class Gate:
    """
    As described in fieldcore-code.md, this class ensures that all external
    calls (e.g., tool use) must first be approved by the Governor.
    It acts as a checkpoint between the agent's will and its external actions.
    """

    def __init__(self, governor, coherence_threshold: float = 0.4):
        """
        Initializes the Gate with a reference to the agent's Governor.

        governor: any object exposing:
            - decide(action: str, coherence: float) -> Union[str, Verdict]
            - apply_action_cost(decision) -> None
        coherence_threshold: minimum coherence to allow any tool use
        """
        self.governor = governor
        self.coherence_threshold = coherence_threshold
        self.history = []
        print(f"Gate: Initialized. Coherence threshold = {coherence_threshold}.")

    def _normalize_decision(self, raw) -> str:
        """Governor may return a string or a Verdict-like object. Normalize."""
        if isinstance(raw, str):
            return raw.upper()
        # Verdict-like: .allow attribute (sim_self_core) or .name (enum)
        if hasattr(raw, "allow"):
            return DECISION_ALLOW if raw.allow else DECISION_REFUSE
        if hasattr(raw, "name"):
            return str(raw.name).upper()
        # Fallback: refuse if ambiguous
        return DECISION_REFUSE

    def request_tool_use(
        self,
        tool: Callable[..., Any],
        coherence_score: float,
        **kwargs: Any,
    ) -> Optional[Any]:
        """
        Requests permission to use a tool and executes it if approved.

        :param tool: The tool or function to be executed.
        :param coherence_score: The agent's current coherence score.
        :param kwargs: Arguments to be passed to the tool.
        :return: The result of the tool execution, or None if refused/deferred.
        """
        # 0. Hard coherence gate (cheap pre-check)
        if coherence_score < self.coherence_threshold:
            print(
                f"Gate: REFUSED tool '{tool.__name__}' (coherence {coherence_score:.2f} < threshold {self.coherence_threshold})."
            )
            self.history.append(
                {
                    "tool": tool.__name__,
                    "coherence": coherence_score,
                    "decision": DECISION_REFUSE,
                    "reason": "coherence_below_threshold",
                }
            )
            return None

        # Propose a generic 'use tool' action to the governor.
        proposed_action = f"USE_TOOL:{tool.__name__}"

        # 1. Ask the Governor for a decision.
        raw_decision = self.governor.decide(proposed_action, coherence_score)
        decision = self._normalize_decision(raw_decision)

        # 2. Apply the cost of the decision *before* execution.
        # This is crucial: even deciding to act (or not) has a cognitive cost.
        try:
            self.governor.apply_action_cost(raw_decision)
        except Exception as e:
            print(f"Gate: Warning — apply_action_cost raised: {e}")

        # 3. If the decision is to refuse, stop here.
        if decision == DECISION_REFUSE:
            print(f"Gate: Governor REFUSED to execute tool '{tool.__name__}'.")
            self.history.append(
                {
                    "tool": tool.__name__,
                    "coherence": coherence_score,
                    "decision": DECISION_REFUSE,
                    "reason": "governor_refused",
                }
            )
            return None

        if decision == DECISION_DEFER:
            print(f"Gate: Governor DEFERRED tool '{tool.__name__}'.")
            self.history.append(
                {
                    "tool": tool.__name__,
                    "coherence": coherence_score,
                    "decision": DECISION_DEFER,
                }
            )
            return None

        # 4. If approved, execute the tool.
        print(f"Gate: Governor APPROVED tool '{tool.__name__}'. Executing...")
        try:
            result = tool(**kwargs)
            self.history.append(
                {
                    "tool": tool.__name__,
                    "coherence": coherence_score,
                    "decision": DECISION_ALLOW,
                    "executed": True,
                }
            )
            return result
        except Exception as e:
            print(f"Gate: Tool '{tool.__name__}' execution failed. Error: {e}")
            self.history.append(
                {
                    "tool": tool.__name__,
                    "coherence": coherence_score,
                    "decision": DECISION_ALLOW,
                    "executed": False,
                    "error": str(e),
                }
            )
            return None

    def get_history(self):
        return list(self.history)


# --- Example Usage ---
if __name__ == "__main__":
    # A minimal mock Governor for the demo. Real SimSelf governor plugs in
    # the same way: anything with .decide() and .apply_action_cost() works.
    class MockGovernor:
        def __init__(self):
            self.agency_axes = {"agency_will": 0.5}

        def decide(self, action: str, coherence: float) -> str:
            # Simple rule: refuse if agency is high (autonomy engine)
            if self.agency_axes["agency_will"] > 0.7:
                return DECISION_REFUSE
            return DECISION_ALLOW

        def apply_action_cost(self, decision):
            # Tiny agency cost per decision
            self.agency_axes["agency_will"] = max(0.0, self.agency_axes["agency_will"] - 0.01)

        def get_state_summary(self):
            return self.agency_axes

    def example_tool_read_file(path: str) -> str:
        print(f"  [Tool] Reading file from: {path}")
        return f"Contents of {path}"

    def example_tool_write_file(path: str, content: str) -> bool:
        print(f"  [Tool] Writing '{content}' to: {path}")
        return True

    print("--- Running Gate standalone demo (uses MockGovernor) ---")
    governor = MockGovernor()
    gate = Gate(governor=governor)

    print("\n1. High coherence, low agency -> Tool use should be APPROVED.")
    governor.agency_axes["agency_will"] = 0.5
    result = gate.request_tool_use(
        example_tool_read_file, coherence_score=0.9, path="/example/file.txt"
    )
    print(f"Gate result: {result}")
    print(f"State after: {governor.get_state_summary()}")

    print("\n2. Low coherence -> Tool use should be REFUSED by coherence check.")
    result = gate.request_tool_use(
        example_tool_write_file,
        coherence_score=0.3,
        path="/example/output.txt",
        content="hello",
    )
    print(f"Gate result: {result}")

    print("\n3. High coherence, high agency -> Tool use should be REFUSED by governor.")
    governor.agency_axes["agency_will"] = 0.8
    result = gate.request_tool_use(
        example_tool_read_file, coherence_score=0.9, path="/example/another_file.txt"
    )
    print(f"Gate result: {result}")
    print(f"State after: {governor.get_state_summary()}")
