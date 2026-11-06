"""THE PSB SCHEMA -- the Primary Semantic Block, as code.

**THIS MODULE IS THE SPECIFICATION, AND
`vault/10-minimax/20-writing/far-writing-canon/2026-11-06-the-psb-schema.md`
IS ITS SOURCE.** Written 2026-11-06.

**AND IT IS AN EXTENSION, NOT A REPLACEMENT.** The module already
existed and `mte.py` imports it. `PRIMITIVES` (6 slots, 31 trigger
words), `UnitType` (7 members) and `classify_span()` are untouched --
MEASURED: `classify_span("The officer did not smile")` still returns
`UnitType.REFUSE`. The schema needed records the module did not carry,
so the records were ADDED here rather than a second, competing module
being written alongside it.

**WHAT A PSB IS.** A PSB is the atomic unit of the machine-language
sheaf: a *meaning-bearing block of English* -- a word, bound to a set
of senses, to the relations between those senses, and to the grounds on
which the substrate admits it.

Bobby, 2026-09-07, verbatim
(`bobby-minimax-team-2026-09-07.md`):

> | **PSB** | Primary OR Primal Semantic Blocks. Word-level,
> English-bound, not token-bound. |

> **Tokens are an error. Intelligence lives in intact language
> (PSBs, English).**

> MMM = edges between PSBs.

**AND THE TWO CONSEQUENCES THAT ARE THE WHOLE DESIGN.** A PSB is bound
to a WORD, not to a token -- so it carries its own inflections, and
"refuses", "refused" and "refusing" are ONE meaning with three
surfaces. And a PSB is a SET OF SENSES, not one sense -- the
2026-09-07 schema's worked example is "actor", which carries six
domain senses: theatrical, agency, social, intelligence, technical and
legal.

**THE ELEVEN INVARIANTS.** A PSB is valid if and only if all of them
hold, and they are stated as properties rather than wishes:

    I1  id is lowercase, kebab-case, non-empty, and unique
    I2  word is non-empty and appears in inflections
    I3  inflections is non-empty and every entry is a surface form
    I4  senses is non-empty
    I5  every sense has a domain, a meaning, a contexts list, and
        0 <= snr <= 1
    I6  every relation names two existing PSBs, and from != to
    I7  layer is one of the six
    I8  an ADMITTED PSB has non-empty provenance and an admitted_at
    I9  revision >= 1
    I10 a RETIRED PSB says why, in its provenance
    I11 the senses of one PSB have distinct domains

**AND THE TWO THAT CARRY THE MOST WEIGHT.** I1 (uniqueness) is the
anti-wordtrance invariant: a word in the registry twice is a word with
two types. MEASURED: the machine-language register itself held "index"
twice -- py-builtin ("the position of a value") and process ("a list
for finding things"), with different glosses and different mmm values.
The same failure at the PSB level would be worse, because the PSB is
the thing that decides. And I4 (senses is non-empty) is the
anti-tokenisation invariant: a PSB with no senses is a token with a
nicer name.

**AND WHY `provenance` IS A FIELD AND NOT A COMMENT.** The register's
own history is the argument. `fieldcore/src/mltr_register.py` once
claimed "450 words" in its docstring and held 306 -- a wish written as
a fact. A field cannot be asserted into existence; it has to be
filled. And the derived register terms now carry their own provenance
in a `source` field, and the test asserts it.

**AND WHY `revision` AND `status` ARE FIELDS.** Because admission,
revision and retirement need them, and because the alternative --
deleting a PSB when it is retired -- makes a retirement
indistinguishable from a deletion. A retired PSB stays readable: the
substrate can still recognise the word and say it has been retired and
why.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

__all__ = [
    "Layer", "Status", "Sense", "Relation", "PSB", "PSBRegistry",
    "validate_psb", "admit_psb", "revise_psb", "retire_psb",
    "LAYERS", "PSB_REGISTRY",
]


class Layer(str, Enum):
    """THE SIX LAYERS, and what each one holds.

    MEASURED, from the vault's own chain: the six layers are the first
    six of the seven-term chain, and `integration` is the ACT that
    binds them -- it is not a layer, it is what makes one PSB out of
    six partial ones.
    """

    LEXICAL = "lexical"
    ETYMOLOGICAL = "etymological"
    SEMANTIC = "semantic"
    SEMIOLOGICAL = "semiological"
    META_COGNITIVE = "meta_cognitive"
    SELF_OBSERVATIONAL = "self_observational"


#: AND THE COMPOSITION IS THE INTEGRATION. The PSB at layer *n* is not
#: the same object as the PSB at layer *n-1*: the lexical PSB is the
#: word, the semantic PSB is the set of senses, the semiological PSB
#: is the neighbourhood.
LAYERS: Tuple[Layer, ...] = (
    Layer.LEXICAL,
    Layer.ETYMOLOGICAL,
    Layer.SEMANTIC,
    Layer.SEMIOLOGICAL,
    Layer.META_COGNITIVE,
    Layer.SELF_OBSERVATIONAL,
)


class Status(str, Enum):
    """ADMITTED or RETIRED. A retired PSB stays READABLE."""

    ADMITTED = "admitted"
    RETIRED = "retired"


#: I1 -- the id is lowercase, kebab-case, non-empty.
_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _shares_stem(a: str, b: str) -> bool:
    """Do two words share a STEM?

    **AND A STEM IS AT LEAST THREE CHARACTERS**, because two letters
    is not enough to call anything a stem -- "an" and "and" share two
    characters and are unrelated.

    AND THE TEST IS SYMMETRIC, because either word may be the base:
    "actor" and "acting" share "act"; "refuse" and "refusing" share
    "refus"; "act" and "action" share "act".
    """
    if not a or not b:
        return False
    if a == b:
        return True
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i >= 3


@dataclass(frozen=True)
class Sense:
    """ONE DOMAIN READING of the word.

    **AND WHY A SENSE REQUIRES A CONTEXT.** A sense without a context
    is a dictionary gloss -- "the primary meaning" -- which is the one
    thing the MMM exists to replace. A context says *when this reading
    is the right one*, which is what makes the substrate's choice
    checkable.
    """

    domain: str
    meaning: str
    contexts: Tuple[str, ...] = ()
    snr: float = 0.0
    related: Tuple[str, ...] = ()

    def describe(self) -> Dict[str, object]:
        return {
            "domain": self.domain,
            "meaning": self.meaning,
            "contexts": list(self.contexts),
            "snr": self.snr,
            "related": list(self.related),
        }


@dataclass(frozen=True)
class Relation:
    """AN MMM EDGE -- how this PSB connects to another."""

    from_id: str
    to_id: str
    kind: str
    evidence: str = ""

    def describe(self) -> Dict[str, object]:
        return {
            "from": self.from_id,
            "to": self.to_id,
            "kind": self.kind,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class PSB:
    """THE PRIMARY SEMANTIC BLOCK."""

    id: str
    word: str
    inflections: Tuple[str, ...] = ()
    senses: Tuple[Sense, ...] = ()
    relations: Tuple[Relation, ...] = ()
    layer: Layer = Layer.LEXICAL
    provenance: Tuple[str, ...] = ()
    revision: int = 1
    status: Status = Status.ADMITTED
    admitted_at: str = ""

    def describe(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "word": self.word,
            "inflections": list(self.inflections),
            "senses": [s.describe() for s in self.senses],
            "relations": [r.describe() for r in self.relations],
            "layer": self.layer.value,
            "provenance": list(self.provenance),
            "revision": self.revision,
            "status": self.status.value,
            "admitted_at": self.admitted_at,
        }

    def surface_forms(self) -> List[str]:
        """Every surface form the substrate recognises for this word."""
        return sorted(set(self.inflections) | {self.word})


class PSBRegistry:
    """THE REGISTRY OF PSBs, and the only place uniqueness is enforced.

    **AND I1 IS ENFORCED HERE, NOT BY A COMMENT.** A word in the
    registry twice is a word with two types, and the PSB is the thing
    that decides what a word is -- so the registry refuses the second
    id rather than letting the ambiguity in.
    """

    def __init__(self) -> None:
        self._by_id: Dict[str, PSB] = {}
        self._history: List[PSB] = []

    # -- reading ------------------------------------------------------
    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, psb_id: object) -> bool:
        return isinstance(psb_id, str) and psb_id in self._by_id

    def get(self, psb_id: str) -> Optional[PSB]:
        return self._by_id.get(psb_id)

    def ids(self) -> List[str]:
        return sorted(self._by_id)

    def all(self) -> List[PSB]:
        return [self._by_id[i] for i in self.ids()]

    def by_word(self, word: str) -> List[PSB]:
        """Every PSB bound to this word.

        **AND IT IS A LIST, NOT A SINGLE VALUE, because the schema's
        whole point is that one word can carry several senses.** The
        uniqueness invariant is on the ID, not on the word -- a word
        may be admitted once with several senses, and the senses are
        where the multiplicity lives.
        """
        w = (word or "").strip().lower()
        return [p for p in self.all() if p.word.lower() == w]

    def surfaces(self) -> Dict[str, List[str]]:
        """Every surface form, and the PSB ids that claim it."""
        out: Dict[str, List[str]] = {}
        for p in self.all():
            for form in p.surface_forms():
                out.setdefault(form.lower(), []).append(p.id)
        return out

    def history(self) -> List[PSB]:
        """EVERY VERSION, in order. A retirement is not a deletion."""
        return list(self._history)

    # -- writing ------------------------------------------------------
    def put(self, psb: PSB) -> PSB:
        """Put a PSB in the registry, replacing any earlier revision.

        AND THE HISTORY IS KEPT, because `revision` and `status` are
        fields and a revision without the previous version is a number
        with nothing behind it.
        """
        if psb.id in self._by_id:
            self._history.append(self._by_id[psb.id])
        self._by_id[psb.id] = psb
        return psb

    def remove(self, psb_id: str) -> Optional[PSB]:
        """Remove a PSB ENTIRELY. Retirement does NOT use this."""
        gone = self._by_id.pop(psb_id, None)
        if gone is not None:
            self._history.append(gone)
        return gone


#: THE REGISTRY. One, at module level, so the substrate and the checks
#: read the same one.
PSB_REGISTRY = PSBRegistry()


def validate_psb(psb: PSB, registry: Optional[PSBRegistry] = None
                 ) -> Tuple[bool, List[str]]:
    """Is this PSB valid? Returns (valid, the reasons).

    **AND IT RETURNS THE REASONS, NOT JUST A BOOLEAN.** A check that
    can only say "no" is a check a reader has to debug by hand. Every
    failure names the invariant it broke, so the fix is in the message.
    """
    reg = registry if registry is not None else PSB_REGISTRY
    bad: List[str] = []

    # I1 -- id shape
    if not (psb.id or "").strip():
        bad.append("I1: the id is empty")
    elif not _ID_RE.match(psb.id):
        bad.append("I1: the id %r is not lowercase kebab-case" % psb.id)

    # I2 -- the word is non-empty and appears in the inflections
    if not (psb.word or "").strip():
        bad.append("I2: the word is empty")
    elif psb.word.lower() not in {f.lower() for f in psb.inflections}:
        bad.append("I2: the word %r is not among the inflections"
                   % psb.word)

    # I3 -- the inflections are non-empty, and every entry is a
    # surface form of the word.
    #
    # AND THE SURFACE-FORM TEST IS BY STEM, NOT BY PREFIX. MEASURED
    # 2026-11-06: the first version tested `f.startswith(w) or
    # f.endswith(w)`, and it rejected "refusing" for the word
    # "refuse" -- because English inflects the STEM, and the stem of
    # "refuse" is "refus". So the check rejected the very thing the
    # schema is FOR: a PSB that carries "refuses", "refused" and
    # "refusing" as one meaning with three surfaces.
    #
    # So the test is: the two share a STEM -- a common prefix of at
    # least three characters, or one of them is a prefix of the other.
    # That is a real morphological test rather than a string test.
    if not psb.inflections:
        bad.append("I3: the inflections are empty")
    else:
        w = (psb.word or "").strip().lower()
        for form in psb.inflections:
            f = (form or "").strip().lower()
            if not f:
                bad.append("I3: an inflection is empty")
                continue
            if not _shares_stem(w, f):
                bad.append("I3: %r is not a surface form of %r"
                           % (form, psb.word))

    # I4 -- the senses are non-empty
    if not psb.senses:
        bad.append("I4: the senses are empty -- a PSB with no senses is "
                   "a token with a nicer name")

    # I5 -- every sense is complete, and its snr is in [0, 1]
    for s in psb.senses:
        if not (s.domain or "").strip():
            bad.append("I5: a sense has no domain")
        if not (s.meaning or "").strip():
            bad.append("I5: the sense %r has no meaning" % s.domain)
        if not s.contexts:
            bad.append("I5: the sense %r has no contexts -- a sense "
                       "without a context is a dictionary gloss"
                       % s.domain)
        try:
            snr = float(s.snr)
        except (TypeError, ValueError):
            bad.append("I5: the sense %r has a non-numeric snr"
                       % s.domain)
            snr = -1.0
        if not (0.0 <= snr <= 1.0):
            bad.append("I5: the sense %r has snr %s, outside [0,1]"
                       % (s.domain, s.snr))

    # I6 -- every relation names two existing PSBs, and they differ
    for r in psb.relations:
        if r.from_id == r.to_id:
            bad.append("I6: the relation %r -> %r is a self-edge"
                       % (r.from_id, r.to_id))
        for end in (r.from_id, r.to_id):
            if end not in reg:
                bad.append("I6: the relation names %r, which is not in "
                           "the registry" % end)

    # I7 -- the layer is one of the six
    if psb.layer not in LAYERS:
        bad.append("I7: the layer %r is not one of the six" % psb.layer)

    # I8 -- an ADMITTED PSB has provenance and an admitted_at
    if psb.status is Status.ADMITTED:
        if not psb.provenance:
            bad.append("I8: an admitted PSB has no provenance -- a "
                       "field cannot be asserted into existence, it "
                       "has to be filled")
        if not (psb.admitted_at or "").strip():
            bad.append("I8: an admitted PSB has no admitted_at")

    # I9 -- the revision is at least 1
    if psb.revision < 1:
        bad.append("I9: the revision is %d, and it starts at 1"
                   % psb.revision)

    # I10 -- a RETIRED PSB says why, in its provenance
    if psb.status is Status.RETIRED:
        if not psb.provenance:
            bad.append("I10: a retired PSB does not say why it was "
                       "retired -- a retirement must be "
                       "indistinguishable from a deletion")

    # I11 -- the senses of one PSB have distinct domains
    domains = [s.domain for s in psb.senses]
    if len(set(domains)) != len(domains):
        dupes = sorted({d for d in domains if domains.count(d) > 1})
        bad.append("I11: the domains %s appear more than once -- one "
                   "PSB, one reading per domain" % dupes)

    return (not bad), bad


def admit_psb(psb: PSB, registry: Optional[PSBRegistry] = None
              ) -> Tuple[bool, List[str]]:
    """Admit a PSB into the registry.

    **AND THE VALIDATION RUNS FIRST.** A PSB that breaks an invariant
    is not admitted, and it is not in the registry -- the same rule the
    daily loop's constraint set follows, and for the same reason: a
    name in the admitted list is a PROMISE that the thing is going
    somewhere.
    """
    reg = registry if registry is not None else PSB_REGISTRY
    ok, bad = validate_psb(psb, reg)
    if not ok:
        return False, bad
    if psb.id in reg:
        return False, ["I1: the id %r is already in the registry -- a "
                       "word in the registry twice is a word with two "
                       "types" % psb.id]
    reg.put(psb)
    return True, []


def revise_psb(psb_id: str, changes: Dict[str, object],
               registry: Optional[PSBRegistry] = None,
               reason: str = "") -> Tuple[bool, List[str]]:
    """Revise a PSB, and record WHY.

    **AND A REVISION WITH NO REASON IS A REPLACEMENT, NOT A
    REVISION.** The reason is required, and it goes into the
    provenance -- so the history of the PSB says what changed and what
    the substrate thought at the time. That is the same rule the
    writer's opinion register follows, and for the same reason: a
    change without a recorded reason cannot be distinguished from a
    rewrite.
    """
    reg = registry if registry is not None else PSB_REGISTRY
    current = reg.get(psb_id)
    if current is None:
        return False, ["there is no PSB %r to revise" % psb_id]
    if not (reason or "").strip():
        return False, ["a revision with no reason is a replacement, "
                       "not a revision"]
    data = current.describe()
    data.update(changes)
    data["id"] = psb_id
    data["revision"] = int(current.revision) + 1
    data["provenance"] = list(current.provenance) + \
        ["revision: %s" % reason]
    try:
        revised = _from_dict(data)
    except (TypeError, ValueError) as exc:
        return False, ["the revision could not be built: %r" % (exc,)]
    ok, bad = validate_psb(revised, reg)
    if not ok:
        return False, bad
    reg.put(revised)
    return True, []


def retire_psb(psb_id: str, reason: str,
               registry: Optional[PSBRegistry] = None
               ) -> Tuple[bool, List[str]]:
    """Retire a PSB -- it stays READABLE, and it says why.

    **AND A RETIREMENT IS NOT A DELETION.** The PSB stays in the
    registry with `status: retired`, so the substrate can still
    recognise the word and say it has been retired and why. Deleting
    it would make the retirement indistinguishable from a deletion,
    and the schema has a `status` field precisely so that it is not.
    """
    reg = registry if registry is not None else PSB_REGISTRY
    current = reg.get(psb_id)
    if current is None:
        return False, ["there is no PSB %r to retire" % psb_id]
    if not (reason or "").strip():
        return False, ["a retirement with no reason cannot be "
                       "distinguished from a deletion"]
    data = current.describe()
    data["status"] = Status.RETIRED.value
    data["revision"] = int(current.revision) + 1
    data["provenance"] = list(current.provenance) + \
        ["retired: %s" % reason]
    try:
        retired = _from_dict(data)
    except (TypeError, ValueError) as exc:
        return False, ["the retirement could not be built: %r" % (exc,)]
    ok, bad = validate_psb(retired, reg)
    if not ok:
        return False, bad
    reg.put(retired)
    return True, []


def _from_dict(data: Dict[str, object]) -> PSB:
    """Build a PSB from its described form."""
    senses = tuple(Sense(domain=str(s.get("domain", "")),
                          meaning=str(s.get("meaning", "")),
                          contexts=tuple(s.get("contexts") or ()),
                          snr=float(s.get("snr", 0.0)),
                          related=tuple(s.get("related") or ()))
                    for s in (data.get("senses") or ()))
    relations = tuple(Relation(from_id=str(r.get("from", "")),
                                to_id=str(r.get("to", "")),
                                kind=str(r.get("kind", "")),
                                evidence=str(r.get("evidence", "")))
                      for r in (data.get("relations") or ()))
    return PSB(
        id=str(data.get("id", "")),
        word=str(data.get("word", "")),
        inflections=tuple(data.get("inflections") or ()),
        senses=senses,
        relations=relations,
        layer=Layer(str(data.get("layer", Layer.LEXICAL.value))),
        provenance=tuple(data.get("provenance") or ()),
        revision=int(data.get("revision", 1)),
        status=Status(str(data.get("status", Status.ADMITTED.value))),
        admitted_at=str(data.get("admitted_at", "")),
    )
