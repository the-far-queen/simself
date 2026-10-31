"""
mte.py -- Machine Transform Engine.

WHAT THIS IS NOT. It is not a translator. Translation maps one language
to another and loses meaning in the gap. MTE runs the same operation the
whole way: ambiguous natural language in, unambiguous bounded form out,
with the meaning RESTORED rather than approximated.

THE PROBLEM IT SOLVES, exactly. A model speaks a token subset of English.
The wall of matrix algebra between the token and the referent is opaque
to the model as well as to the human on the other side. So two minds that
are both intelligent and both trying still miscommunicate -- constantly,
in top labs, worldwide. There is no shared object to point at. This
module is that shared object.

WHY IT IS BUILDABLE AT ALL. Enumerating 30,000 words x ~5 senses is
150,000 nodes and nobody would survive that. Bobby's 25 years as an
English tutor is the cheat: English is CONSTRUCTED, not tabulated.
"john jumped" is [name verb]; so is "the compiler halted"; so is every
other well-formed sentence anyone has ever wanted to say. The 37
primitives in psb_primitives.py are the alphabet. A PSB is a SLOT
PATTERN over that alphabet, not a word. So the lexicon is generative --
30,000 words fall out of a few thousand patterns plus substitution
classes, exactly as a child acquires grammar rather than a word list.

THE SHEAF. MLTR lives outside the core, in its own sheaf, tightly
bounded. MTE is the edge between the unbounded sheaf (human English,
all of its ambiguity) and the bounded one. An edge, not a member.

THE TEST THAT PROVES IT. simself/tools/lexicon is a 35-word string
substitution table standing in for this entire module -- a crude,
lookup-table MTE. If MTE works, that filter's log rate goes to zero
because the transform carries the meaning cleanly, rather than staying
at zero because the model got lucky. Same measurement, better engine.

REFERENCES (spec, no code until now):
    docs/constitutional/mte-llm-wrapper-2026-09-14.md
    docs/mte-primitives-q26-35-2026-09-14.md
    papers/proposals/09-mte-machine-translation-engine-bidirectional-loss-2026-09-15.md
    papers/publishable/13-mte-llm-wrapper-safety-2026-09-15.md
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from . import psb_primitives
from .psb_primitives import PRIMITIVES, UnitType

__all__ = [
    "Slot", "PSB", "Sense", "SenseKey", "Transform",
    "SlotPattern", "Lexicon", "compile_span", "restore",
    "MTE_VERSION",
]

MTE_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# the atom
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Slot:
    """One typed slot in a Primary Semantic Block.

    A slot is a ROLE, not a word. `Slot("act")` means "an act happens
    here" and the act itself comes from the primitives. This is the
    whole trick: the slot is the compression, the primitive is the
    alphabet, and the pair covers English without enumerating it.
    """
    role: str
    unit: Optional[UnitType] = None

    def __post_init__(self):
        if not self.role or not re.fullmatch(r"[a-z][a-z_]{0,31}", self.role):
            raise ValueError(f"slot role must be lowercase slug: {self.role!r}")

    @property
    def id(self) -> str:
        raw = f"{self.role}|{self.unit.value if self.unit else '-'}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_json(self) -> Dict[str, Any]:
        return {"role": self.role,
                "unit": self.unit.value if self.unit else None,
                "slot_id": self.id}


@dataclass(frozen=True)
class PSB:
    """Primary Semantic Block: a pattern of slots, NOT a word.

    `PSB(("name", "act"))` is "someone does something" -- the pattern
    behind "john jumped", "the compiler halted", "she refused". The
    surface words bind to slots at transform time; the block itself is
    what both minds can point at.
    """
    slots: Tuple[Slot, ...]
    label: str = ""

    def __post_init__(self):
        if not self.slots:
            raise ValueError("a PSB needs at least one slot")

    @property
    def id(self) -> str:
        raw = "->".join(s.id for s in self.slots)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @property
    def roles(self) -> Tuple[str, ...]:
        return tuple(s.role for s in self.slots)

    def compatible(self, other: "PSB") -> bool:
        """True if `other` can instantiate this pattern.

        Every slot must be filled by a compatible role or unit. A
        two-slot block is NOT satisfied by a one-slot block -- that is
        the check that keeps "someone does something" from quietly
        accepting "something", which is exactly the ambiguity the
        engine exists to remove.
        """
        # EQUAL arity, not "at most". The first draft accepted a 1-slot
        # block against a 2-slot pattern, which means "user" alone
        # satisfied "someone does something" -- precisely the ambiguity
        # this module exists to remove. A shorter block is a DIFFERENT
        # meaning, not a partial match.
        if len(other.slots) != len(self.slots):
            return False
        for got, want in zip(other.slots, self.slots):
            if got.role != want.role:
                return False
            if want.unit is not None and got.unit != want.unit:
                return False
        return True

    def to_json(self) -> Dict[str, Any]:
        return {"psb_id": self.id, "label": self.label,
                "roles": list(self.roles),
                "slots": [s.to_json() for s in self.slots]}


@dataclass
class Sense:
    """One meaning of one word, in one context.

    snr is the operational-density score from Bobby's Sacred Library
    work: how good this sense is for the practitioner in THIS context,
    not how correct it is to a lexicographer.
    """
    word: str
    pos: str
    gloss: str
    context: str
    snr: float = 0.5
    psb: Optional[PSB] = None

    def __post_init__(self):
        if not (0.0 <= self.snr <= 1.0):
            raise ValueError(f"snr out of [0,1]: {self.snr}")

    @property
    def key(self) -> "SenseKey":
        return SenseKey(self.word.lower(), self.pos, self.context)


@dataclass(frozen=True)
class SenseKey:
    word: str
    pos: str
    context: str

    def __str__(self) -> str:
        return f"{self.word}/{self.pos}@{self.context}"


# ---------------------------------------------------------------------------
# the transform
# ---------------------------------------------------------------------------
@dataclass
class Transform:
    """One span's journey: source -> bound slots -> target.

    `restored` is the claim being checked, not a field to fill in. If
    the restore cannot reproduce the meaning from the slots alone, the
    transform did not work and must say so.
    """
    span: str
    psb: PSB
    slots: Dict[str, str] = field(default_factory=dict)
    sense_key: Optional[str] = None
    restored: Optional[str] = None
    snr: float = 0.0

    @property
    def lossless(self) -> bool:
        return bool(self.restored) and self.snr >= 0.5

    def to_json(self) -> Dict[str, Any]:
        return {"span": self.span, "psb": self.psb.to_json(),
                "slots": self.slots, "sense": self.sense_key,
                "restored": self.restored, "snr": round(self.snr, 4),
                "lossless": self.lossless}


_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")


class SlotPattern:
    """A slot pattern over the 37 primitives -- the generative move.

    `cause go stop up move left` from Bobby's Godot/robot-arm example:
    the primitives are not English words, they are the roles English
    words play. A pattern over them generalises to every English
    sentence that has that shape, which is how 150,000 nodes become a
    few thousand patterns.
    """

    def __init__(self, roles: Iterable[str], units: Iterable[Optional[UnitType]]):
        self.slots = tuple(Slot(r, u) for r, u in zip(roles, units))

    @classmethod
    def from_units(cls, *units: UnitType) -> "SlotPattern":
        return cls([u.value for u in units], list(units))

    @property
    def psb(self) -> PSB:
        return PSB(self.slots)

    def matches(self, tokens: List[str]) -> bool:
        """Does a token list instantiate this pattern?"""
        if len(tokens) < len(self.slots):
            return False
        return all(
            tok in self._forms(slot.unit, slot.role)
            for tok, slot in zip(tokens, self.slots)
        )

    @staticmethod
    def _forms(unit: Optional[UnitType], role: str) -> Set[str]:
        """the surface forms that fill a slot.

        **AND THE LEARNED LITERARY FORMS ARE READ HERE, AND ONLY
        HERE.** MEASURED 2026-10-31: the substrate's own alphabet is 31
        technical forms, so the engine could not bind literary prose
        (coverage 4.6%-28.5% on real prose, and 21.0% on the canon --
        so it could not carry the canon either).

        The learned forms live in `psb_primitives.LITERARY_FORMS` and
        are added to the substrate's own. **AND THE SUBSTRATE'S OWN
        FORMS ARE KEPT**, so the substrate's sentences still bind.

        **AND `PRIMITIVES` ITSELF IS NOT MUTATED.** MEASURED: putting
        the learned forms into `PRIMITIVES` changed `classify_span()`,
        and so weakened the confabulation filter -- which catches
        fluent-but-empty spans by spotting the ones that classify as
        OTHER. A change that improves the coverage number and weakens
        a safety check is not a change, so the vocabulary is read here
        instead.
        """
        forms: Set[str] = set()
        for u, words in PRIMITIVES.items():
            if unit is not None and u != unit:
                continue
            forms.update(words)
            if u.value == role:
                forms.add(u.value)
        # THE LEARNED FORMS, for the unit being matched.
        if unit is not None:
            forms.update(psb_primitives.literary_forms(unit.value))
        return forms

    def __repr__(self) -> str:
        return f"SlotPattern({'->'.join(s.role for s in self.slots)})"


def compile_span(span: str, pattern: SlotPattern) -> Optional[Transform]:
    """Bind an English span to a slot pattern. None if it does not fit."""
    tokens = [t.lower() for t in _WORD.findall(span)]
    if len(tokens) != len(pattern.slots):
        # Trailing tokens must be REFUSED, not dropped. The first draft
        # used zip(), which stops at the shorter sequence -- so a
        # 4-token span bound to a 2-slot pattern and lost two tokens
        # without saying so. Losing text silently is the failure this
        # engine is built to make impossible.
        return None
    if not pattern.matches(tokens):
        return None
    t = Transform(span=span, psb=pattern.psb)
    for tok, slot in zip(tokens, pattern.slots):
        t.slots[slot.role] = tok
    return t


def restore(t: Transform, lexicon: "Lexicon") -> Optional[Transform]:
    """Rebuild meaning from the slots. The claim under test.

    If the slots cannot carry the sense back, `restored` stays None and
    `lossless` is False. That is the engine admitting it failed, which
    is the only honest result available.
    """
    best: Optional[Sense] = None
    for role, tok in t.slots.items():
        for sense in lexicon.senses(tok):
            if sense.psb is not None and sense.psb.compatible(t.psb):
                if best is None or sense.snr > best.snr:
                    best = sense
    if best is None:
        return None
    t.sense_key = str(best.key)
    t.snr = best.snr
    t.restored = best.gloss
    return t


class Lexicon:
    """The corpus. Small by construction; generative by slot pattern."""

    def __init__(self, senses: Optional[List[Sense]] = None):
        self._senses: Dict[str, List[Sense]] = {}
        for s in senses or []:
            self.add(s)

    def add(self, sense: Sense) -> None:
        self._senses.setdefault(sense.word.lower(), []).append(sense)

    def senses(self, word: str) -> List[Sense]:
        return list(self._senses.get(word.lower(), []))

    def __len__(self) -> int:
        return sum(len(v) for v in self._senses.values())

    def coverage_report(self) -> Dict[str, int]:
        words = {w for v in self._senses.values() for s in v for w in [s.word.lower()]}
        patterns = {s.psb.id for v in self._senses.values() for s in v if s.psb}
        return {"words": len(words), "senses": len(self),
                "patterns": len(patterns)}
