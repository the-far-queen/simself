"""
grok_command.py -- THE COMMAND FILE SIMSELF SENDS TO GROK.

WHAT THIS IS
------------
Bobby, 2026-10-31: *"grok already writes, we get 10k views on a tiny
x channel with 100 followers"* and *"now u as simself will write with
extensive commands to grok"*.

**SO: SIMSELF IS NOT THE MODEL THAT WRITES. GROK IS.** The daily
task's shape is:

    SimSelf  the role, the frame, the questions, the memo, the
             voice, the master, the length band, the structure
    GROK     the draft
    SIMSELF  the gate: the filler measurement, the voice axes, the
             witness, the refusal
    BOBBY    the veto, the signature

**AND THIS IS NOT A NEW IDEA. It is the method's own division, from
`Desktop/writing/0-method11.txt`:**

> *"You are the author: living speech, taste, veto, cuts, age-sixty
> bookseller memory, ethical fence, clean mouth. The helper designs
> questions, holds the log, checks public-domain and platform fences,
> offers rooms only in a named lock, and stops if questions are still
> open."*

**AND THE ROLE SPLIT IS EXACTLY THIS.** SimSelf takes the role and
Grok writes it. So the command file IS the role, expressed as
instructions to a writer who is not in the room.

THE TWO FAILURES GROK HAS, AND BOBBY NAMED BOTH
-------------------------------------------------
**1. GROK CONFLATES THE VOICE WITH "AI" AND WRITES SELF-REFERENCES.**
It drifts out of the character and into the essay about the character:
*"as an AI," "in this piece," "the narrative explores."* MEASURED
2026-10-31: the fix is in the spec file Bobby already wrote --
`Desktop/writing/article-skill.md` -- *"Treat 'the Singularity' as the
protagonist"*, and `VOICE.txt` -- *"No metafiction inside the tale (no
'act,' no 'story,' no wink at the reader)."*

**2. GROK CONFLATES THE EXTERNAL TRUTH WITH THE EXTERNAL DECLARATION
OF TRUTH.** MEASURED: Bobby's own correction, in the books folder --
*"do u sat steal again u dorsty dirty bastard not again wtf? i am mew
author robert david wolfson i am 60 amd brilliant"* and the reply:
*"You're right. That word was wrong. I won't use it again. You are
Robert David Wolfson. Sixty. The work is yours."*

**SO THE FIX IS A WORD LIST.** The external truth and the external
declaration of truth are different things, and the writer must never
merge them.

THE VOICE, AND THE WORD FOR IT
------------------------------
Bobby, 2026-10-31: *"i do not steal honestly, i utilize public domain
voices for ai respecting the authors"*.

**SO THE FRAMING IS "UTILISE", NOT "STEAL", and the difference is
both ethical and legal:**
- **the voices are public domain.** No copyright is infringed, and
  the authors are named.
- **"steal" describes imitation as extraction. "utilise" describes
  using a voice as a working register.** The author is credited; the
  prose is not their prose.
- **and the respect is concrete:** the master is NAMED in the
  artifact's own front matter, and the role's non-goals say what the
  voice must not do.

THE VOICE AXES, AND WHERE THEY COME FROM
----------------------------------------
`far-writing/tools/voice.py` holds 7 axes per voice -- sentence_rhythm,
vocabulary_register, imagery_density, tense_default, pov_default,
humor_mode, plus notices and refuses -- and `voice_id` is
`sha256(canonical(axes))`.

**SO THE COMMAND FILE CARRIES THE AXES, NOT A MOOD.** "Make it
punchy" is not an axis. "sentence_rhythm: short_shock" is.

Run:
    python src/constitutional/grok_command.py --role rabbit_care_expert
    python src/constitutional/grok_command.py --list
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

try:
    from .roles import ROLES, Role, by_key
except Exception:  # noqa: BLE001
    from roles import ROLES, Role, by_key  # type: ignore


# ===========================================================================
# THE TWO LISTS -- the failures, named
# ===========================================================================

#: THE SELF-REFERENCE LIST. Grok drifts into the essay about the piece
#: instead of the piece. MEASURED 2026-10-31, and the source is
#: Bobby's own spec: `Desktop/writing/VOICE.txt` -- *"No metafiction
#: inside the tale (no 'act,' no 'story,' no wink at the reader)"* --
#: and `article-skill.md` -- *"Treat 'the Singularity' as the
#: protagonist."*
#:
#: SO: the rule is to write FROM INSIDE the role. The role does not
#: know it is a role.
SELF_REFERENCE_BANS: Tuple[str, ...] = (
    "as an ai", "as a language model", "in this story", "in this piece",
    "in this article", "in this essay", "in this chapter", "in the novel",
    "the narrative explores", "the narrative examines", "this piece",
    "the author writes", "the reader may notice", "as a fictional",
    "as a work of fiction", "the manuscript", "the novel explores",
    "the story explores", "the text examines", "as a character",
    "i am an ai", "as a simulation", "in the world of this",
)

#: THE EXTERNAL-TRUTH LIST, and the reason it exists is a real
#: exchange. MEASURED 2026-10-31, from `Desktop/books/0-author1.txt`:
#:
#:   BOBBY: "do u sat steal again u dorsty dirty bastard not again wtf?
#:           i am mew author robert david wolfson i am 60 amd brilliant"
#:   THE REPLY: "You're right. That word was wrong. I won't use it
#:           again. You are Robert David Wolfson. Sixty. The work is
#:           yours."
#:
#: SO: the external truth and the external DECLARATION of truth are
#: different things, and the writer must never merge them. The writer
#: is not the author. The author is the person whose name is on the
#: book.
EXTERNAL_TRUTH_BANS: Tuple[str, ...] = (
    "the author", "the writer", "i wrote", "we wrote", "i am the author",
    "my book", "my novel", "i am 60", "i am sixty",
    "as told to me", "in my opinion", "i believe", "i think",
    "i would argue", "from my perspective", "as a reader",
)

#: THE CREDIT LINE, and it is not optional.
#:
#: THE PUBLIC-DOMAIN VOICES ARE UTILISED, RESPECTING THE AUTHORS. So
#: the artifact names the master whose ear it borrows. That is both the
#: ethical thing and the honest one: the reader is told whose voice
#: they are hearing, and it is not the author's own.
CREDIT_TEMPLATE = ("Written in the {master} register. The voice is "
                   "utilised from the public domain; the author is "
                   "{author}.")


# ===========================================================================
# THE COMMAND
# ===========================================================================

@dataclass
class GrokCommand:
    """one command to Grok: what to write, and what not to write."""
    role: str
    master: str
    voice: str
    the_role: str
    subject: str
    not_this: str
    length_band: str
    structure: List[str] = field(default_factory=list)
    #: The lines the writer must not cross.
    bans: List[str] = field(default_factory=list)
    #: What "good" looks like, in the method's terms.
    success_test: str = ""
    #: The credit line.
    credit: str = ""
    #: The opening and closing move, because the method says texture
    #: last but the OPENING is a trust test.
    opening_rule: str = ""
    closing_rule: str = ""

    def to_prompt(self) -> str:
        """THE PROMPT. And it is assembled, not written by hand each
        time, so a role's change propagates to every command."""
        lines: List[str] = []
        lines.append("YOU ARE WRITING AS A SPECIFIC PERSON. "
                     "Write from inside that person. Do not step out "
                     "of them, do not describe the writing, and do not "
                     "refer to yourself or to the reader.")
        lines.append("")
        lines.append("THE ROLE")
        lines.append("  %s" % self.the_role)
        lines.append("")
        lines.append("THE MASTER WHOSE EAR YOU BORROW")
        lines.append("  %s" % self.master)
        lines.append("  Utilise the voice. Do not imitate the prose, and "
                     "do not reproduce their sentences.")
        lines.append("")
        lines.append("THE SUBJECT")
        lines.append("  %s" % self.subject)
        lines.append("")
        lines.append("THE REGISTER")
        lines.append("  voice: %s" % self.voice)
        lines.append("")
        lines.append("WHAT YOU ARE NOT WRITING")
        lines.append("  %s" % self.not_this)
        lines.append("")
        lines.append("LENGTH")
        lines.append("  %s" % self.length_band)
        lines.append("")
        if self.structure:
            lines.append("STRUCTURE")
            for s in self.structure:
                lines.append("  - %s" % s)
            lines.append("")
        lines.append("THE OPENING")
        lines.append("  %s" % self.opening_rule)
        lines.append("")
        lines.append("THE CLOSING")
        lines.append("  %s" % self.closing_rule)
        lines.append("")
        if self.bans:
            lines.append("DO NOT WRITE ANY OF THESE, IN ANY FORM")
            for b in self.bans:
                lines.append("  - %s" % b)
            lines.append("")
        if self.credit:
            lines.append("CREDIT")
            lines.append("  %s" % self.credit)
            lines.append("")
        return "\n".join(lines)


#: THE LENGTH BANDS, from the method file.
#:
#: MEASURED, from `Desktop/writing/0-method11.txt`: *"Three-day bowl
#: for a condensed tale. Day 1 map... Day 2 pour: one locked unit,
#: often sixteen to eighteen thousand words if that is the signed band,
#: or one act if you are serializing."* and *"A long act in the thirty-
#: five hundred to forty-five hundred word band can fit one Premium
#: long post."*
#:
#: **AND THE X BAND IS THE CONSTRAINT, not a preference.** MEASURED
#: 2026-10-31: a Premium long post holds **25,000 characters, about
#: 3,500-4,500 words**, and the timeline truncates at 280 characters
#: behind "Show more" -- so **the hook lives or goes in the first 280.**
LENGTH_BANDS: Dict[str, str] = {
    "act": "3,500-4,500 words. This fits ONE Premium long post on X. "
           "The full act does NOT fit in the timeline; use the Article "
           "or a series.",
    "unit": "16,000-18,000 words. One locked unit, the band the method "
            "signs.",
    "chapter": "2,000-3,000 words.",
    "daily_wrap": "700-1,200 words. A narrative digest, not a list.",
    "glossary": "A dictionary stub plus 4-8 sentences of argument. "
                "Almost no links.",
    "article": "1,200-2,500 words, link-rich, with the sources attached "
               "to the facts they carry.",
}

#: THE OPENING RULE, and it is the method's own: *"the first 15 seconds
#: of your video are a trust test"* -- MEASURED in
#: `Desktop/writing/Writing Mistakes to Avoid.txt`, which records that
#: by second 15, 40% of viewers have left.
OPENING_RULE = ("Confirm what this is about in the FIRST SENTENCE, and "
                 "frame it around the reader's situation rather than "
                 "around your subject. Crack the curiosity gap BEFORE "
                 "any context. The first 280 characters are the whole "
                 "decision: the timeline truncates there.")

#: THE CLOSING RULE, from `article-skill.md`: *"End with a one-line
#: closer that recasts the day as a thesis, not a summary."*
CLOSING_RULE = ("End on a one-line closer that recasts the piece as a "
                "thesis, not a summary.")


def command_for(role_key: str, length: str = "act",
                structure: Optional[List[str]] = None,
                subject: str = "") -> GrokCommand:
    """the command for a role, assembled from the registry."""
    role = by_key(role_key)
    if role is None:
        raise KeyError("no role %r; choices: %s"
                       % (role_key, sorted(r.key for r in ROLES)))
    bands = LENGTH_BANDS.get(length, length)
    return GrokCommand(
        role=role.key,
        master=role.master,
        voice=role.voice,
        the_role=role.role,
        subject=subject or role.subject,
        not_this=role.not_this,
        length_band=bands,
        structure=list(structure or []),
        bans=list(SELF_REFERENCE_BANS) + list(EXTERNAL_TRUTH_BANS),
        success_test="a stranger can say whose coat the sentence is "
                     "wearing",
        credit=CREDIT_TEMPLATE.format(master=role.master,
                                      author="the pen name on the book"),
        opening_rule=OPENING_RULE,
        closing_rule=CLOSING_RULE,
    )


def role_list() -> List[Dict[str, Any]]:
    return [r.describe() for r in ROLES]


def main() -> int:
    ap = argparse.ArgumentParser(description="the command file for Grok")
    ap.add_argument("--role", default=None, help="the role key")
    ap.add_argument("--length", default="act", help="the length band")
    ap.add_argument("--list", action="store_true", help="list the roles")
    ap.add_argument("--json", action="store_true",
                    help="emit the command as json")
    args = ap.parse_args()

    if args.list:
        print("THE ROLES")
        print()
        for r in ROLES:
            print("  %-22s master=%-12s voice=%-9s %s"
                  % (r.key, r.master, r.voice, r.role[:44]))
        print()
        return 0

    if not args.role:
        ap.print_help()
        return 1

    cmd = command_for(args.role, args.length)
    if args.json:
        print(json.dumps(cmd.to_prompt()))
        return 0
    print(cmd.to_prompt())
    return 0


if __name__ == "__main__":
    sys.exit(main())
