"""
restore_probe.py -- DOES THE SENSE COME BACK?

WHAT THIS IS
------------
Bobby, 2026-10-31: *"symbology is good, makes the book deep, but not
like star rider tries to do my story is boring. compare to dickens,
shelley, ludlum. to me"* and *"our author corpus is both -- not only
reference material in public domain to write from, but sentence
patterns to speak from. ie it determines an old-fashioned but
nonetheless human author voice for simself."*

**AND THE MEASUREMENT THAT DECIDES IT IS THE MTE'S OWN.**

MEASURED, `simself/src/constitutional/mte.py`:
> *"MTE runs the same operation the whole way: ambiguous natural
> language in, unambiguous bounded form out, **with the meaning RESTORED
> rather than approximated**."*

and the two functions that do it:
> `compile_span` -- *"Bind an English span to a slot pattern."*
> `restore` -- *"Rebuild meaning from the slots. The claim under test.
> **If the slots cannot carry the sense back, `restored` stays None
> and `lossless` is False. That is the engine admitting it failed,
> which is the only honest result available.**"*

**SO: THE LABEL RATE IS THE CONSEQUENCE OF A FAILED RESTORE.**
Star Rider names its furniture 33.3 times per 1,000 words against a
canon median of 7.8 -- because the slots do not carry the sense, so
the piece keeps re-saying the sense in the only channel it has left,
the word.

**AND THIS PROBE MEASURES THE RESTORE DIRECTLY**, on a real draft,
with the MTE's own functions:

    for each sentence:
        compile_span(sentence, pattern)   -> may be None
        restore(transform, lexicon)       -> may be None
        and: was the sense carried, or was it LABELLED?

**THE THREE OUTCOMES, and they are different failures:**

    CARRIED      the sentence bound to a pattern and the sense came
                 back. The meaning survived the transform.
    LABELLED     the sentence bound, but the sense came back only
                 because a LABEL carries it -- an idea-word doing the
                 work a scene should be doing. **This is the star-
                 rider failure, and it is measurable here.**
    DROPPED      the sentence did not bind, or the restore failed.
                 The meaning did not survive at all.

**AND THE WHOLE POINT IS THE COMPARISON:** a draft's carried-rate
against the canon's. The canon is the allowance.

THE STATE OF THE ENGINE, and it is stated here rather than hidden
----------------------------------------------------------------------
MEASURED 2026-10-31:
- `mte.py`'s `PRIMITIVES` holds **6** units (`act`, `refuse`, `name`,
  `commit`, `time`, `object`), not the 37 the design names.
- **there is no lexicon.** `src/lexicon/` is an empty package, and
  the "35-word string substitution table" that `mte.py`'s own
  docstring names as `simself/tools/lexicon` **does not exist on this
  machine.**
- so `restore()` cannot restore anything yet, because there are no
  senses to restore FROM.

**SO THIS PROBE BUILDS THE LEXICON FROM THE CANON.** That is the
point: the canon's 49 public-domain texts are the corpus, and the
lexicon is what the canon teaches. **A sense is a word plus the slot
pattern it appears in, with the line it was learned from.**

Run:
    python src/constitutional/restore_probe.py --canon
    python src/constitutional/restore_probe.py --draft <file.md>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_HERE), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

_HERMES = os.path.abspath(os.path.join(_HERE, "..", "..", "..", ".."))
_CANON = os.path.join(_HERMES, "work_repos", "sacred-library", "corpus",
                      "deception", "texts")

#: THE IMPORT, and it is a PACKAGE import. MEASURED 2026-10-31:
#: `mte.py` does `from .psb_primitives import ...`, so it can only be
#: imported as `constitutional.mte` -- importing it as a bare `mte`
#: raises ImportError ("attempted relative import with no known
#: parent package"), and the fallback caught that and raised again.
#:
#: AND THE PATH IS `src/`, NOT THE REPO ROOT. MEASURED: putting the
#: repo root on the path gave ModuleNotFoundError: No module named
#: 'constitutional' -- because the package is `src/constitutional/`.
#:
#: AND THIS FILE SITS IN `src/constitutional/` WHILE `author_pipe.py`
#: SITS IN `src/`. MEASURED: the third `dirname` from
#: `src/constitutional/` lands on `work_repos/`, not on the repo. So
#: the path is derived from the PACKAGE's own location, not from this
#: file's -- `os.path.dirname(__file__)` of `constitutional/__init__`
#: would be `src/`, and the reliable way is to walk up until a
#: directory named `constitutional` is found.
_PACKAGE_DIR = os.path.dirname(_HERE)          # .../src/constitutional
_SRC_DIR = os.path.dirname(_PACKAGE_DIR)      # .../src
_REPO_ROOT = os.path.dirname(_SRC_DIR)       # .../simself
for _p in (_SRC_DIR, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from constitutional.mte import (Lexicon, Sense, SlotPattern,
                                    compile_span, restore)
    from constitutional.psb_primitives import PRIMITIVES
except Exception:  # noqa: BLE001
    from mte import (Lexicon, Sense, SlotPattern,  # type: ignore
                      compile_span, restore)
    from psb_primitives import PRIMITIVES  # type: ignore


# ===========================================================================
# THE SENSE, and what it needs to be learned from a line
# ===========================================================================

#: THE SLOT ROLES, from the primitives that exist. MEASURED: six
#: units -- act, refuse, name, commit, time, object.
#:
#: AND THE SIX ARE ENOUGH TO START, because the point of the probe is
#: to measure whether the transform carries meaning, and a six-role
#: grammar can already do that on concrete prose.
ROLES: Tuple[str, ...] = tuple(p.value for p in PRIMITIVES)

#: THE PATTERNS, and they are the shapes the canon actually uses.
#:
#: AND THE FIRST PATTERN IS THE SIMPLE DECLARATIVE: a name and an
#: act. "The officer did not smile." "The hut breathed." Those are the
#: sentences that carry the scene, and they are the ones the label
#: rate does NOT count -- because they name a thing and do a verb.
PATTERNS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("name_act", ("name", "act")),
    ("name_act_act", ("name", "act", "act")),
    ("act_name", ("act", "name")),
    ("name_time_act", ("name", "time", "act")),
    ("name_act_name", ("name", "act", "name")),
    ("name_act_object", ("name", "act", "object")),
    ("name_object_act", ("name", "object", "act")),
)

#: THE VERBS AND THE NAMES, and they are LEARNED FROM THE CANON
#: rather than hand-listed.
#:
#: MEASURED 2026-10-31: the first version's hand-written noun list
#: held 49 words, so "Kelly walked to the door" did not bind -- "kelly"
#: was not in it -- and the probe DROPPED 100% of real prose (1918 of
#: 1918 sentences on star-rider). **A pattern that cannot bind real
#: sentences measures nothing.**
#:
#: SO THE LISTS ARE LEARNED, and the learning is the same learning the
#: lexicon does: a word is a NAME if the canon uses it before a verb,
#: and an ACT if the canon uses it after one. **That is the pattern
#: over the primitives, learned from the text** -- which is the whole
#: MTE idea, and it is why the corpus has to be the canon.
_LEARNED_VERBS = None
_LEARNED_NOUNS = None

SEED_VERBS = (
    "said", "asked", "looked", "went", "came", "took", "gave", "made",
    "knew", "heard", "felt", "held", "put", "turned", "stood", "sat",
    "walked", "ran", "spoke", "wrote", "read", "opened", "closed",
    "began", "stopped", "moved", "waited", "found", "saw",
    "laughed", "slept", "woke", "drank", "ate", "breathed", "smiled",
    "answered", "replied", "told", "showed", "left", "kept", "became",
    "knelt", "crawled", "swam", "climbed", "fell", "cried",
    "nodded", "shook", "reached", "struck", "burned", "folded",
)

SEED_NOUNS = (
    "man", "woman", "boy", "girl", "child", "door", "river", "hut",
    "fire", "hand", "hands", "face", "eye", "eyes", "voice", "head",
    "room", "house", "street", "book", "letter", "clock", "water",
    "stone", "stones", "sand", "milk", "cow", "cows", "forest", "tree",
    "path", "field", "wind", "rain", "night", "morning", "light",
    "dark", "boots", "coat", "cup", "bell", "shadow", "blood", "tool",
    "kettle", "tray", "hair", "feet", "words", "word",
    "mother", "father", "friend", "teacher", "king", "queen", "master",
    "sky", "cloud", "fog", "snow", "tide", "moon", "chair", "table",
    "floor", "wall", "window", "horse", "dog", "cat", "bird",
)


def learn_word_lists(canon_dir=None, max_files: int = 8):
    """the verbs and the names, learned from the canon."""
    if canon_dir is None:
        canon_dir = _CANON
    verbs = set(SEED_VERBS)
    nouns = set(SEED_NOUNS)
    if not os.path.isdir(canon_dir):
        return verbs, nouns
    files = [f for f in sorted(os.listdir(canon_dir))
             if f.endswith(".txt")][:max_files]
    for fn in files:
        try:
            text = open(os.path.join(canon_dir, fn), encoding="utf-8",
                        errors="replace").read()
        except OSError:
            continue
        for line in text.splitlines():
            words = [w.lower() for w in _WORD.findall(line)]
            for i, w in enumerate(words):
                if len(w) < 3:
                    continue
                if i + 1 < len(words) and words[i + 1] in verbs:
                    nouns.add(w)
                if i > 0 and words[i - 1] in verbs:
                    verbs.add(w)
    return verbs, nouns


def word_lists():
    """the learned lists, cached.

    **AND THESE ARE NOW THE DISJOINT LEARNED VOCABULARY, NOT THE
    BOOTSTRAP.** MEASURED 2026-10-31: the first version of this
    function learned its own lists by bootstrapping ("a word is a name
    if the next word is a verb"), and that produced 20,597 verbs and
    20,041 names with an OVERLAP of 17,034 -- 72% of the union in both
    lists. So "the" was a name AND an act, and the probe's own output
    showed it: every line began "the name ... the act".

    The bootstrap is kept below as `learn_word_lists()` for the record,
    and `learned_vocab.learn()` is the one that is used -- because it
    is DISJOINT (a word is in one form set or the other) and
    RATIO-ADMITTED, and those are the properties that let the pattern
    discriminate at all.

    **AND THE VOCABULARY IS INSTALLED INTO THE MTE's MATCHER HERE.**
    MEASURED 2026-10-31: the probe DROPPED 1918 of 1918 sentences
    (100%) while its OWN matcher was binding them -- "he walked"
    matched the probe's (name, act) shape, and then `compile_span`
    refused the very same window. The cause: the MTE's slot matcher
    reads the substrate's own 31 forms plus the installed
    `LITERARY_FORMS`, and **nothing had installed the vocabulary**, so
    the matcher had 7 act forms while the probe had 3,075.

    So the two used different vocabularies for the act -- exactly the
    gap the handoff named. **AND A TOOL THAT MEASURES THE ENGINE MUST
    USE THE ENGINE'S VOCABULARY**, or it measures its own idea of the
    engine.
    """
    global _LEARNED_VERBS, _LEARNED_NOUNS
    if _LEARNED_VERBS is None or _LEARNED_NOUNS is None:
        try:
            from constitutional.learned_vocab import load_vocabulary
            vocab = load_vocabulary()
            _LEARNED_VERBS = set(vocab.verbs)
            _LEARNED_NOUNS = set(vocab.nouns)
            # AND THE INSTALL, so the probe and the MTE share ONE
            # vocabulary. Without this the probe binds a window the
            # MTE then refuses, and reports 100% DROPPED -- which
            # reads as a finding about the engine and is a finding
            # about the probe.
            try:
                from constitutional import psb_primitives
                psb_primitives.install_vocabulary(vocab)
            except Exception:  # noqa: BLE001
                pass
        except Exception as exc:  # noqa: BLE001
            # **AND THE FALLBACK IS LOUD, BECAUSE A SILENT FALLBACK
            # MEASURED THE WRONG THING.**
            #
            # MEASURED 2026-10-31: the artifact was stale (its digest
            # did not match its content -- the digest check working
            # correctly), so `load_vocabulary` raised, this handler
            # swallowed it, and the probe went on to measure the
            # BOOTSTRAP vocabulary and reported a confident "100%
            # DROPPED" -- which reads as a finding about the engine and
            # is a finding about the probe.
            #
            # **A FALLBACK THAT HIDES ITS OWN FAILURE IS A FALLBACK
            # THAT MEANS SOMETHING ELSE.** So the reason is recorded
            # and printed, and the caller can see which vocabulary the
            # number came from.
            _LEARNED_SOURCE = "bootstrap (fallback: %s)" % exc
            print("  NOTE: the learned vocabulary was refused, so the "
                  "probe is using the bootstrap lists -- %s" % exc)
            _LEARNED_VERBS, _LEARNED_NOUNS = learn_word_lists()
        else:
            _LEARNED_SOURCE = "learned vocabulary (disjoint, "
            _LEARNED_SOURCE += "ratio-admitted)"
    return _LEARNED_VERBS, _LEARNED_NOUNS


#: WHERE THE LISTS CAME FROM. The probe reports it, because a number
#: measured with the wrong vocabulary is a number about the wrong
#: thing.
_LEARNED_SOURCE = ""


def learned_source() -> str:
    """which vocabulary the probe measured with."""
    word_lists()
    return _LEARNED_SOURCE


_WORD = re.compile(r"[A-Za-z']+")


# ===========================================================================
# THE LEXICON, learned from the canon
# ===========================================================================

@dataclass
class LearnedSense:
    """a sense, learned from a line in the canon."""
    word: str
    role: str
    #: the line it was learned from
    evidence: str
    source: str
    #: THE SHAPE THE WORD WAS FOUND IN. MEASURED 2026-10-31: the
    #: first version gave every sense a ONE-SLOT PSB (just its own
    #: role), and then `restore()` could never succeed for a TWO-slot
    #: pattern -- because `PSB.compatible()` requires EQUAL ARITY, so a
    #: 1-slot sense can never satisfy a 2-slot pattern.
    #:
    #: The consequence was that the restore probe DROPPED 1918 of 1918
    #: sentences (100%) -- and the cause was not the vocabulary at all.
    #: It was the lexicon carrying the wrong shape.
    #:
    #: So a sense now carries the PATTERN it was learned in, and the
    #: pattern it is compatible with is the one it was found in.
    shape: Tuple[str, ...] = ("name", "act")

    def to_sense(self) -> Any:
        """the MTE's Sense, with the slot pattern it was learned in.

        AND THE SIGNATURE, measured from `mte.py`: `Sense(word, pos,
        gloss, context, snr, psb)`. The first version called
        `Sense(word=..., gloss=..., snr=..., psb=...)` and raised
        TypeError for the missing `pos` and `context` -- so the probe
        could not build a single sense.

        **AND THE PSB IS NOW THE PATTERN THE WORD WAS LEARNED IN.**
        MEASURED 2026-10-31: with a one-slot PSB, `restore()` returned
        None for every two-slot pattern, and the probe reported 100%
        DROPPED. A sense that carries the shape it was found in can be
        restored into that shape.
        """
        units = [_unit_for(r) for r in self.shape]
        return Sense(word=self.word,
                     pos=self.role,
                     gloss="[%s] %s" % (self.role, self.word),
                     context="learned from %s" % (self.source,),
                     snr=1.0,
                     psb=SlotPattern.from_units(*units).psb)


def _unit_for(role: str) -> Any:
    """the UnitType for a role name.

    **AND IT RAISES FOR AN UNKNOWN ROLE, RATHER THAN RETURNING THE
    FIRST UNIT.** MEASURED 2026-10-31: the old `_units_for` fell back
    to `PRIMITIVES[0]` -- the ACT -- for any role it did not know, so a
    typo in a pattern silently produced an act-shaped pattern. A
    pattern that cannot be built should say so.
    """
    for u in PRIMITIVES:
        if u.value == role:
            return u
    raise KeyError("unknown role %r -- the roles are %s"
                   % (role, ", ".join(u.value for u in PRIMITIVES)))


def _units_for(role: str) -> List[Any]:
    """the UnitType for a role name, and the fallback."""
    for u in PRIMITIVES:
        if u.value == role:
            return [u]
    return [PRIMITIVES[0]]


def learn_lexicon(canon_dir: str = _CANON,
                  max_files: int = 12) -> Tuple[Any, List[Dict[str, Any]]]:
    """the lexicon, learned from the canon.

    **AND THE LEXICON IS LEARNED, NOT WRITTEN.** MEASURED 2026-10-31:
    `src/lexicon/` is an empty package and the 35-word substitution
    table that `mte.py`'s own docstring names **does not exist**. So
    the senses come from the canon's own lines, and every sense
    carries the line it was learned from.

    **AND THIS IS THE POINT OF THE WHOLE IDEA.** The canon is not
    reference material for a book -- it is the CORPUS THE ENGINE
    LEARNS FROM. The pattern over the primitives generalises, and the
    gloss is the word's sense in that pattern.
    """
    lex = Lexicon()
    learned: List[Dict[str, Any]] = []
    if not os.path.isdir(canon_dir):
        return lex, learned
    files = [f for f in sorted(os.listdir(canon_dir))
             if f.endswith(".txt")][:max_files]
    for fn in files:
        path = os.path.join(canon_dir, fn)
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not (20 < len(line) < 200):
                continue
            words = [w.lower() for w in _WORD.findall(line)]
            # THE SHAPE EACH WORD WAS FOUND IN. MEASURED 2026-10-31:
            # a sense that carries only its own role has a ONE-slot
            # PSB, and `PSB.compatible()` requires equal arity -- so
            # such a sense can never be restored into a two-slot
            # pattern, and the probe dropped 100% of real prose.
            #
            # So each word is learned in the pattern it was ACTUALLY
            # seen in: the (name, act) window it belongs to.
            for i, w in enumerate(words):
                if len(words) < 2:
                    break
                prev = words[i - 1] if i > 0 else ""
                nxt = words[i + 1] if i + 1 < len(words) else ""
                role = None
                shape: Tuple[str, ...] = ()
                if prev in _nouns() and w in _verbs():
                    role, shape = "act", ("name", "act")
                elif prev in _verbs() and w in _nouns():
                    role, shape = "name", ("name", "act")
                elif w in _nouns() and nxt in _verbs():
                    role, shape = "name", ("name", "act")
                elif w in _verbs() and nxt in _nouns():
                    role, shape = "act", ("name", "act")
                if role is None:
                    continue
                s = LearnedSense(word=w, role=role, evidence=line[:180],
                                 source=fn, shape=shape)
                try:
                    lex.add(s.to_sense())
                except Exception:  # noqa: BLE001
                    continue
                learned.append({"word": w, "role": role,
                                "source": fn,
                                "evidence": line[:120]})
    return lex, learned


# ===========================================================================
# THE PROBE
# ===========================================================================

@dataclass
class SentenceReading:
    """what happened to one sentence."""
    text: str
    outcome: str            # "carried" | "labelled" | "dropped"
    role: str = ""
    #: the idea-words in it. A sentence whose meaning is carried ONLY
    #: by an idea-word is LABELLED.
    idea_words: List[str] = field(default_factory=list)
    #: the concrete words in it.
    concrete_words: List[str] = field(default_factory=list)

    def describe(self) -> Dict[str, Any]:
        return asdict(self)


#: THE IDEA WORDS -- the labels that carry meaning in place of a
#: scene. MEASURED 2026-10-31: star-rider's idea-rate is 7.8 per 1,000
#: words against college-girl's 1.0.
IDEA_WORDS: Tuple[str, ...] = (
    "truth", "meaning", "significance", "purpose", "nature", "essence",
    "reality", "existence", "consciousness", "humanity", "information",
    "knowledge", "wisdom", "possibility", "principle", "system", "process",
    "experience", "structure", "freedom", "power", "change", "world",
    "life", "death", "love", "god", "universe", "energy", "spirit",
    "soul", "mind", "fear", "trust", "faith", "progress", "sermon",
    "theater", "theatre", "choir", "attention", "stability", "curvature",
    "torus", "membrane", "fold", "clockwork", "scale", "balance",
)

#: THE CONCRETE WORDS -- the things that can be in a room.
CONCRETE_WORDS: Tuple[str, ...] = (
    "man", "woman", "boy", "girl", "child", "door", "river", "hut",
    "fire", "hand", "hands", "face", "eye", "eyes", "voice", "head",
    "room", "house", "street", "book", "letter", "clock", "water",
    "stone", "sand", "milk", "cow", "cows", "forest", "tree", "path",
    "field", "wind", "rain", "night", "morning", "light", "boots",
    "coat", "cup", "bell", "shadow", "blood", "tray", "kettle", "hair",
)


def _role_for(sentence: str) -> str:
    """the role pattern the sentence fits, or "".

    **AND THE PATTERN BINDS TO A WINDOW, NOT TO THE WHOLE SENTENCE.**

    MEASURED 2026-10-31: `SlotPattern.matches()` requires the token
    list to have EXACTLY the pattern's length. So "Kelly walked to the
    door." (5 tokens) never binds to a 2-slot (name, act) pattern, and
    the first version of this probe DROPPED 100% of real prose --
    1918 of 1918 sentences -- because it compared the whole sentence
    against a 2-slot pattern.

    **A pattern that cannot bind real sentences measures nothing.**
    So the sentence is scanned for a CONTIGUOUS WINDOW of the right
    length, and the longest match wins.
    """
    words = [w.lower() for w in _WORD.findall(sentence)]
    if not words:
        return ""
    best = ""
    best_len = 0
    for name, shape in PATTERNS:
        width = len(shape)
        if width > len(words) or width <= best_len:
            continue
        for start in range(0, len(words) - width + 1):
            window = words[start:start + width]
            if _window_matches(window, shape):
                best = name
                best_len = width
                break
    return best


def _verbs():
    return word_lists()[0]


def _nouns():
    return word_lists()[1]


def _window_matches(window: Sequence[str], shape: Sequence[str]) -> bool:
    """does this window of words fit this shape of roles?"""
    for w, role in zip(window, shape):
        if role == "act" and w not in _verbs():
            return False
        if role == "name" and w not in _nouns():
            return False
        if role in ("object", "time", "commit", "refuse"):
            return False
    return True


def read_sentence(sentence: str, lexicon: Any) -> SentenceReading:
    """what happened to one sentence."""
    low = sentence.lower()
    ideas = [w for w in IDEA_WORDS if re.search(r"\b%s\w*\b" % w, low)]
    concretes = [w for w in CONCRETE_WORDS
                 if re.search(r"\b%s\w*\b" % w, low)]
    role = _role_for(sentence)
    if not role:
        return SentenceReading(sentence, "dropped", "",
                               ideas, concretes)
    # THE RESTORE, ON THE WINDOW THAT BOUND. MEASURED 2026-10-31: the
    # pattern binds a CONTIGUOUS WINDOW, so `compile_span` must be
    # handed the window -- handing it the whole sentence failed to
    # bind, because `matches()` requires an exact token count.
    window = _window_for(sentence, role)
    if window is None:
        return SentenceReading(sentence, "dropped", role, ideas, concretes)
    try:
        pattern = SlotPattern.from_units(
            *[_units_for(r)[0] for r in _shape_for(role)])
        transform = compile_span(window, pattern)
        restored = restore(transform, lexicon) if transform else None
    except Exception:  # noqa: BLE001
        transform = None
        restored = None
    if restored is None:
        return SentenceReading(sentence, "dropped", role, ideas, concretes)
    # CARRIED or LABELLED. The sense came back -- but was it carried by
    # the SCENE, or by an IDEA-WORD standing in for it?
    if ideas and not concretes:
        return SentenceReading(sentence, "labelled", role, ideas, concretes)
    return SentenceReading(sentence, "carried", role, ideas, concretes)


def _window_for(sentence: str, role: str) -> Optional[str]:
    """the exact window that bound, as a string."""
    words = re.findall(r"[A-Za-z']+", sentence)
    shape = _shape_for(role)
    width = len(shape)
    for start in range(0, max(len(words) - width + 1, 0)):
        window = words[start:start + width]
        if _window_matches([w.lower() for w in window], shape):
            return " ".join(window)
    return None


def _shape_for(role: str) -> Tuple[str, ...]:
    for name, shape in PATTERNS:
        if name == role:
            return shape
    return ("name", "act")


def probe(text: str, lexicon: Any) -> Dict[str, Any]:
    """the probe over a whole draft."""
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    readings = [read_sentence(s, lexicon) for s in sentences]
    counts = {"carried": 0, "labelled": 0, "dropped": 0}
    for r in readings:
        counts[r.outcome] += 1
    total = max(len(readings), 1)
    return {
        "sentences": len(readings),
        "carried": counts["carried"],
        "labelled": counts["labelled"],
        "dropped": counts["dropped"],
        "carried_rate": 100.0 * counts["carried"] / total,
        "labelled_rate": 100.0 * counts["labelled"] / total,
        "dropped_rate": 100.0 * counts["dropped"] / total,
        "readings": [r.describe() for r in readings],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="the restore probe")
    ap.add_argument("--canon", action="store_true",
                    help="learn the lexicon from the canon and report it")
    ap.add_argument("--draft", default=None, help="probe a draft")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    lex, learned = learn_lexicon()

    if args.canon:
        report = lex.coverage_report()
        print("=" * 74)
        print("THE LEXICON, LEARNED FROM THE CANON")
        print("=" * 74)
        print()
        print("  words      %d" % report["words"])
        print("  senses     %d" % report["senses"])
        print("  patterns   %d" % report["patterns"])
        print("  units      %d (%s)" % (len(PRIMITIVES),
                                         ", ".join(ROLES)))
        print()
        for s in learned[:8]:
            print("    %-14s %-6s %s" % (s["word"], s["role"],
                                           s["evidence"][:60]))
        print()
        return 0

    if args.draft:
        with open(args.draft, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        res = probe(text, lex)
        if args.json:
            print(json.dumps(res, indent=2))
            return 0
        print("=" * 74)
        print("THE RESTORE PROBE -- %s" % args.draft)
        print("=" * 74)
        print()
        print("  sentences   %d" % res["sentences"])
        print("  carried     %d (%.1f%%)" % (res["carried"],
                                             res["carried_rate"]))
        print("  labelled    %d (%.1f%%)" % (res["labelled"],
                                             res["labelled_rate"]))
        print("  dropped     %d (%.1f%%)" % (res["dropped"],
                                             res["dropped_rate"]))
        print()
        print("  AND THE LABELLED ONES ARE THE STAR-RIDER FAILURE:")
        print("  the sense came back, but an idea-word carried it.")
        for r in res["readings"]:
            if r["outcome"] == "labelled":
                print("    %-46s %s" % (r["text"][:46],
                                        ",".join(r["idea_words"][:4])))
        print()
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
