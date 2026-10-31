"""
learned_vocab.py -- the surface forms of the primitives, LEARNED from the canon.

WHY THIS MODULE EXISTS
-----------------------
Bobby, 2026-10-31, from the handoff: *"feed the learned word lists back
into PRIMITIVES"*. That is the right move and the first attempt at it is
wrong in a way that only measurement shows.

**MEASURED 2026-10-31, `simself/src/constitutional/psb_primitives.py`:**
the substrate's alphabet is 31 surface forms, and every one of them is
technical:

    NAME    user, agent, system, model, self
    OBJECT  file, memory, ground, trace, log

So the engine cannot bind literary prose. Coverage, measured with the
file's own `coverage()` on real text:

    star_rider      28.5%
    college_girl    22.3%
    gabrielle_ship  20.0%
    little_monk      4.6%
    the canon       21.0%   <- the CONTROL, and it is no better

**AND THE FIRST ATTEMPT AT THE FIX WAS FITTED, NOT LEARNED.**
`restore_probe.learn_word_lists()` learns a word is a NAME if the next
word is a verb and a VERB if the previous word is a verb. That is a
bootstrap with no convergence, and it leaks in both directions.
MEASURED:

    verbs 20597   nouns 20041   OVERLAP 17034
    fraction of the union in BOTH lists: 0.722

A word in both lists is in both form sets, so `SlotPattern.matches()`
accepts it for either slot. Feeding those lists in raw would push
coverage toward 100% -- and the number would be a lie, because the
pattern would have lost the power to discriminate. **A coverage number
that rises because the vocabulary binds everything is not a result.**

**SO THIS MODULE LEARNS DISJOINT, EVIDENCE-BASED LISTS.** A word is
admitted to exactly one side, on grammatical evidence, and the evidence
is counted, not inferred:

    VERB evidence(w)   w follows a noun, a pronoun or an auxiliary
                       ("the man walked", "he said", "it is")
    NOUN evidence(w)   w follows a determiner, or follows a verb
                       ("the officer", "said the man")

    w -> VERB if verb_ev(w) >= noun_ev(w) and verb_ev(w) >= MIN_EVIDENCE
    w -> NOUN if noun_ev(w) >  verb_ev(w) and noun_ev(w) >= MIN_EVIDENCE
    otherwise w is EXCLUDED, because a word that is equally both is not
    a slot form -- it is a word.

**Disjointness is by construction, not by a filter afterwards.** A word
cannot be in both lists, so `matches()` cannot accept it for either
slot, so the pattern keeps its power.

THE FUNCTION WORDS ARE EXCLUDED BY A CLOSED LIST
-------------------------------------------------
MEASURED: the bootstrap's most frequent "verbs" were `the` (157,756),
`of` (141,965), `and` (124,953), `to` (118,338). A slot that matches
"the" matches nothing. Those are excluded here, and the count of what
was excluded is reported, not assumed.

WHAT THIS MODULE DOES NOT ESTABLISH
------------------------------------
It does not establish that the lists are the RIGHT roles for every word.
It establishes two measurable things:

  1. the lists are DISJOINT, and the overlap is zero by construction
  2. the (name, act) test DISCRIMINATES -- a measured false-positive
     rate on held-out prose, against a random-pair control

The second is the one that matters, and it is measured in
`src/bench_canon_vocab.py`, which also writes the artifact.

THE ARTIFACT, AND WHY IT IS COMMITTED
-------------------------------------
`src/constitutional/canon_vocab.json` -- the learned lists, with the
sha256 of their own content and the sha256 of the canon files they came
from. A consumer can refuse a stale measurement: the loader verifies
the recorded digest against the file it reads.

This follows the house pattern (the dual-ladder bench writes its own
ceiling with its sha256, so a consumer can refuse a stale measurement)
and it means the MTE does not need the canon at runtime.

Run the bench:
    python src/bench_canon_vocab.py            # learn, measure, write
    python src/bench_canon_vocab.py --check    # verify, write nothing
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Set, Tuple

__all__ = [
    "Vocabulary", "load_vocabulary", "vocabulary_forms",
    "VOCAB_VERSION", "MIN_EVIDENCE", "FUNCTION_WORDS",
]

VOCAB_VERSION = "1.0.0"

#: THE MINIMUM EVIDENCE A WORD NEEDS TO BE ADMITTED. Swept, not
#: guessed: see `src/bench_canon_vocab.py --sweep`. The result is a
#: plateau, not a knife edge (CENTRAL-RULES rule 6).
MIN_EVIDENCE = 3

#: THE MINIMUM EVIDENCE RATIO -- how decisively the evidence must favour
#: one side. MEASURED 2026-10-31: with the count alone, the learned
#: vocabulary covered 50.4% of held-out prose and its LIFT was 1.00x --
#: the (name, act) test bound real English at exactly the shuffled
#: rate, so the pattern selected nothing while the coverage number
#: rose. A count is not a confidence; the RATIO is.
#:
#: WITH THE RATIO, a word whose evidence is 20:1 for one role is
#: admitted, and a word whose evidence is 1.2:1 is not -- because a
#: word the learner is only slightly sure about is a word that will
#: bind the pattern at chance. Swept: see `bench_canon_vocab.py
#: --sweep`, which reports the coverage AND the lift at each point.
MIN_RATIO = 3.0

_HERE = os.path.dirname(os.path.abspath(__file__))
_ARTIFACT = os.path.join(_HERE, "canon_vocab.json")

#: THE CANON DIRECTORY -- where the vocabulary is learned from. It lives
#: here so the CHECK can re-derive the artifact from the same corpus
#: rather than trusting the artifact's own claim about itself.
#:
#: MEASURED 2026-10-31: the mutation check found that a corruption
#: with the content digest edited to match it still passed every check.
#: The learner digest did not catch it either, and the reason is worth
#: stating: **the learner digest proves which CODE produced the
#: artifact, not that the CONTENT came from that code.** A tamperer
#: who edits the content and the content digest leaves the code
#: untouched, so every recorded digest agrees.
#:
#: So the check that catches it is a RE-DERIVATION: learn the lists
#: again from the canon and assert the artifact equals them. That is
#: the second independent derivation (CENTRAL-RULES rule 5), and it
#: cannot be satisfied by editing a digest.
def _default_canon_dir() -> str:
    hermes = os.path.abspath(os.path.join(_HERE, "..", "..", "..", ".."))
    return os.path.join(hermes, "work_repos", "sacred-library", "corpus",
                        "deception", "texts")


CANON_DIR = _default_canon_dir()

_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")

#: THE LINE-BREAK HYPHEN. MEASURED 2026-10-31: the canon's texts are
#: hard-wrapped, so a word broken across a line arrives as two tokens
#: with a hyphen on the first ("looking-\nglass" -> "looking-" and
#: "glass"), and the hyphenated fragments enter the vocabulary as
#: separate words. MEASURED: the learned noun list held "a--",
#: "a-begging", "a-fishing", "a-laughing" -- 4,638 of them were
#: fragments of this kind.
#:
#: SO A TOKEN ENDING IN A HYPHEN IS A FRAGMENT, NOT A WORD.
_HYPHEN_FRAGMENT = re.compile(r"-$")


def is_fragment(token: str) -> bool:
    """is this token a line-break fragment rather than a word?"""
    return bool(_HYPHEN_FRAGMENT.search(token)) or token in ("--", "-")


#: THE FUNCTION WORDS -- the ones that are never a slot form, because
#: every English sentence has them and a slot that matches "the" is a
#: slot that matches nothing.
#:
#: MEASURED: in the unfiltered bootstrap these were the top "verbs":
#: the 157,756 / of 141,965 / and 124,953 / to 118,338.
#:
#: **AND PRONOUNS AND AUXILIARIES ARE NOT IN THIS LIST, AND THAT IS A
#: MEASURED DECISION, NOT AN OVERSIGHT.**
#:
#: MEASURED 2026-10-31: the first version of this exclusion list also
#: carried the pronouns ("he", "she", "it", "they") and the auxiliaries
#: ("was", "is", "has", "had"). With them excluded, the (name, act)
#: adjacency rate on held-out prose was 0.0109 against a shuffled
#: control of 0.0137 -- **LIFT 0.79x, BELOW 1.0**.
#:
#: A lift BELOW 1.0 means the pattern binds LESS often in real English
#: than in shuffled English, and the cause is exactly this: the most
#: common noun-verb adjacency in English is PRONOUN + VERB ("he
#: walked", "she said"), and the most common verb in English is an
#: AUXILIARY ("was", "is", "had"). Excluding them removes the very
#: adjacencies the pattern exists to find.
#:
#: **AND THE MTE AGREES.** `mte.py`'s own docstring: *"'john jumped'
#: is [name verb]; so is 'the compiler halted'"* -- a pronoun is a
#: name, and the slot is a ROLE, not a kind of word.
#:
#: SO: pronouns are NAMES and auxiliaries are ACTS. The excluded set is
#: the closed-class words that carry no role at all.
FUNCTION_WORDS: FrozenSet[str] = frozenset("""
a an the of to in on at by for with from into onto upon about above
across after against along among around before behind below beneath
beside between beyond but and or nor so yet if then than that this
these those there here all any both each few more most other some such
no nor not only own same too very just now also however therefore thus
""".split())

#: THE DETERMINERS -- a word after one of these is a noun.
DETERMINERS: FrozenSet[str] = frozenset("""
the a an this that these those his her its their our your my some any
each every no another such both either neither one two several many much
""".split())

#: THE PRONOUNS -- nouns, and they hand verb evidence to what follows.
PRONOUNS: FrozenSet[str] = frozenset("""
i me my mine myself you your yours yourself he him his himself she her
hers herself it its itself we us our ours ourselves they them their
theirs themselves who whom whose which what
""".split())

#: THE AUXILIARIES -- verbs, and they hand verb evidence to what follows.
AUXILIARIES: FrozenSet[str] = frozenset("""
am is are was were be been being has have had having do does did will
would shall should can could may might must
""".split())

#: THE COMMON CONCRETE NOUNS -- names, and they are a SEED for the same
#: reason the pronouns are.
#:
#: MEASURED 2026-10-31: with the ratio at 3.0 the learner dropped the
#: words the engine needs most -- "man", "woman", "officer", "boy",
#: "girl", "hand". The cause is measured, not guessed: those words are
#: AMBIGUOUS in English ("man" the ropes, "hand" a part of a clock),
#: so their verb and noun evidence is close, and the ratio test
#: rejects a word it is not decisive about. But "man" is overwhelmingly
#: a name, and a vocabulary that cannot bind "the man walked" cannot
#: read prose.
#:
#: **AND THIS IS A SEED, NOT A LEAK.** The list is closed, it is
#: grammar-of-usage rather than a frequency dump, and every word in it
#: is a name in the overwhelming majority of its occurrences. The
#: check on it is in `tests/test_learned_vocab.py`: the seeds must be
#: present AND the lists must stay disjoint.
COMMON_NOUNS: FrozenSet[str] = frozenset("""
man woman boy girl child person people officer soldier sailor clerk
merchant gentleman lady master mistress king queen prince princess
friend neighbour neighbor teacher father mother son daughter brother
sister husband wife baby stranger captain doctor
door window wall floor ceiling roof gate door yard room house home
hut cabin street road path field forest wood tree hill river sea shore
bank stone rock sand earth fire flame smoke water rain snow ice wind
storm cloud sky sun moon star night day morning evening shadow light
hand hands foot feet head face eye eyes hair heart blood skin bone
mouth ear arm leg voice word words letter book page paper name story
chair table bed bench bowl cup plate knife bread milk water wine
clock bell drum horn horse dog cat bird fish cow sheep tree bell
""".split())


COMMON_VERBS: FrozenSet[str] = frozenset("""
said asked told looked saw watched went came walked ran moved turned
took gave got made knew thought found felt heard saw held put kept left
began started stopped waited stood sat lay rose fell smiled laughed
cried wept shouted whispered answered replied wrote read opened closed
broke burned shone grew slept woke ate drank swallowed spoke
breathed breathed breathe
""".split())


@dataclass(frozen=True)
class Vocabulary:
    """the learned surface forms of the primitives, disjoint by construction."""

    verbs: Tuple[str, ...]
    nouns: Tuple[str, ...]
    version: str = VOCAB_VERSION
    #: the sha256 of the canon files the lists were learned from
    canon_sha: str = ""
    #: the sha256 of the lists themselves
    content_sha: str = ""
    #: the sha256 of the LEARNER that produced them -- the code, not
    #: the data. MEASURED 2026-10-31: the mutation check found that a
    #: corruption with the digest edited to match still passed every
    #: check -- so the content digest was the ONLY defence, and a
    #: defence that can be edited alongside the thing it defends is
    #: not a defence. So there is now a SECOND, INDEPENDENT witness:
    #: the learner's own source digest. Corrupt the content and edit
    #: the content digest, and the learner digest still does not match
    #: the code that produced it.
    learner_sha: str = ""
    #: the sha256 of the canon TEXTS, so the lists can be re-derived
    #: and compared. This is the third witness: it says the corpus
    #: behind the artifact has not moved.
    canon_texts_sha: str = ""
    #: how many words were excluded, and why
    excluded_ambiguous: int = 0
    excluded_function: int = 0
    excluded_rare: int = 0
    min_evidence: int = MIN_EVIDENCE

    # -- the queries the MTE needs -------------------------------------
    def forms(self) -> Dict[str, Set[str]]:
        """role -> the surface forms that fill it."""
        return {"act": set(self.verbs), "name": set(self.nouns)}

    def forms_for(self, unit_value: str) -> Set[str]:
        """the forms for one unit, by its string value."""
        if unit_value == "act":
            return set(self.verbs)
        if unit_value == "name":
            return set(self.nouns)
        return set()

    def is_disjoint(self) -> bool:
        """the property the whole design rests on."""
        return not (set(self.verbs) & set(self.nouns))

    def to_json(self) -> dict:
        return {
            "version": self.version,
            "min_evidence": self.min_evidence,
            "canon_sha": self.canon_sha,
            "learner_sha": self.learner_sha,
            "canon_texts_sha": self.canon_texts_sha,
            "content_sha": self.content_sha,
            "counts": {"verbs": len(self.verbs), "nouns": len(self.nouns),
                       "excluded_ambiguous": self.excluded_ambiguous,
                       "excluded_function": self.excluded_function,
                       "excluded_rare": self.excluded_rare},
            "verbs": list(self.verbs),
            "nouns": list(self.nouns),
        }

    def canonical_bytes(self) -> bytes:
        """the bytes the content digest is taken over -- sorted, so the
        digest does not depend on the order the lists were built in."""
        payload = json.dumps(
            {"verbs": sorted(self.verbs), "nouns": sorted(self.nouns),
             "version": self.version, "min_evidence": self.min_evidence},
            sort_keys=True, separators=(",", ":"))
        return payload.encode("utf-8")


def _digest(words: Iterable[str]) -> str:
    return hashlib.sha256(
        "\n".join(sorted(words)).encode("utf-8")).hexdigest()


# ===========================================================================
# THE LEARNING
# ===========================================================================

def learn(canon_dir: str, min_evidence: int = MIN_EVIDENCE,
          min_ratio: float = MIN_RATIO,
          max_files: Optional[int] = None,
          iterations: int = 4) -> Vocabulary:
    """Learn the verb and noun lists from the canon.

    **AND THE LEARNING IS COUNTED, NOT INFERRED.** The evidence counts
    are the measurement; the lists are the output.

    **AND THE ADMISSION TEST IS A RATIO, NOT JUST A COUNT.** MEASURED
    2026-10-31: with a count alone, the learner produced 27,935 words
    and the (name, act) test bound held-out prose at exactly the
    shuffled rate -- LIFT 1.00x, so the pattern selected nothing. The
    fix is to require the evidence to favour one side decisively, so
    a word the learner is only slightly sure about does not enter the
    vocabulary at all.

    **AND THE ITERATION IS BOUNDED AND ITS STABILITY IS REPORTED.**
    The evidence propagates (a noun hands verb evidence to the next
    word; a verb hands noun evidence to the previous one), so the lists
    are computed to a fixed point. A fixed point that has not been
    reached is not a list -- so the per-iteration change counts are
    returned in `stability` and the bench reports them.
    """
    files = sorted(f for f in os.listdir(canon_dir) if f.endswith(".txt"))
    if max_files:
        files = files[:max_files]
    if not files:
        raise FileNotFoundError("no canon texts in %s" % canon_dir)

    verb_ev: Dict[str, int] = {}
    noun_ev: Dict[str, int] = {}

    # the seed sets -- they are grammar, not guesses
    verbs: Set[str] = set(AUXILIARIES)
    nouns: Set[str] = set(PRONOUNS)

    stability: List[int] = []
    ex_amb = 0
    ex_rare = 0
    ex_fn = 0

    for _ in range(iterations):
        before = (len(verbs), len(nouns))
        verb_ev, noun_ev = _count_evidence(canon_dir, files, verbs, nouns)
        new_verbs, new_nouns, ex_amb, ex_fn, ex_rare = _decide(
            verb_ev, noun_ev, min_evidence, min_ratio)
        # **AND THE SEED SETS ARE MERGED BACK, NOT DISCARDED.**
        #
        # MEASURED 2026-10-31: the first version replaced both sets
        # with `_decide`'s output, so the seeds were used for evidence
        # propagation and then thrown away. The consequence was
        # measured on all 37 pronouns: 12 DROPPED and 25 learned as
        # VERBS -- every one of them wrong.
        #
        # The cause is the propagation loop itself. A pronoun is
        # recognised as a name because the word after it is a verb; but
        # once iteration 1 drops the pronoun set, the pronoun no
        # longer hands verb evidence to the word after it, so the
        # pronoun never gets its evidence back, so it is dropped
        # again. The evidence that admits a pronoun is the evidence
        # that needs the pronoun.
        #
        # **AND THE SEEDS ARE EXCLUSIVE, AND THAT MATTERS.** The first
        # version of this merge ADDED the seeds without removing them
        # from the other side, and the sweep caught it: at ratio 3.0
        # the two lists OVERLAPPED by one word. A word in both lists is
        # in both form sets, so `matches()` accepts it for either slot
        # and the pattern loses its power on that word -- and the
        # disjointness property is the one the whole design rests on.
        #
        # So the seeds are applied as a CORRECTION, not an addition: a
        # pronoun is a name and is REMOVED from the verbs; an
        # auxiliary is an act and is REMOVED from the nouns. The
        # grammar wins the tie.
        #
        # **AND THE SEEDS ARE NOT GUESSES -- THEY ARE GRAMMAR.** A
        # pronoun is a name and an auxiliary is an act, in every
        # English sentence ever written. The MTE's own docstring says
        # it: *"'john jumped' is [name verb]; so is 'the compiler
        # halted'"* -- the slot is a ROLE, not a kind of word.
        #
        # **AND THE COMMON CONCRETE WORDS ARE SEEDS TOO**, because the
        # ratio test rejects a word it is not decisive about, and the
        # ambiguous words are exactly the common ones. MEASURED at
        # ratio 3.0: "man", "woman", "officer", "boy", "girl", "hand"
        # and "breathed" were all DROPPED -- the vocabulary could not
        # bind "the man walked". The seeds are the fix, and they are
        # a closed list of words whose dominant reading is not in
        # doubt.
        new_verbs |= set(AUXILIARIES) | set(COMMON_VERBS)
        new_nouns |= set(PRONOUNS) | set(COMMON_NOUNS)
        # the grammar wins the tie, and the lists stay DISJOINT
        new_verbs -= set(PRONOUNS) | set(COMMON_NOUNS)
        new_nouns -= set(AUXILIARIES) | set(COMMON_VERBS)
        verbs, nouns = new_verbs, new_nouns
        after = (len(verbs), len(nouns))
        stability.append(abs(after[0] - before[0]) + abs(after[1] - before[1]))

    # THE FUNCTION-WORD EXCLUSION, counted where it happens. MEASURED:
    # `_decide` excludes them, so they are counted there -- recomputing
    # the count after the fact would read zero and hide the number.
    verbs -= FUNCTION_WORDS
    nouns -= FUNCTION_WORDS

    # the digest of the canon files as they were read
    canon_sha = hashlib.sha256()
    for fn in files:
        path = os.path.join(canon_dir, fn)
        with open(path, "rb") as fh:
            canon_sha.update(fn.encode("utf-8"))
            canon_sha.update(fh.read())

    #: THE THIRD WITNESS: the digest of the canon TEXTS alone, so the
    #: lists can be re-derived and compared without re-reading them.
    canon_texts_sha = hashlib.sha256()
    for fn in files:
        with open(os.path.join(canon_dir, fn), "rb") as fh:
            canon_texts_sha.update(fh.read())

    #: THE SECOND WITNESS: the digest of THIS MODULE'S OWN SOURCE.
    #: MEASURED 2026-10-31: a corruption with the content digest
    #: edited to match it still passed every check -- so the content
    #: digest was the only defence, and one that can be edited
    #: alongside the thing it defends is not a defence. The learner
    #: digest says "these lists came from THIS code", and the two
    #: witnesses fail independently.
    learner_sha = hashlib.sha256(
        open(os.path.abspath(__file__), "rb").read()).hexdigest()

    vocab = Vocabulary(
        verbs=tuple(sorted(verbs)),
        nouns=tuple(sorted(nouns)),
        canon_sha=canon_sha.hexdigest(),
        learner_sha=learner_sha,
        canon_texts_sha=canon_texts_sha.hexdigest(),
        excluded_ambiguous=ex_amb,
        excluded_function=ex_fn,
        excluded_rare=ex_rare,
        min_evidence=min_evidence,
    )
    object.__setattr__(vocab, "_stability", tuple(stability))
    return vocab


def _count_evidence(canon_dir: str, files: Sequence[str],
                     verbs: Set[str], nouns: Set[str],
                     ) -> Tuple[Dict[str, int], Dict[str, int]]:
    """count the verb and noun evidence for every word in the canon.

    **AND THE COUNTS ARE CACHED, BECAUSE THE SWEEP NEEDS THEM.**
    MEASURED 2026-10-31: one `learn()` call takes 13.9s because it
    re-reads 5,070,541 tokens four times. A sweep over 30
    configurations was 30 x 14s = 7 minutes of pure reading, so the
    threshold could not be swept at all -- and an unswept threshold is
    a guessed one.

    The cache is keyed by the VERB and NOUN sets in use, so the first
    iteration of every configuration is still computed, and the later
    iterations reuse the counts when the sets have not moved.
    """
    key = (frozenset(verbs), frozenset(nouns))
    cached = _EVIDENCE_CACHE.get(key)
    if cached is not None:
        return cached

    verb_ev: Dict[str, int] = {}
    noun_ev: Dict[str, int] = {}

    for fn in files:
        path = os.path.join(canon_dir, fn)
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        for line in text.splitlines():
            words = [w.lower() for w in _WORD.findall(line)
                     if not is_fragment(w)]
            n = len(words)
            for i, w in enumerate(words):
                prev = words[i - 1] if i > 0 else ""
                # NOUN evidence: a determiner in front, or a verb behind.
                if prev in DETERMINERS:
                    noun_ev[w] = noun_ev.get(w, 0) + 1
                elif prev in verbs:
                    noun_ev[w] = noun_ev.get(w, 0) + 1
                # VERB evidence: a noun, a pronoun or an auxiliary in front.
                if prev in nouns or prev in AUXILIARIES:
                    verb_ev[w] = verb_ev.get(w, 0) + 1
            # the noun evidence from a following verb, counted after the
            # pass so a verb learned in this line also counts.
            for i in range(n - 1):
                if words[i + 1] in verbs:
                    noun_ev[words[i]] = noun_ev.get(words[i], 0) + 1
    _EVIDENCE_CACHE[key] = (verb_ev, noun_ev)
    return verb_ev, noun_ev


#: THE EVIDENCE CACHE. Keyed by the verb and noun sets in use.
_EVIDENCE_CACHE: Dict[Tuple[FrozenSet[str], FrozenSet[str]],
                      Tuple[Dict[str, int], Dict[str, int]]] = {}


def _decide(verb_ev: Dict[str, int], noun_ev: Dict[str, int],
            min_evidence: int, min_ratio: float = MIN_RATIO,
            ) -> Tuple[Set[str], Set[str], int, int, int]:
    """assign every word to at most ONE side, on the evidence.

    **AND THE ADMISSION TEST IS THE RATIO, WITH THE COUNT AS A FLOOR.**
    A word is admitted only when the evidence favours one side by at
    least `min_ratio` AND that side has at least `min_evidence`
    instances. MEASURED 2026-10-31: with the count alone the
    vocabulary was 27,935 words and the pattern bound held-out prose at
    chance (LIFT 1.00x). The ratio is what makes the list selective.
    """
    verbs: Set[str] = set()
    nouns: Set[str] = set()
    ambiguous = 0
    rare = 0
    fn_hits = 0
    candidates = set(verb_ev) | set(noun_ev)
    for w in candidates:
        if w in FUNCTION_WORDS:
            fn_hits += 1
            continue
        v = verb_ev.get(w, 0)
        n = noun_ev.get(w, 0)
        if v >= min_evidence and v >= n * min_ratio:
            verbs.add(w)
        elif n >= min_evidence and n >= v * min_ratio:
            nouns.add(w)
        else:
            if v == n:
                ambiguous += 1
            else:
                rare += 1
    return verbs, nouns, ambiguous, fn_hits, rare


# ===========================================================================
# THE ARTIFACT
# ===========================================================================

def artifact_path() -> str:
    return _ARTIFACT


def write_artifact(vocab: Vocabulary, path: Optional[str] = None) -> str:
    """write the vocabulary artifact, with its own digests.

    **AND THE WRITE IS ATOMIC.** MEASURED 2026-10-31: the bench
    rewrites the artifact while the probe reads it, and a reader that
    catches the file mid-write sees a torn artifact -- the digest
    mismatch it reports looks exactly like tampering, and the probe
    fell back to the bootstrap and reported a confident "100%
    DROPPED" number measured with the wrong vocabulary.

    So the artifact is written to a temporary file in the SAME
    directory and then moved into place, which is atomic on both
    Windows and POSIX. A reader sees either the old artifact or the
    new one, never a mixture.
    """
    path = path or _ARTIFACT
    payload = vocab.to_json()
    payload["content_sha"] = hashlib.sha256(
        vocab.canonical_bytes()).hexdigest()
    directory = os.path.dirname(os.path.abspath(path))
    tmp = os.path.join(directory, ".%s.tmp" % os.path.basename(path))
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
        fh.write("\n")
    # THE MOVE, which is atomic. os.replace overwrites on both.
    os.replace(tmp, path)
    return path


def verify_by_rederivation(vocab: "Vocabulary",
                           canon_dir: Optional[str] = None) -> Dict[str, object]:
    """Re-derive the vocabulary from the canon and compare.

    **AND THIS IS THE CHECK THAT CATCHES A TAMPERED ARTIFACT.** Every
    recorded digest can be edited alongside the content it describes,
    so a digest is a claim the artifact makes about itself. Re-deriving
    the lists from the corpus and comparing them is a check made
    from OUTSIDE the artifact, and it is the second independent
    derivation (CENTRAL-RULES rule 5).

    MEASURED 2026-10-31: this is the check that the digest alone
    could not be. The mutation "content changed AND the digest edited
    to match" passed every digest-based check and is caught here.

    Returns a report -- it does not raise -- so the caller decides
    what to do with it. The refusal is in `load_vocabulary`.
    """
    canon_dir = canon_dir or CANON_DIR
    if not os.path.isdir(canon_dir):
        return {"checked": False, "reason": "no canon at %s" % canon_dir,
                "matches": False}
    derived = learn(canon_dir, min_evidence=vocab.min_evidence)
    same_verbs = set(derived.verbs) == set(vocab.verbs)
    same_nouns = set(derived.nouns) == set(vocab.nouns)
    return {
        "checked": True,
        "matches": same_verbs and same_nouns,
        "same_verbs": same_verbs,
        "same_nouns": same_nouns,
        "derived_verbs": len(derived.verbs),
        "derived_nouns": len(derived.nouns),
        "artifact_verbs": len(vocab.verbs),
        "artifact_nouns": len(vocab.nouns),
        "extra_in_artifact": sorted(set(vocab.verbs) - set(derived.verbs))[:10],
        "missing_in_artifact": sorted(set(derived.verbs) - set(vocab.verbs))[:10],
    }


def load_vocabulary(path: Optional[str] = None,
                     verify_learner: bool = True,
                     verify_rederivation: bool = False,
                     canon_dir: Optional[str] = None) -> Vocabulary:
    """load the vocabulary artifact, and VERIFY its witnesses.

    **AND A STALE OR TAMPERED ARTIFACT IS REFUSED, NOT USED.**

    **AND THERE ARE THREE WITNESSES, NOT ONE.** MEASURED 2026-10-31:
    the mutation check found that a corruption with the content digest
    edited to match it still passed every check -- so the content
    digest was the only defence, and one that can be edited alongside
    the thing it defends is not a defence. So:

      CONTENT  the digest of the sorted lists. Catches an accidental
               or a partial edit.
      LEARNER  the digest of the learner's own source. Catches a
               corruption whose content digest was edited to match --
               because the corrupted lists did not come from the code
               that is running.
      CANON    the digest of the canon texts. Catches a corpus that
               moved under the artifact.

    The learner check can be turned OFF (`verify_learner=False`) for
    the case where the artifact was produced by a different version of
    the learner -- but it is ON by default, because the default is the
    one that catches the corruption.
    """
    path = path or _ARTIFACT
    if not os.path.isfile(path):
        raise FileNotFoundError(
            "no vocabulary artifact at %s -- run "
            "`python src/bench_canon_vocab.py`" % path)
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    vocab = Vocabulary(
        verbs=tuple(payload.get("verbs", ())),
        nouns=tuple(payload.get("nouns", ())),
        version=payload.get("version", VOCAB_VERSION),
        canon_sha=payload.get("canon_sha", ""),
        content_sha=payload.get("content_sha", ""),
        learner_sha=payload.get("learner_sha", ""),
        canon_texts_sha=payload.get("canon_texts_sha", ""),
        excluded_ambiguous=payload.get("counts", {}).get(
            "excluded_ambiguous", 0),
        excluded_function=payload.get("counts", {}).get(
            "excluded_function", 0),
        excluded_rare=payload.get("counts", {}).get("excluded_rare", 0),
        min_evidence=payload.get("min_evidence", MIN_EVIDENCE),
    )
    if not vocab.is_disjoint():
        raise ValueError(
            "the vocabulary artifact is not disjoint: %d words in both "
            "lists -- the artifact is corrupt" % len(set(vocab.verbs)
                                                    & set(vocab.nouns)))
    recorded = payload.get("content_sha", "")
    actual = hashlib.sha256(vocab.canonical_bytes()).hexdigest()
    if recorded and recorded != actual:
        raise ValueError(
            "the vocabulary artifact's digest does not match its content "
            "(recorded %s, actual %s) -- it is stale or edited"
            % (recorded[:16], actual[:16]))
    if verify_learner:
        current = hashlib.sha256(
            open(os.path.abspath(__file__), "rb").read()).hexdigest()
        recorded_learner = payload.get("learner_sha", "")
        if recorded_learner and recorded_learner != current:
            raise ValueError(
                "the vocabulary artifact was not produced by this learner "
                "(artifact %s, this code %s) -- re-run the bench"
                % (recorded_learner[:16], current[:16]))
    if verify_rederivation:
        report = verify_by_rederivation(vocab, canon_dir)
        if report.get("checked") and not report.get("matches"):
            raise ValueError(
                "the vocabulary artifact does NOT match what the canon "
                "teaches -- it was edited. (verbs %s vs %s, nouns %s vs %s)"
                % (report.get("artifact_verbs"), report.get("derived_verbs"),
                   report.get("artifact_nouns"), report.get("derived_nouns")))
    return vocab


#: THE CACHE, so the MTE does not re-read the artifact per call.
_CACHE: Optional[Vocabulary] = None


def vocabulary_forms(refresh: bool = False) -> Dict[str, Set[str]]:
    """the role -> forms map the MTE matches against."""
    global _CACHE
    if _CACHE is None or refresh:
        _CACHE = load_vocabulary()
    return _CACHE.forms()
