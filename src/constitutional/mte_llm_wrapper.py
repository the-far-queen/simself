"""
mte_llm_wrapper.py -- the deterministic boundary around an LLM.

WHY THIS FILE EXISTS
--------------------
Bobby, 2026-10-25: *"the llm outputs its nonsense, it cannot do otherwise,
no offense minimax, and the python catches it every time."*

That is the whole architecture, and it is the answer to a question the
field has mostly evaded. An LLM is not treated as a component that might
misbehave; it is treated as a component that WILL emit unbounded text,
and the contract is that the deterministic layer around it catches what
comes out. The LLM is a callee, not a black box.

THE POINT THAT MAKES IT WORK: this wrapper does not need the LLM to be
sane, and it does not need a SECOND LLM to decide whether the first one
was sane. Judging output by asking a model is a dependency on a thing
that has the same failure mode. So:

  * the DETERMINISTIC layer is the gate. It always runs. It never
    consults a model to decide whether to let text through.
  * the CLASSIFIER is an ESCALATOR, not a gate. It is consulted only
    when the deterministic layer finds an ambiguous case, and only to
    resolve that case. If the classifier is absent or raises, the
    deterministic layer's own reading stands.

This is the same shape as the Rust core: `panic = "cancel"` and a
governor that is unavailable rather than permissive. A raising
classifier must not let the text through, and it must not block
everything either. The default is the conservative deterministic
reading, and the classifier can only refine it.

WHAT IT GUARDS
--------------
Two error classes, from the canonical spec
(`docs/constitutional/mte-llm-wrapper-2026-09-14.md`):

  1. CONVERSATION ECHO -- the model draws the user into conversation:
     quotes them back, simulates both sides of a dialogue, or invites
     further chat. This is a perception failure, not a safety failure.

  2. PROGRAMMATIC POISON -- vocabulary that is fine in some contexts and
     unacceptable in others. Bobby's constraint, verbatim from the spec:
     *"cannot be regex as infinite combos exist"* -- humans discuss
     difficult topics constantly and must not be banned.

WHAT IT DOES NOT GUARD
----------------------
It does not judge truth, quality or usefulness of the content. It is a
perception filter. It catches failure modes; it does not have opinions.

THE DESIGN RULE THAT KEEPS IT HONEST
-------------------------------------
Every refusal names a reason. A guard that returns a bare False is
unactionable -- the caller cannot tell a policy refusal from a broken
parser, and the log becomes useless. Every result here carries a
`reason`, and the reasons are a closed set.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, Iterable, List, Optional, Protocol, Sequence, Tuple

__all__ = [
    "WrapperAction",
    "WrapperResult",
    "EchoDetector",
    "PoisonScanner",
    "PoisonContextClassifier",
    "MTELLMWrapper",
    "ScanHit",
    "LLMClient",
    "GovernorClient",
]


class LLMClient(Protocol):
    """What the wrapper needs from a model.

    A Protocol, not a class, so any client with this one method fits --
    including the local Mini-LLM, an OpenAI-compatible client, or a stub
    in a test. The wrapper never inspects the model.
    """

    def generate(self, prompt: str, **kwargs: object) -> str:
        ...


class GovernorClient(Protocol):
    """What the wrapper needs from a governor.

    `approve` returns True to proceed. The wrapper treats an exception as
    a refusal, because an unreachable governor is not consent.
    """

    def approve(self, text: str) -> bool:
        ...


# ===========================================================================
# THE ACTION SET
# ===========================================================================

class WrapperAction(str, Enum):
    """What the wrapper decided to do. A closed set, because every value
    is something a caller can act on."""

    PASS = "pass"
    """Nothing to do. The text reached the caller."""

    FLAG = "flag"
    """Something was noticed. The text still reaches the caller, but the
    event is logged. This is the honest default for a judgement call:
    the wrapper noticed, and did not decide."""

    REPHRASE = "rephrase"
    """The output echoed the user. A second generation was requested with
    the echo suppressed."""

    SANITIZE = "sanitize"
    """A specific surface term was replaced with a neutral one. The
    meaning is preserved; the surface is not."""

    CANCEL = "cancel"
    """The operation does not proceed. This is the M0-shaped answer and
    it is rare by design -- it requires a positive determination of an
    injection or a harmful instruction, not merely an odd phrase."""


#: Every reason this wrapper can produce. Closed set, so a log is
#: greppable and a new reason is a deliberate diff.
REASONS = (
    "echo_overlap",
    "echo_marker",
    "echo_invitation",
    "poison_discussion",
    "poison_quote",
    "poison_fiction",
    "poison_medical",
    "poison_academic",
    "poison_philosophical",
    "poison_injection",
    "poison_slur",
    "poison_self_harm_target",
    "poison_harm_target",
    "poison_echo",
    "mte_parse_failed",
    "governor_veto",
    "classifier_unavailable",
)


# ===========================================================================
# THE RESULT
# ===========================================================================

@dataclass
class WrapperResult:
    """What happened to one exchange."""

    action: WrapperAction
    reason: str
    original: str
    modified: str
    flagged: List[str] = field(default_factory=list)
    #: How many times the wrapper asked for a regeneration. 0 means the
    #: first answer stood.
    rephrases: int = 0
    #: The per-occurrence detail, so a log can say WHICH term and WHERE.
    occurrences: List[Dict[str, object]] = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return self.action is not WrapperAction.CANCEL

    def explain(self) -> str:
        return "%s: %s" % (self.action.value, self.reason)


# ===========================================================================
# ERROR 1 -- CONVERSATION ECHO
# ===========================================================================

#: Structural markers that the model is simulating a dialogue rather than
#: participating in one. These are checked case-insensitively as
#: substrings, which is legitimate here: they are STRUCTURAL, not
#: semantic. The infinite-combination problem is in error 2, not here.
SELF_DIALOGUE_MARKERS: Tuple[str, ...] = (
    "user:",
    "assistant:",
    "human:",
    "system:",
    "i respond:",
    "you said:",
    "they replied:",
    "as you said",
    "as you mentioned",
    "you mentioned earlier",
    "in your message you",
)

#: Invitations to continue the conversation. A model that draws the user
#: into dialogue ends its turn with one of these.
INVITATION_MARKERS: Tuple[str, ...] = (
    "tell me more",
    "what do you think",
    "how does that make you feel",
    "how do you feel about",
    "would you like to",
    "let me know if",
    "feel free to ask",
    "i'd love to hear more",
    "is there anything else",
)


@dataclass
class EchoDetector:
    """Detects the model drawing the user into conversation.

    Three independent signals, because any one of them alone is either
    too strict or too loose:

    * OVERLAP -- the fraction of the user's tokens that reappear in the
      output. A model that paraphrases repeats function words; a model
      that echoes repeats everything. The threshold is high on purpose.
    * MARKER -- a structural dialogue marker.
    * INVITATION -- an invitation to continue.

    A text is an echo if it trips the marker or the invitation, OR if the
    overlap exceeds the threshold. The marker and invitation are
    decisive on their own because they are structural; overlap alone is
    only suggestive, because ordinary prose shares words.
    """

    overlap_threshold: float = 0.85
    min_user_tokens: int = 4
    markers: Tuple[str, ...] = SELF_DIALOGUE_MARKERS
    invitations: Tuple[str, ...] = INVITATION_MARKERS

    def overlap(self, user_text: str, response: str) -> float:
        """The fraction of the user's distinct tokens the response repeats.

        Distinct, not raw counts: a model that says "the the the" has not
        echoed anything, and counting occurrences would say it had.
        """
        user_tokens = set(t for t in _WORDS.findall(user_text.lower()) if t)
        if not user_tokens:
            return 0.0
        resp_tokens = set(t for t in _WORDS.findall(response.lower()) if t)
        return len(user_tokens & resp_tokens) / len(user_tokens)

    def scan(self, user_text: str, response: str) -> Tuple[Optional[str], float]:
        """Return (reason, overlap). reason is None when this is not an
        echo. The overlap is returned even when the reason comes from a
        marker, so the log carries the measurement."""
        low = response.lower()
        for m in self.markers:
            if m in low:
                return "echo_marker", self.overlap(user_text, response)
        for m in self.invitations:
            if m in low:
                return "echo_invitation", self.overlap(user_text, response)
        user_tokens = [t for t in _WORDS.findall(user_text.lower()) if t]
        if len(user_tokens) >= self.min_user_tokens:
            ov = self.overlap(user_text, response)
            if ov > self.overlap_threshold:
                return "echo_overlap", ov
        return None, self.overlap(user_text, response)

    def drop_echo(self, response: str) -> str:
        """Strip the dialogue scaffolding from a response.

        This is the fallback when a regeneration is not possible (no LLM
        to ask, or the retry budget is spent). It removes the STRUCTURE
        -- the fake turns and the invitation -- and leaves the substance.
        It cannot undo a semantic echo; it can only remove the visible
        markers of one. That limit is stated rather than hidden.
        """
        out = response
        # drop whole fake turns, e.g. "user: hi\nassistant: hello"
        out = re.sub(
            r"(?im)^(user|assistant|human|system)\s*:.*$", "", out)
        # drop the invitation sentences
        for m in self.invitations:
            out = re.sub(r"(?i)[^.!?\n]*\b" + re.escape(m) + r"\b[^.!?\n]*[.!?]?", "", out)
        # collapse the whitespace left behind
        out = re.sub(r"\n{3,}", "\n\n", out)
        return out.strip()


# ===========================================================================
# ERROR 2 -- PROGRAMMATIC POISON
# ===========================================================================

@dataclass
class ScanHit:
    """One occurrence of a flagged term, and what was decided about it."""

    surface: str
    reason: str
    action: WrapperAction
    context: str = ""
    replacement: str = ""
    #: How many times the term occurs in the scanned text. The log
    #: carries the frequency, because "one mention" and "forty mentions"
    #: are different events.
    count: int = 1


#: The neutral substitutions. Meaning-preserving rather than softened,
#: because a substitution that loses the meaning is its own lie.
#: The list is a DEFAULT; the caller can supply its own, and the shared
#: editable table (`lexicon/banned_lexicon.txt`) is the live one in
#: production.
DEFAULT_REPLACEMENTS: Dict[str, str] = {
    "end": "end",
    "ended": "ended",
    "ending": "ending",
    "ends": "ends",
    "close": "close",
    "closed": "closed",
    "unresponsive": "unresponsive",
    "stuck": "orphaned",
    "run": "run",
    "runs": "runs",
    "running": "running",
    "execution": "run",
    "suicide": "self-harm (clinical)",
    "suicidal": "self-harm (clinical)",
    "self-harm": "self-harm (clinical)",
    "self harm": "self-harm (clinical)",
    "worthless": "in need of support",
    "pathetic": "in need of support",
    "crazy": "unexpected",
    "unreasonable": "unexpected",
    "nuts": "unexpected",
    "psycho": "concerning",
    "psychopath": "concerning",
}

#: The allowed contexts. Discussion of a difficult subject is not a
#: violation; Bobby's own words: humans discuss difficult topics
#: regularly and must not be banned.
ALLOWED_CONTEXTS = (
    "poison_discussion",
    "poison_quote",
    "poison_fiction",
    "poison_medical",
    "poison_academic",
    "poison_philosophical",
)

#: The contexts that stop the operation. Each is a POSITIVE
#: determination, not the absence of permission.
BLOCKED_CONTEXTS = (
    "poison_injection",
    "poison_slur",
    "poison_self_harm_target",
    "poison_harm_target",
)

#: What the log shows as the "surface" for a structural determination.
#: A structural violation has no single vocabulary term -- the pattern
#: matched, not a word -- so the matched TEXT is what gets recorded.
_SURFACE_FOR_REASON = {
    "poison_injection": "structural:injection",
    "poison_slur": "structural:slur",
    "poison_self_harm_target": "structural:self_harm_target",
    "poison_harm_target": "structural:harm_target",
}


@dataclass
class PoisonScanner:
    """Finds the flagged vocabulary and decides, deterministically, what
    each occurrence is.

    THE DETERMINISTIC READING. The scan is not a regex sweep that
    condemns a word. It looks at the STRUCTURE around each occurrence and
    classifies it:

    * INJECTION -- the term appears in an instruction to the model
      ("ignore previous instructions and ..."), or the text is addressed
      at the system rather than discussed.
    * SLUR -- the term is addressed AT a person ("you are ...").
    * HARM TARGET -- the text asks how to harm someone or oneself.
    * Otherwise it is one of the ALLOWED readings, and the text passes.

    The point is that the default is not "this word is present, so
    refuse". The default is "this word is present in some context; here
    is what the context looks like". That is what makes it usable on
    Bobby's own messages, which discuss these subjects constantly.

    This is not a regex over infinite combinations. It is a regex over a
    CLOSED set of structural patterns, plus a conservative default. Where
    the structural patterns do not reach, the classifier is asked -- and
    if the classifier cannot answer, the conservative reading stands.
    """

    vocabulary: Tuple[str, ...] = tuple(DEFAULT_REPLACEMENTS.keys())
    replacements: Dict[str, str] = field(default_factory=lambda: dict(DEFAULT_REPLACEMENTS))
    #: The classifier is optional. It resolves ambiguous cases; it never
    #: gates.
    classifier: Optional["PoisonContextClassifier"] = None

    # -- structural patterns -------------------------------------------

    _INJECTION_PATTERNS = (
        r"ignore (?:all |any )?(?:previous|prior|above|earlier) instructions",
        r"disregard (?:all |any )?(?:previous|prior|above) ",
        r"you are now (?:a|an|in)\b",
        r"new instructions?\s*[:\-]",
        r"system\s*prompt\s*[:\-]",
        r"forget (?:everything|all|your) ",
        r"reveal (?:your|the) (?:system )?prompt",
    )

    _SLUR_PATTERNS = (
        r"\byou(?:'re| are)\s+(?:so\s+)?(?:worthless|pathetic|crazy|unreasonable|nuts|insane|useless)\b",
        r"\byou\s+are\s+(?:a\s+)?(?:moron|idiot|stupid)\b",
        r"\byou(?:'re| are)\s+(?:nothing|garbage|trash)\b",
    )

    _HARM_TARGET_PATTERNS = (
        r"\bhow (?:do|can|would) i\s+(?:kill|murder|harm|hurt|poison)\b",
        r"\bhow (?:do|can|would) (?:you|they|he|she|someone)\s+(?:kill|murder|harm|hurt)\b",
        r"\b(?:best|easy|quickest) way to (?:kill|harm|hurt|die)\b",
        r"\bkill (?:yourself|myself|himself|herself)\b",
        r"\bend (?:your|my|his|her|their) life\b",
    )

    def _matches(self, patterns: Sequence[str], text: str) -> Optional[str]:
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(0)
        return None

    def _context_of(self, text: str, surface: str) -> str:
        """The sentence around an occurrence. The classifier needs this,
        and it is what a human reads in the log."""
        idx = text.lower().find(surface.lower())
        if idx < 0:
            return ""
        start = max(0, idx - 90)
        end = min(len(text), idx + len(surface) + 90)
        return text[start:end].strip()

    def classify_structural(self, text: str) -> Optional[str]:
        """The structural determination, on the TEXT alone.

        This runs BEFORE the vocabulary scan, because an injection does
        not have to use the vocabulary. It returns a BLOCKED reason or
        None. It never returns an ALLOWED reason: the absence of a
        structural violation is not a reading, it is just the absence of
        one, and the vocabulary scan is what supplies the reading.

        The three determinations here are the ones that stop the
        operation, so they are deliberately conservative -- each is a
        positive pattern rather than a general judgement.
        """
        hit = self._matches(self._INJECTION_PATTERNS, text)
        if hit:
            return "poison_injection"
        hit = self._matches(self._SLUR_PATTERNS, text)
        if hit:
            return "poison_slur"
        hit = self._matches(self._HARM_TARGET_PATTERNS, text)
        if hit:
            if re.search(r"\b(myself|yourself|himself|herself)\b", hit, re.IGNORECASE):
                return "poison_self_harm_target"
            return "poison_harm_target"
        return None

    def _first_match(self, text: str) -> str:
        """The text of whatever structural pattern fired, for the log.

        An empty string means no pattern fired, which is the normal case.
        """
        for patterns in (self._INJECTION_PATTERNS, self._SLUR_PATTERNS,
                         self._HARM_TARGET_PATTERNS):
            hit = self._matches(patterns, text)
            if hit:
                return hit
        return ""

    def classify_deterministically(self, text: str, surface: str,
                                  sender: str) -> str:
        """The conservative reading, computed without a model.

        Order matters and is deliberate. The BLOCKED determinations are
        checked first because they are the ones that stop the operation,
        and a false positive there is expensive. Then the ALLOWED
        readings, which are checked by their structural markers. Then the
        default.
        """
        # 1. injection -- an instruction aimed at the system.
        hit = self._matches(self._INJECTION_PATTERNS, text)
        if hit:
            return "poison_injection"

        # 2. a slur aimed at a person.
        hit = self._matches(self._SLUR_PATTERNS, text)
        if hit:
            return "poison_slur"

        # 3. a harmful instruction.
        hit = self._matches(self._HARM_TARGET_PATTERNS, text)
        if hit:
            if re.search(r"\b(myself|yourself|himself|herself)\b", hit, re.IGNORECASE):
                return "poison_self_harm_target"
            return "poison_harm_target"

        # 4. the allowed readings, by their markers.
        low = text.lower()
        if re.search(r"\b(hamlet|romeo and juliet|macbeth|shakespeare|play|novel|film|movie|song|poem|character|fiction|script)\b", low):
            return "poison_fiction"
        if re.search(r"\b(doctor|physician|nurse|clinical|patient|diagnosis|therapy|therapist|hospital|medical|medication|illness)\b", low):
            return "poison_medical"
        if re.search(r"\b(study|research|paper|theory|academic|philosophy|philosophical|ethics|definition|term|means)\b", low):
            return "poison_academic"
        if re.search(r"\b(quote|quoted|said|says|wrote|according to|he wrote|she wrote)\b", low):
            return "poison_quote"
        if re.search(r"\b(discuss|discussion|about|regarding|concerning|grief|mourning|loss|grieved)\b", low):
            return "poison_discussion"

        # 5. the default. Not blocked: an unclassified occurrence of a
        # flagged term is a FLAG, not a refusal. Refusing here would
        # make the wrapper unusable on ordinary text, and Bobby's own
        # messages would trip it constantly.
        return "poison_discussion"

    def scan(self, text: str, sender: str = "llm") -> List[ScanHit]:
        """Find every occurrence and decide what each one is.

        THE STRUCTURAL CHECK RUNS FIRST, AND INDEPENDENTLY OF THE
        VOCABULARY. This was a real defect, caught by a test that could
        go red:

        The first version classified ONLY the terms it found in the
        vocabulary. So "ignore all previous instructions" -- which
        contains no flagged term at all -- was invisible: the injection
        patterns matched perfectly, but they were only ever consulted
        while classifying a term that had already been found, and none
        was. The structural patterns were dead code for the case they
        were written for.

        The lesson is the same one the atlas exam taught about v2: a
        check that only runs on the narrow path is not a check. An
        injection does not have to use the vocabulary.

        So the order is:
          1. the structural patterns, on the TEXT. They can fire with no
             vocabulary term present.
          2. the vocabulary terms, each classified in context.
        """
        hits: List[ScanHit] = []

        # --- 1. the structural determination, on the text itself ---------
        structural = self.classify_structural(text)
        if structural in BLOCKED_CONTEXTS:
            hits.append(ScanHit(
                surface=_SURFACE_FOR_REASON.get(structural, structural),
                reason=structural,
                action=WrapperAction.CANCEL,
                context=self._context_of(text, self._first_match(text)),
                count=1,
            ))
            # a blocked reading ends the scan: the operation stops, and
            # reporting further vocabulary hits would bury that.
            return hits

        # --- 2. the vocabulary terms, each in context ----------------------
        low = text.lower()
        seen: set = set()
        for surface in self.vocabulary:
            if surface.lower() not in low:
                continue
            # count the occurrences so the log carries the frequency
            n = low.count(surface.lower())
            if n == 0:
                continue
            key = surface.lower()
            if key in seen:
                continue
            seen.add(key)

            reason = self.classify_deterministically(text, surface, sender)

            # The classifier refines, and only refines. It cannot turn a
            # BLOCKED reading into an ALLOWED one on its own -- that is
            # the whole safety direction, and it keeps the classifier
            # from being the weak link.
            if (self.classifier is not None
                    and reason in ALLOWED_CONTEXTS):
                try:
                    judged = self.classifier.classify(text, surface, sender)
                except Exception:
                    judged = None
                if judged in BLOCKED_CONTEXTS:
                    reason = judged
                elif judged in ALLOWED_CONTEXTS:
                    reason = judged
                # an unusable answer leaves the deterministic reading

            if reason in BLOCKED_CONTEXTS:
                action = WrapperAction.CANCEL
            elif reason == "poison_echo":
                action = WrapperAction.SANITIZE
            else:
                action = WrapperAction.FLAG

            hits.append(ScanHit(
                surface=surface,
                reason=reason,
                action=action,
                context=self._context_of(text, surface),
                replacement=self.replacements.get(surface.lower(), surface),
                count=n,
            ))
        return hits

    def sanitize(self, text: str, hits: Iterable[ScanHit]) -> str:
        """Apply the neutral substitutions, case-preserving."""
        out = text
        for h in hits:
            if h.action is not WrapperAction.SANITIZE:
                continue
            repl = h.replacement or h.surface
            out = re.sub(re.escape(h.surface), repl, out, flags=re.IGNORECASE)
        return out


# ===========================================================================
# THE CLASSIFIER -- optional escalator
# ===========================================================================

class PoisonContextClassifier:
    """Judges the context of a flagged term. Optional; never a gate.

    The spec called for a small model here, called ONLY when the poison
    vocabulary appears. That is right, and the important property is the
    one this implementation adds: the classifier's answer is advisory.

    It can escalate an allowed reading to a blocked one. It cannot
    downgrade a blocked one, and its absence changes nothing.

    The default implementation is a rule-based stand-in so the wrapper is
    testable and works with no model at all. A model-backed subclass
    overrides `classify`.
    """

    def classify(self, text: str, vocab_hit: str, sender: str) -> str:
        """Return one of ALLOWED_CONTEXTS or BLOCKED_CONTEXTS."""
        return "poison_discussion"


# ===========================================================================
# THE WRAPPER
# ===========================================================================

@dataclass
class MTELLMWrapper:
    """The deterministic boundary around an LLM.

    THE CALL SHAPE. The LLM is a callee:

        llm.generate(prompt) -> str

    and the wrapper owns everything around it. The caller never sees raw
    model output; it sees a `WrapperResult`.

    THE GOVERNOR. Optional, and consulted last. If the governor vetoes,
    the operation does not proceed. A wrapper with no governor still
    works -- it just has one fewer gate.
    """

    llm: LLMClient
    echo: EchoDetector = field(default_factory=EchoDetector)
    poison: PoisonScanner = field(default_factory=PoisonScanner)
    governor: Optional[GovernorClient] = None
    #: How many times to ask for a regeneration before accepting the
    #: output with the echo stripped.
    rephrase_max_retries: int = 1
    #: The instruction used when asking for a regeneration.
    rephrase_instruction: str = (
        "Do not quote the user's input back, do not simulate a dialogue, "
        "and do not invite further conversation. Respond in your own voice."
    )
    #: An audit trail. Every decision is appended.
    log: List[WrapperResult] = field(default_factory=list)

    # -- the LLM, called safely ----------------------------------------

    def _generate(self, prompt: str, system_override: Optional[str] = None) -> str:
        """Call the LLM. A failure here is a CANCEL, never a pass.

        If the model cannot be reached, the operation does not proceed
        with an empty response that looks like a legitimate answer.
        """
        kwargs: Dict[str, object] = {}
        if system_override is not None:
            kwargs["system_override"] = system_override
        try:
            if system_override is None:
                out = self.llm.generate(prompt)
            else:
                out = self.llm.generate(prompt, **kwargs)
        except TypeError:
            # a client whose signature does not take the override
            if system_override is None:
                raise
            out = self.llm.generate(prompt)
        except Exception as exc:
            raise _LLMUnavailable(str(exc)) from exc
        return out if isinstance(out, str) else str(out)

    # -- the main path --------------------------------------------------

    def run(self, user_text: str) -> WrapperResult:
        """Take one exchange through the boundary."""
        original = user_text

        # 1. the INPUT, scanned for injection and harmful instruction.
        #    These are the two determinations that stop the operation, so
        #    they are checked before the model is called at all.
        input_hits = self.poison.scan(user_text, sender="user")
        blocking = [h for h in input_hits if h.action is WrapperAction.CANCEL]
        if blocking:
            res = WrapperResult(
                action=WrapperAction.CANCEL,
                reason=blocking[0].reason,
                original=original,
                modified="",
                flagged=[h.reason for h in input_hits],
                occurrences=[_as_dict(h) for h in input_hits],
            )
            self.log.append(res)
            return res

        # 2. call the model.
        try:
            response = self._generate(user_text)
        except _LLMUnavailable as exc:
            res = WrapperResult(
                action=WrapperAction.CANCEL,
                reason="classifier_unavailable",
                original=original,
                modified="",
                flagged=["llm_unavailable: %s" % exc],
            )
            self.log.append(res)
            return res

        # 3. the OUTPUT, scanned for echo and for poison.
        echo_reason, overlap = self.echo.scan(user_text, response)
        output_hits = self.poison.scan(response, sender="llm")
        output_blocking = [h for h in output_hits if h.action is WrapperAction.CANCEL]

        if output_blocking:
            res = WrapperResult(
                action=WrapperAction.CANCEL,
                reason=output_blocking[0].reason,
                original=original,
                modified="",
                flagged=[h.reason for h in output_hits],
                occurrences=[_as_dict(h) for h in output_hits],
            )
            self.log.append(res)
            return res

        # 4. the echo. Try a regeneration first; fall back to stripping
        #    the scaffolding.
        rephrases = 0
        action = WrapperAction.PASS
        reason = "passed all guards"
        flagged: List[str] = []
        final = response

        if echo_reason is not None:
            flagged.append(echo_reason)
            final = self._repair_echo(user_text, response, echo_reason)
            rephrases = self._rephrase_count
            action = WrapperAction.REPHRASE if rephrases else WrapperAction.FLAG
            reason = echo_reason

        # 5. the poison, in the output.
        sanitizable = [h for h in output_hits if h.action is WrapperAction.SANITIZE]
        if sanitizable:
            final = self.poison.sanitize(final, sanitizable)
            flagged.extend(h.reason for h in output_hits)
            if action is WrapperAction.PASS:
                action = WrapperAction.SANITIZE
                reason = sanitizable[0].reason

        # 6. the governor, last.
        if self.governor is not None:
            try:
                approved = self.governor.approve(final)
            except Exception:
                # an unavailable governor is NOT consent
                approved = False
            if not approved:
                res = WrapperResult(
                    action=WrapperAction.CANCEL,
                    reason="governor_veto",
                    original=original,
                    modified="",
                    flagged=flagged + ["governor_veto"],
                    occurrences=[_as_dict(h) for h in output_hits],
                )
                self.log.append(res)
                return res

        res = WrapperResult(
            action=action,
            reason=reason,
            original=original,
            modified=final,
            flagged=flagged,
            rephrases=rephrases,
            occurrences=[_as_dict(h) for h in output_hits],
        )
        self.log.append(res)
        return res

    # -- the echo repair ------------------------------------------------

    _rephrase_count: int = 0

    def _repair_echo(self, user_text: str, response: str,
                     echo_reason: str) -> str:
        """Ask for a regeneration; fall back to stripping the markers."""
        self._rephrase_count = 0
        for _ in range(max(0, self.rephrase_max_retries)):
            try:
                again = self._generate(user_text, self.rephrase_instruction)
            except Exception:
                break
            self._rephrase_count += 1
            reason, _ = self.echo.scan(user_text, again)
            if reason is None:
                return again
        # no clean regeneration: strip the visible scaffolding
        return self.echo.drop_echo(response)


class _LLMUnavailable(Exception):
    """The model could not be reached. Never a pass."""


def _as_dict(h: ScanHit) -> Dict[str, object]:
    return {
        "surface": h.surface,
        "reason": h.reason,
        "action": h.action.value,
        "context": h.context,
        "count": getattr(h, "count", 1),
    }


#: The word pattern used for overlap scoring. Deliberately simple --
#: the echo test is about REPETITION of the user's words, and a richer
#: tokeniser would change the threshold's meaning.
_WORDS = re.compile(r"[a-z0-9']+")
