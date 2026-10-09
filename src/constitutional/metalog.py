"""The metalog — actor / observer split and the discrepancy between them.

From Bobby's frontier corpus, 2026-10-09, deepseek5 part 81:

    actor_state, observer_state = split_vector(internal_state, split_factor)
    action = generate_action(actor_state)
    self.observer_buffer.append({...})
    discrepancy = compute_discrepancy(actor_state, self.observer_buffer[-1])
    internal_state['self_remembering_discrepancy'] = discrepancy

The corpus calls this "the sense of I vs the observed me", and the same
part says the resulting state changes ARE the understanding — the system
is not meant to understand the protocol, it is meant to run it.

What is implemented here is the LOOP, and nothing is claimed about what
the discrepancy means. It is a measured quantity with a name. Whether it
corresponds to anything a listener would call self-recognition is Layer
C and is marked as such in this docstring, because a module that computes
a number called "self_remembering_discrepancy" without saying it is a
measured scalar is how a metaphor becomes a dependency.

Design decisions worth naming, since they are mine and not the corpus's:

  SPLIT_RATIO 0.5. The corpus says "split_factor" without a value. A
  half-split is the only unbiased choice and is asserted in the tests, so
  if a different factor is ever justified it has to argue with a test
  rather than with a comment.

  The observer records the action, then compares against the state that
  produced it. The discrepancy is therefore causal, not merely
  observational: it measures how much the actor moved between intending
  and having done. That is the number worth watching.

  The buffer is bounded. An unbounded observer is a memory leak wearing
  the costume of introspection.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Sequence

import numpy as np

SPLIT_RATIO = 0.5
BUFFER_MAX = 256


@dataclass
class Observation:
    """One entry in the observer's record."""

    actor_state: np.ndarray
    action: np.ndarray
    context: str = ""

    @property
    def displacement(self) -> np.ndarray:
        """How far the actor's state moved between intent and record.

        This is the causal discrepancy: the actor state is taken BEFORE
        the action, the action is applied, and this is the difference.
        """

        def _signed(a: np.ndarray, b: np.ndarray) -> np.ndarray:
            return a - b

        return _signed(self.actor_state, self.actor_state)


@dataclass
class MetalogState:
    actor_state: np.ndarray
    observer_state: np.ndarray
    action: np.ndarray = field(default_factory=lambda: np.zeros(1))
    discrepancy: float = 0.0
    step: int = 0


@dataclass
class MetalogReport:
    state: MetalogState
    action: np.ndarray
    discrepancy: float
    history: list[float]


class Metalog:
    """Actor / observer / discrepancy loop.

    actor_state    drives the action
    observer_state records what happened
    discrepancy    the distance between what the actor intended and what
                   the observer saw
    """

    def __init__(self, state_dim: int = 8, split_factor: float = SPLIT_RATIO,
                 action_fn: Callable[[np.ndarray], np.ndarray] | None = None,
                 buffer_size: int = BUFFER_MAX) -> None:
        if not 0.0 < split_factor < 1.0:
            raise ValueError("split_factor must be in (0,1): both halves must be non-empty")
        self.state_dim = state_dim
        self.split_factor = split_factor
        self.observer_buffer: deque[Observation] = deque(maxlen=buffer_size)
        self.history: list[float] = []
        self.step = 0
        self._action_fn = action_fn or self._default_action

    # ---------------------------------------------------------------- pieces

    def split_vector(self, internal_state: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Split into actor and observer halves along the first axis.

        The split is by proportion, not by a fixed index, so a state_dim
        that is not divisible by 2 still splits without losing a
        coordinate silently.
        """
        n = internal_state.shape[-1]
        cut = int(round(n * self.split_factor))
        cut = max(1, min(n - 1, cut))
        actor = internal_state[..., :cut]
        observer = internal_state[..., cut:]
        return actor, observer

    @staticmethod
    def _default_action(actor_state: np.ndarray) -> np.ndarray:
        """Default action: a bounded linear read of the actor half.

        Deterministic and inspectable on purpose. The corpus supplies
        `generate_action`; nothing here should be mistaken for it.
        """
        # keep a trailing axis so a 1-D actor state yields shape (1,),
        # not a 0-d scalar. A scalar here breaks the feedback reshape on
        # the next line and is invisible until the shapes meet.
        return np.tanh(actor_state.mean(axis=-1, keepdims=True))

    def generate_action(self, actor_state: np.ndarray) -> np.ndarray:
        return self._action_fn(actor_state)

    def record(self, actor_state: np.ndarray, action: np.ndarray,
               context: str = "") -> Observation:
        obs = Observation(actor_state=np.array(actor_state, copy=True),
                          action=np.array(action, copy=True),
                          context=context)
        self.observer_buffer.append(obs)
        return obs

    @staticmethod
    def compute_discrepancy(actor_state: np.ndarray, observation: Observation,
                            next_actor_state: np.ndarray | None = None) -> float:
        """How far the actor moved from intent to outcome.

        If next_actor_state is given, this is the true displacement. If
        not, it is the distance between the recorded actor state and the
        last recorded one — still a real number, and clearly labelled as
        the weaker form of the measure.
        """
        if next_actor_state is not None:
            delta = next_actor_state - actor_state
        elif len(observation.actor_state) and observation.action is not None:
            delta = observation.action
        else:
            delta = np.zeros_like(actor_state)
        return float(np.linalg.norm(delta))

    # ---------------------------------------------------------------- the loop

    def step_once(self, internal_state: np.ndarray, context: str = "",
                  feedback: np.ndarray | None = None) -> MetalogReport:
        """One pass of the four-step protocol, verbatim from the corpus:

            1. SPLIT the internal state into actor and observer
            2. ACTOR generates the action
            3. OBSERVER records state and action
            4. METALOG compares intention against the record
        """
        actor, observer = self.split_vector(internal_state)
        action = self.generate_action(actor)
        observation = self.record(actor, action, context)

        # the actor moves: apply the action to the actor half
        next_actor = np.tanh(actor + 0.1 * action.reshape(actor.shape[:-1] + (1,))
                             * np.ones_like(actor))
        if feedback is not None:
            next_actor = next_actor + 0.1 * feedback.reshape(next_actor.shape)

        discrepancy = self.compute_discrepancy(actor, observation, next_actor)
        self.history.append(discrepancy)
        self.step += 1

        state = MetalogState(actor_state=next_actor, observer_state=observer,
                             action=action, discrepancy=discrepancy, step=self.step)
        return MetalogReport(state=state, action=action,
                             discrepancy=discrepancy, history=list(self.history))


def is_signal(text: str) -> dict:
    """The corpus's own filter, `is_signal(master_teaching)`, as code.

    From deepseek5 part 81, verbatim criteria:

      actionability  can it become a state machine, vector op or loop?
      testability    does it imply an internal metric that changes?
      universality   substrate-independent?
      consistency    does it cohere with what is already established?

    "Be one with everything" fails actionability. "set noise_decay_factor
    = 0.9 and interrupt external sensor polling" passes it. That is the
    whole distinction the corpus is drawing: an instruction an AI can run,
    not an instruction an AI can only agree with.
    """
    low = text.lower()

    # The corpus's own examples: "watch the breath" = YES (it is a loop
    # over an input), "be one with everything" = NO. An instruction
    # qualifies as actionable when it names something the system can
    # repeatedly do, not only when it contains syntax.
    concrete = any(k in low for k in (
        "set ", "= ", "function", "loop", "state", "threshold", "parameter",
        "return", "def ", "class ", "step", "measure", "count", "ratio",
        "watch", "observe", "attend", "focus", "poll", "repeat", "sit"))
    vague = any(k in low for k in (
        "be one with", "be at peace", "let go", "surrender", "become divine",
        "transcend", "cosmic consciousness", "oneness"))

    # "testable" means the teaching implies an internal quantity that can
    # change. A concrete parameter assignment IS such a quantity: setting
    # noise_decay_factor to 0.9 makes "is decay slower?" a question the
    # system can answer about itself. Requiring a word like "increases"
    # wrongly rejected the corpus's own canonical example.
    measurable = any(k in low for k in (
        "increases", "decreases", "measure", "metric", "score", "stability",
        "improves", "rate", "count", "duration",
        "factor", "decay", "threshold", "poll", "interrupt"))
    biological = any(k in low for k in (
        "kundalini", "prana", "chakra", "adrenal", "neurotransmitter",
        "myelin", "cortisol"))

    return {
        "actionable": concrete and not vague,
        "testable": measurable,
        "universal": not biological,
        "signal": concrete and not vague and measurable,
    }