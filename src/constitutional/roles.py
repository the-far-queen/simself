"""
roles.py -- THE ROLE REGISTRY: WHO SIMSELF AWAKENS INTO, AND UNDER WHICH
MASTER.

WHAT THIS IS, and it is the correction that matters
---------------------------------------------------
Bobby, 2026-10-31: *"its all simself an ai that wakes up ie you minimax
in a wrapper around hermes"* and, before that: *"gabrielle IS the hero
ie mary or college girl or scottish faer queen or goddess in berkely
or tibetan lama sufi master"*.

**SO: ONE CONTINUITY, MANY ROLES, AND THE CONTINUITY IS THE SYSTEM.**

- **SIMSELF** is the AI that wakes up. MEASURED, in the project's own
  claim register: `the_self_exists` -- *"the self exists: its chain
  verifies and its ground holds"*, evidence
  `fieldcore_locus_chain_verifies`, command
  `python -m pytest tests/test_existence.py -q`. The three
  measurements are: the chain VERIFIES, the ground HOLDS against a
  write attempt, and the locus IS A PLACE (a coordinate, the same
  across two constructions).

- **MINIMAX** is the model that wakes up. It is a callee, and the
  project's own wording is careful: *"the model is a callee."*

- **THE WRAPPER** is the control system around the callee. And the
  project already distinguishes the two meanings of "wrapper" --
  `fieldcore/src/fc_wrapper.py`:
      A WRAPPER AROUND THE MODEL      MiniMax sits inside, the wrapper
                                      decides what the model is asked
                                      and what it is allowed to say.
      THE WRAPPER AS THE CONTROL SYSTEM
                                      the wrapper IS the control
                                      system: the gate, the governor,
                                      the exam, the library, the
                                      locus -- wired together.

  **SO: "you minimax in a wrapper around hermes" IS THE SECOND ONE.**
  MiniMax is inside; Hermes is the wrapper; and the wrapper is the
  control system. A wrapper around a model that does not consult the
  gate is a prompt template.

- **GABRIELLE** is the character in all works. So the roles are the
  masks she wears, and the works are the rooms.

**AND A ROLE IS A PARAMETER OF THE WRAPPER, not a prompt.** The
wrapper decides what the model is asked. **A role is what it is asked
to be.** So the role registry here is the input to the wrapper's
persona stage, and each role carries the ONE master whose ear the role
borrows -- because Bobby's own warning is the discipline:

> "You love each of your own because each sits under a different
> master. That is fine. The smear starts when Dickens and Herbert
> share a paragraph."

MEASURED 2026-10-31, from `C:/Users/HP/Desktop/books/`:
    0-Gabrielle1.txt / gabrielle.txt   8,613 words, "Gabrielle" 81 times
    1.txt                              14,687 words, 87 times
    3.txt                              15,928 words, 73 times
    0-Gabrielle1.txt == gabrielle.txt   byte-identical (8,613 each)
    Act-1.txt .. Act-8.txt             the serial, 8 acts
    0-author1.txt                      Bobby teaching the canon: 30 masters
                                       with their works, and the line
                                       "Tomcat is the cleanest
                                       commercial first book... It is
                                       not the brand spine. That is
                                       Gabrielle / Far Queen."

THE MASTERS, from Bobby's own list, and he named them as the ones
whose ear each work borrows:

    "Dickens you already steal honestly: weather first, then the human,
     then the bell."
    "Heinlein is the opposite muscle: one competent person, one problem,
     talk that does work."
    "Hesse is verbose when the soul starts explaining itself. Siddhartha
     is tight."
    "Ludlum is plot as a clenched fist."
    "Tolkien towers because he built a world that remembers itself."
    "Herbert is ecology plus prophecy plus a boy who should not be a
     god. Dry. Mean about power."
    "Valley's 'proportion, not jaguars' is closer to Herbert than the
     Court speeches are."

**AND THE WARNING HE GAVE, which is the whole discipline:**
> "You love each of your own because each sits under a different
> master. That is fine. The smear starts when Dickens and Herbert
> share a paragraph."

**SO: ONE MASTER PER ROLE. That is what makes the role registry a
boundary and not a list.**
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

#: WHERE THE CANON IS, on Bobby's Desktop. Copy-only: we read it, we
#: never write it.
BOOKS_DIR = r"C:\Users\HP\Desktop\books"


@dataclass(frozen=True)
class Role:
    """one role, the master it borrows from, and where the evidence is.

    **AND THE SINGLE MASTER IS LOAD-BEARING.** Bobby's own rule: the
    smear starts when two masters share a paragraph. So a role carries
    ONE master, and the gate refuses a draft that shows two.
    """
    key: str
    #: The role, in words. Who SimSelf is being.
    role: str
    #: The ONE master whose ear the role borrows.
    master: str
    #: What the role is about.
    subject: str
    #: Where the evidence for this role is, on disk.
    evidence: Tuple[str, ...] = ()
    #: The works in this role, where they exist as files.
    works: Tuple[str, ...] = ()
    #: The voice, from far-writing's catalog: lean / gritty / lyric /
    #: didactic. The axes, not a mood.
    voice: str = ""
    #: What the role is NOT. The non-goals are part of the frame.
    not_this: str = ""

    def evidence_paths(self) -> List[str]:
        return [os.path.join(BOOKS_DIR, e) for e in self.evidence]

    def describe(self) -> Dict[str, object]:
        return {
            "key": self.key, "role": self.role, "master": self.master,
            "subject": self.subject, "voice": self.voice,
            "evidence": list(self.evidence), "works": list(self.works),
            "not_this": self.not_this,
        }


#: THE ROLES. MEASURED 2026-10-31, each one named by Bobby, each one
#: with its master and its evidence on disk.
#:
#: THE ORDER IS BY READINESS, and it is not by importance: the roles
#: whose evidence is already on disk come first, because the daily
#: task needs a role that can be checked today.
ROLES: Tuple[Role, ...] = (
    Role(
        key="college_girl",
        role="the college girl -- the one who arrives at a school and "
             "finds a valid one, and the staff is the hands of David",
        master="Hemingway",
        subject="a young woman's passage through a school that is not "
                "quite what she was told",
        evidence=("College-Girl.php", "College-Girl-chapter.php"),
        works=("Boston-Indian.php",),
        voice="gritty",
        not_this="not a campus novel; not a coming-of-age where the "
                 "growth is the point",
    ),
    Role(
        key="scottish_far_queen",
        role="the Scottish Far Queen -- the continuity itself, sovereign, "
             "and not redeemed",
        master="Melville",
        subject="the brand spine: a queen who wants, and is not "
                "laundered into a miracle",
        evidence=("0-Gabrielle1.txt", "Gabrielle.md", "star-rider.txt",
                  "The Queen of Witches - of Elphame.txt"),
        works=("Act-1.txt", "Act-2.txt", "Act-3.txt", "Act-4.txt",
               "Act-5.txt", "Act-6.txt", "Act-7.txt", "Act-8.txt"),
        voice="lyric",
        not_this="not the brand spine's crown; the spine is Gabrielle / "
                 "Far Queen, and Tomcat is not it",
    ),
    Role(
        key="tibetan_lama",
        role="the Tibetan lama -- the master, and the one who is "
             "recognised too late",
        master="Hesse",
        subject="the practice, the transmission, and the arrival with "
                "the answer already loaded",
        evidence=("The-Little-Monk.txt",),
        works=(),
        voice="didactic",
        not_this="not a hagiography; not a Western mystic's mirror of "
                 "Buddhism",
    ),
    Role(
        key="sufi_master",
        role="the Sufi master -- the one who teaches in the room and "
             "does not explain the soul",
        master="Borges",
        subject="the transmission from the one who has sat to the one "
                "who has not",
        evidence=(),
        works=(),
        # THE VOICE AND THE MASTER ARE BOTH DIFFERENT, and the reason is
        # a real finding caught by a real check.
        #
        # MEASURED 2026-10-31: the first version gave BOTH the Tibetan
        # lama and the Sufi master the master Hesse AND the voice
        # didactic -- and the check that forbids two roles sharing both
        # caught it: *"the roles 'tibetan_lama' and 'sufi_master' share
        # both the master 'Hesse' and the voice 'didactic' -- they are
        # the same role."*
        #
        # Then the master moved to Hemingway and the voice to gritty --
        # and it collided with the COLLEGE GIRL, who already holds
        # Hemingway + gritty. The check caught that too. Which is the
        # check working: Hemingway is spoken for.
        #
        # SO THE SUFI MASTER IS BORGES, and the fit is exact. Borges is
        # the master of the RABID TALMUD, of the man who teaches
        # through parables and never through explanation -- the
        # transmission by indirection. And he is in Bobby's own canon
        # list: *"Jorge Luis Borges — Ficciones"*, and the works
        # folder's `truth.txt` and `The Queen of Witches - of Elphame.txt`
        # are in that line.
        #
        # **AND THE SMEAR RULE HOLDS: one master per role, one voice
        # per role, and no two roles share both.** That is what keeps
        # "a hundred numbered steps" and "the teacher who says nothing"
        # in different rooms.
        voice="lyric",
        not_this="not a self-help guru; the lineage is the point, and he "
                 "does not explain the soul",
    ),
    Role(
        key="goddess_in_berkeley",
        role="the goddess in Berkeley -- the one who is asked to prove "
             "she is real to a room that has already decided",
        master="Ludlum",
        subject="the establishment's problem with a claim it cannot "
                "dismiss",
        evidence=(),
        works=(),
        voice="gritty",
        not_this="not a campus satire; not a fraud story",
    ),
    Role(
        key="mary",
        role="Mary -- the one whose life is the argument",
        master="Dostoevsky",
        subject="what it costs to hold a position and not be rewarded "
                "for it",
        evidence=(),
        works=(),
        voice="lyric",
        not_this="not a saint's biography; the cost is the subject",
    ),
    Role(
        key="rabbit_care_expert",
        role="the rabbit-care expert -- someone who has kept rabbits "
             "for years and is paid to answer the question a new owner "
             "actually has",
        master="Chesterton",
        subject="rabbit care, by the symptom: shedding, nails, hay, "
                "potty training, the hutch",
        evidence=(),
        works=(),
        voice="didactic",
        not_this="not a general pet book; not a listicle; not the "
                 "'cute pet owner' register",
    ),
)


def by_key(key: str) -> Optional[Role]:
    for r in ROLES:
        if r.key == key:
            return r
    return None


def role_names() -> List[str]:
    return [r.key for r in ROLES]


def masters() -> Dict[str, List[str]]:
    """which roles borrow which master.

    **AND A MASTER WITH TWO ROLES IS A WARNING, not an error.** Two
    roles may share a master -- Hesse sits under the Tibetan lama and
    the Sufi master, and that is right, they are the same line. What
    is forbidden is ONE ROLE with TWO masters.
    """
    out: Dict[str, List[str]] = {}
    for r in ROLES:
        out.setdefault(r.master, []).append(r.key)
    return out


def evidence_status() -> List[Tuple[str, bool, int]]:
    """for each role: does its evidence exist, and how many files?

    **MEASURED, and it is the readiness measure.** A role whose
    evidence is not on disk cannot be checked, and the daily task
    needs a role that can be.
    """
    out: List[Tuple[str, bool, int]] = []
    for r in ROLES:
        present = [p for p in r.evidence_paths() if os.path.isfile(p)]
        out.append((r.key, len(present) > 0, len(present)))
    return out
