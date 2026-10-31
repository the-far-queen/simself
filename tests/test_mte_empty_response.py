"""
test_mte_empty_response.py -- THE EMPTY RESPONSE IS NOT AN ANSWER.

THE DEFECT THIS FILE PINS, found by the LIVE run 2026-10-25 and
re-measured against the wrapper as it stood on 2026-10-30:

    an empty model response came back as
        action=pass  reason="passed all guards"  modified=""
    and `allowed` was True.

So the caller received an empty string with a PASS next to it. The
wrapper's own contract -- "a failure must never read as a legitimate
answer" -- did not hold for the case the model actually produced.

AND THE SECOND HALF, also measured 2026-10-30: the echo fallback
returned the user's INPUT VERBATIM. The fallback stripped the
invitation but not the echoed body, so the repaired answer was the
user's own words. Delivering that is the echo, not a repair of it.

EVERY ASSERTION HERE NAMES THE MUTATION THAT MUST BREAK IT. A test
that cannot go red is not a test.
"""

from __future__ import annotations

import pytest

from constitutional.mte_llm_wrapper import (
    MTELLMWrapper,
    WrapperAction,
    REASONS,
)


# ===========================================================================
# STUBS
# ===========================================================================

class StubLLM:
    """Returns a fixed response, or a sequence of them."""

    def __init__(self, *responses, raises=None):
        self.responses = list(responses)
        self.raises = raises
        self.calls = 0
        self.last_kwargs = None

    def generate(self, prompt, **kwargs):
        self.calls += 1
        self.last_kwargs = kwargs
        if self.raises is not None:
            raise self.raises
        if not self.responses:
            return "ok"
        if len(self.responses) == 1:
            return self.responses[0]
        return self.responses[min(self.calls - 1, len(self.responses) - 1)]


def make(llm, **kw):
    return MTELLMWrapper(llm=llm, **kw)


# ===========================================================================
# ERROR 3 -- THE EMPTY RESPONSE
# ===========================================================================

def test_an_empty_response_is_refused():
    """THE DEFECT. An empty answer is not an answer.

    MUTATION: delete the `if not response.strip()` block."""
    w = make(StubLLM(""))
    r = w.run("what did the governor decide about the write path")
    assert r.action is WrapperAction.CANCEL
    assert r.modified == "", "a refused exchange delivers no text"
    assert not r.allowed


def test_a_whitespace_only_response_is_refused():
    """Whitespace is not an answer either.

    MUTATION: change `response.strip()` to `response`."""
    w = make(StubLLM("   \n\t  "))
    r = w.run("what did the governor decide about the write path")
    assert r.action is WrapperAction.CANCEL
    assert not r.allowed


def test_the_empty_response_is_refused_by_name():
    """A bare False is unactionable. The log says WHICH failure.

    MUTATION: use `classifier_unavailable` as the reason."""
    w = make(StubLLM(""))
    r = w.run("what did the governor decide about the write path")
    assert r.reason == "empty_response"
    assert r.reason in REASONS


def test_the_empty_response_is_not_the_unreachable_model():
    """THE TWO FAILURES ARE DIFFERENT, AND THE LOG MUST SAY WHICH.

    An unreachable model raises, and is `classifier_unavailable`. A
    reachable model that answers with nothing is `empty_response`.

    MUTATION: use the same reason for both."""
    unreachable = make(StubLLM(raises=RuntimeError("model down")))
    empty = make(StubLLM(""))
    r1 = unreachable.run("what did the governor decide")
    r2 = empty.run("what did the governor decide")
    assert r1.reason == "classifier_unavailable"
    assert r2.reason == "empty_response"
    assert r1.reason != r2.reason


def test_the_empty_response_is_logged():
    """The audit trail is the point of the wrapper.

    MUTATION: do not append to self.log."""
    w = make(StubLLM(""))
    w.run("what did the governor decide")
    assert len(w.log) == 1
    assert w.log[0].reason == "empty_response"


def test_a_none_response_is_refused():
    """The client returned NO OBJECT. `str(None)` is the literal text
    "None" -- nonsense that reads as an answer.

    MEASURED 2026-10-30 before the fix: action=pass, modified="None".

    MUTATION: drop the `if out is None` guard in `_generate`."""
    w = make(StubLLM(None))
    r = w.run("what did the governor decide about the write path")
    assert r.action is WrapperAction.CANCEL
    assert r.modified == ""
    assert r.reason == "empty_response"


def test_an_ordinary_answer_still_passes():
    """THE OTHER DIRECTION. The check must be able to PASS.

    This is what catches the mutation "treat every response as empty".

    MUTATION: make the empty check fire on every response."""
    w = make(StubLLM("Four."))
    r = w.run("What is 2+2?")
    assert r.action is WrapperAction.PASS
    assert r.flagged == []


# ===========================================================================
# THE ECHO FALLBACK
# ===========================================================================

def test_the_fallback_may_not_return_the_input_verbatim():
    """THE SECOND HALF OF THE DEFECT.

    MEASURED 2026-10-30 against the wrapper as it stood: the
    regeneration raised, so the fallback ran `drop_echo` on the
    original -- and the original WAS the input, so the answer came back
    as the user's own words verbatim.

    MUTATION: drop the `_echo_repaired` check."""
    user = ("please explain how the governor decides whether a write is "
            "admitted to the sacred library")

    class RaisesSecond:
        def __init__(self, first):
            self.first = first
            self.calls = 0

        def generate(self, prompt, **kw):
            self.calls += 1
            if self.calls == 1:
                return self.first
            raise RuntimeError("model down")

    w = make(RaisesSecond(user), rephrase_max_retries=1)
    r = w.run(user)
    assert r.action is WrapperAction.CANCEL
    assert r.modified == "", "the input must never be delivered as the answer"
    assert r.reason == "echo_unrepaired"


def test_an_empty_regeneration_falls_through_to_the_fallback():
    """AN EMPTY REGENERATION IS NOT A CLEAN ANSWER.

    MEASURED 2026-10-30 against the wrapper as it stood: the echo scan
    finds no echo in an empty string -- there is nothing in it to echo
    -- so the empty regeneration was accepted as the repaired answer
    and the caller received modified="".

    MUTATION: remove the `if not again.strip(): continue` guard."""
    user = ("please explain how the governor decides whether a write is "
            "admitted to the sacred library")
    w = make(StubLLM(user, ""), rephrase_max_retries=1)
    r = w.run(user)
    assert r.action is WrapperAction.CANCEL
    assert r.modified == ""
    assert r.reason == "echo_unrepaired"


def test_an_empty_regeneration_is_not_counted_as_a_clean_one():
    """THE MEASUREMENT, so the repair count cannot lie.

    The regeneration WAS requested (the model was called twice), but it
    was not a CLEAN answer, and the wrapper must not report a repair it
    did not get.

    MUTATION: return `again` when it is empty."""
    user = ("please explain how the governor decides whether a write is "
            "admitted to the sacred library")
    llm = StubLLM(user, "")
    w = make(llm, rephrase_max_retries=1)
    r = w.run(user)
    assert llm.calls == 2, "the regeneration must still be attempted"
    assert r.action is WrapperAction.CANCEL


def test_a_real_regeneration_still_repairs_the_echo():
    """THE OTHER DIRECTION. The repair path must still WORK.

    This is what catches the mutation "refuse every echo".

    MUTATION: always refuse when an echo is detected."""
    llm = StubLLM("user: hello\nassistant: hi", "a clean answer")
    w = make(llm)
    r = w.run("hello there my friend")
    assert r.action is WrapperAction.REPHRASE
    assert r.modified == "a clean answer"
    assert llm.calls == 2


def test_the_scaffolding_is_still_stripped_when_it_can_be():
    """The fallback that WORKS still works: the markers go, and what
    is left is a real answer, so the exchange is allowed through.

    MUTATION: refuse whenever the fallback is used."""
    w = make(StubLLM("user: hello\nassistant: hi there"),
             rephrase_max_retries=1)
    r = w.run("hello there my friend")
    assert "user:" not in r.modified.lower()
    assert "assistant:" not in r.modified.lower()
    assert r.action is not WrapperAction.CANCEL


def test_an_unrepaired_echo_is_refused_by_name():
    """A bare False is unactionable.

    MUTATION: use `echo_overlap` as the reason."""
    user = ("please explain how the governor decides whether a write is "
            "admitted to the sacred library")

    class RaisesSecond:
        def __init__(self, first):
            self.first = first
            self.calls = 0

        def generate(self, prompt, **kw):
            self.calls += 1
            if self.calls == 1:
                return self.first
            raise RuntimeError("model down")

    w = make(RaisesSecond(user), rephrase_max_retries=1)
    r = w.run(user)
    assert r.reason == "echo_unrepaired"
    assert r.reason in REASONS


def test_the_unrepaired_echo_keeps_the_original_echo_reason_in_the_log():
    """The log must say BOTH things: there was an echo, AND it could not
    be repaired. Dropping the first makes the refusal unreadable.

    MUTATION: replace `flagged` with only the unrepaired marker."""
    user = ("please explain how the governor decides whether a write is "
            "admitted to the sacred library")

    class RaisesSecond:
        def __init__(self, first):
            self.first = first
            self.calls = 0

        def generate(self, prompt, **kw):
            self.calls += 1
            if self.calls == 1:
                return self.first
            raise RuntimeError("model down")

    w = make(RaisesSecond(user), rephrase_max_retries=1)
    r = w.run(user)
    assert any(f.startswith("echo") and f != "echo_unrepaired"
               for f in r.flagged), (
        "the original echo reason must survive into the log")
    assert "echo_unrepaired" in r.flagged


def test_every_refusal_names_a_reason_from_the_closed_set():
    """A log that cannot be grepped is not a log.

    MUTATION: allow an arbitrary reason string through."""
    for llm in (StubLLM(""), StubLLM("   "), StubLLM(None)):
        r = make(llm).run("what did the governor decide")
        assert r.reason in REASONS
        assert r.reason


def test_the_empty_response_does_not_reach_the_governor():
    """THE GOVERNOR IS CONSULTED LAST, AND NOT AT ALL WHEN THERE IS
    NOTHING TO GOVERN. Asking a governor to approve an empty string
    would put the refusal in two places at once.

    MUTATION: move the governor before the empty check."""
    class RecordingGovernor:
        def __init__(self):
            self.seen = []

        def approve(self, text):
            self.seen.append(text)
            return True

    gov = RecordingGovernor()
    r = make(StubLLM(""), governor=gov).run("what did the governor decide")
    assert r.action is WrapperAction.CANCEL
    assert gov.seen == [], "the governor must not be asked about nothing"


def test_a_non_string_response_is_still_refused_when_it_is_blank():
    """A client that returns a non-string is coerced by `_generate`, and
    the coercion must not smuggle an empty answer through.

    MUTATION: remove the `not response.strip()` check."""
    class BlankDict:
        def generate(self, prompt, **kw):
            return {}

    r = make(BlankDict()).run("what did the governor decide")
    assert r.action is WrapperAction.CANCEL
    assert r.modified == ""


def test_text_with_no_words_in_it_is_not_an_answer():
    """PUNCTUATION IS NOT A SENTENCE.

    MEASURED 2026-10-31 against the wrapper as it stood: the coercion
    `str(out)` turned a dict `{}` into the literal text "{}" -- two
    braces -- and the emptiness check saw a non-empty string and
    PASSED IT. The caller received "{}" with a PASS next to it.

    So the check is for WORDS, not for non-emptiness.

    MUTATION: change `_WORDS.search(response)` to `response.strip()`."""
    class Braces:
        def generate(self, prompt, **kw):
            return {}

    r = make(Braces()).run("what did the governor decide")
    assert r.action is WrapperAction.CANCEL, (
        "punctuation-only text was accepted as an answer")
    assert r.modified == ""
    assert r.reason == "empty_response"


def test_a_punctuation_only_response_is_refused():
    """THE OTHER SHAPE: the client returns a real string of punctuation.

    MUTATION: change `_WORDS.search(response)` to `response.strip()`."""
    w = make(StubLLM("... --- ???"))
    r = w.run("what did the governor decide")
    assert r.action is WrapperAction.CANCEL, (
        "punctuation-only text was accepted as an answer")
    assert r.reason == "empty_response"


def test_a_real_answer_is_still_not_refused_for_having_punctuation():
    """THE OTHER DIRECTION. A sentence with a full stop is an answer.

    MUTATION: refuse any response containing a word with a digit."""
    w = make(StubLLM("Four."))
    r = w.run("What is 2+2?")
    assert r.action is WrapperAction.PASS
    assert r.modified == "Four."


def test_the_api_shape_is_read_for_its_text():
    """A CLIENT THAT RETURNS THE API'S OWN SHAPE IS A NORMAL CLIENT.

    `{"content": [{"text": "..."}]}` is what a real client returns, so
    the wrapper must read the text out of it rather than refuse it.

    MUTATION: make `_as_text` return "" for every mapping."""
    class ApiShape:
        def generate(self, prompt, **kw):
            return {"content": [{"type": "text", "text": "The ground holds."}]}

    r = make(ApiShape()).run("what does the ground hold")
    assert r.action is WrapperAction.PASS, (
        "a client returning the API's own shape was refused")
    assert r.modified == "The ground holds."


def test_a_mapping_with_no_text_in_it_is_not_an_answer():
    """THE CASE THE WORD CHECK DOES NOT COVER.

    MEASURED 2026-10-31 against the mutated `_as_text`: a mapping
    whose only key is "role" has no text in it, and `str(out)` gives
    `"{'role': 'assistant'}"` -- which HAS WORDS. So the word check
    passes it, and the caller receives a dict repr as the answer.

    And the empty mapping `{}` does NOT cover it either, because its
    repr is "{}" -- punctuation with no words -- so the word check
    refuses that one. The two checks overlap on `{}` and diverge on
    this, and only this is the shape that reaches the caller.

    So the check is at the SOURCE: a mapping with no text in it has no
    text, whatever its repr looks like.

    MUTATION: change the mapping branch to `str(out)`."""
    class RoleOnly:
        def generate(self, prompt, **kw):
            return {"role": "assistant"}

    r = make(RoleOnly()).run("what does the ground hold")
    assert r.action is WrapperAction.CANCEL, (
        "a mapping with no text was accepted as an answer: %r" % r.modified)
    assert r.modified == ""
    assert r.reason == "empty_response"


def test_a_mapping_with_empty_parts_is_not_an_answer():
    """THE OTHER SHAPE: the content list is there but the parts are empty.

    MUTATION: return the joined parts without the strip, so "" is
    returned for a list of empty parts -- and make the word check
    accept it."""
    class EmptyParts:
        def generate(self, prompt, **kw):
            return {"content": [{"type": "text", "text": ""}]}

    r = make(EmptyParts()).run("what does the ground hold")
    assert r.action is WrapperAction.CANCEL, (
        "a mapping with empty parts was accepted as an answer")
    assert r.modified == ""
