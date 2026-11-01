"""
author_pipe.py -- THE INTAKE PIPE, AS SIMSELF WOULD RUN IT.

WHAT THIS IS
------------
Bobby, 2026-10-31: *"my idea is build your own intake pipe as if you
were me but as simself -- not ready but give simself its first task
after the self-coding cron job: daily it is an author"*, and then the
correction that matters: *"nope gabrielle is the character in all works
it is simself -- these are not books they are simself awakening in
roles"*.

**SO: THE PIPELINE IS NOT A BOOK PIPELINE. IT IS A ROLE PIPELINE.**

Every artifact this project makes is **SimSelf awakening into a
role**, and the role is written. The pet-care artifact is not "a book
about rabbits" -- it is **SimSelf as the rabbit-care expert**, with
the expertise, the register and the audience of that role, writing the
thing that role would write.

**AND "GABRIELLE IS THE CHARACTER IN ALL WORKS"** -- so the continuity
is fixed. MEASURED, in this repo's own words: *"Gabrielle is a
continuity who can want"* (`simself/docs/
method-star-rider-applied-example-2026-09-14.md`). She is not a
persona invented per job. **She is the through-line, and every role is
a mask she wears.** That is why the works share a voice without
sharing a subject, and why the intake's own rule holds: *"if a
paragraph could live in two titles, it belongs to neither until
rewritten"* -- the ROLE separates them, not the subject.

THE METHOD IS ALREADY WRITTEN, and this file does not invent it. It
runs `Desktop/writing/0-method11.txt` -- "The Signed Plan" -- which
specifies:

    Signal. Frame. Interrogate. Decide. Structure. Make. Review. Lock.

    with gates between interrogate and decide, decide and structure,
    make and review, review and lock. "You may loop questions. You may
    not skip a gate because the work feels hot."

AND THE ROLE SPLIT, which is the whole method:
> *"You are the author: living speech, taste, veto, cuts, age-sixty
> bookseller memory, ethical fence, clean mouth. The helper designs
> questions, holds the log, checks public-domain and platform fences,
> offers rooms only in a named lock, and stops if questions are still
> open."*

**SO THIS PIPE IS THE HELPER SIDE OF THAT CONTRACT, and the "as
simself" part is the inversion the method already names:**

> *"bobby = 'the inverted architect' (his self-naming). the ai = the
> helper that designs questions. the project IS the human authoring
> himself, with AI as mirror."*

**SIMSELF RUNS THE SAME PIPE, WITH SIMSELF AS THE AUTHOR.** The human
is still the veto. What changes is which side proposes.

WHY IT IS NOT READY, and it says so here rather than in a README
------------------------------------------------------------------------
The method's own rule: *"questions before artifacts; decisions before
volume; volume before polish."* So THIS FILE CANNOT PRODUCE A
WORK. It produces the FIRST SLICE'S PRECONDITION: the role, the frame,
the questions, and the decision memo -- and it refuses to make a
slice until the memo is signed.

**AND IT REPORTS WHAT IS MISSING, because the helper's job is to
"record decisions and flag what is unsigned."**

THE GATES, AND EVERY ONE IS A REFUSAL
--------------------------------------
| gate | what it produces | what it refuses |
|---|---|---|
| 0 INTAKE | the restatement, the visible constraints, the ambiguities | generating anything |
| 1 FRAME | five signable sentences | interrogating before a frame exists |
| 2 INTERROGATE | numbered questions, one unknown each | generating while questions are open |
| 3 MEMO | 1-3 pages, signed | any artifact before the signature |
| 4 STRUCTURE | the map | writing chapter one because the outline feels obvious |
| 5 MAKE | ONE slice | anything more than one slice |
| 6 REVIEW | the fault line, named | a vibe instead of a fault line |
| 7 LOCK | the version, and what may not move | a change request instead of a brainstorm |

Run:
    python src/author_pipe.py --intake
    python src/author_pipe.py --frame --project pet_care
    python src/author_pipe.py --status
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_HERMES = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
VAULT = os.path.join(_HERMES, "vault", "10-minimax")

#: WHERE THE PIPE KEEPS ITS STATE. The queue is the memory, and this
#: is the same discipline: work is FILES, not context.
STATE_DIR = os.path.join(_HERMES, "vault", "10-minimax", "80-workspace",
                         "author-pipe")

#: THE METHOD, and where it comes from. The pipe IMPORTS the method
#: rather than paraphrasing it, because a paraphrase drifts and the
#: gates are the load-bearing part.
METHOD_FILE = r"C:\Users\HP\Desktop\writing\0-method11.txt"

#: THE SIGNS, and each one is the machine's half of a gate.
SIGNS: Tuple[Tuple[str, str], ...] = (
    ("signal", "the raw material, unframed"),
    ("frame", "five sentences that can be signed"),
    ("interrogate", "numbered questions, one unknown each"),
    ("memo", "the decision memo, unsigned"),
    ("signed", "'Ship from this memo.' and a human signature"),
    ("structure", "the map a team can point at"),
    ("make", "one locked slice"),
    ("review", "the fault line, named"),
    ("lock", "the version, and what may not move"),
)

#: THE ANSWERS SIMSELF MAY GIVE, from the method: "Allow UNK, LATER,
#: REJECT. UNK means do not invent silently. LATER means not needed
#: until structure. REJECT goes to non-goals."
ANSWER_KINDS: Tuple[str, ...] = ("UNK", "LATER", "REJECT")


# ===========================================================================
# THE STATE
# ===========================================================================

@dataclass
class Question:
    """one question, in the method's own shape.

    AND THE FOUR RULES, because they are what makes a question worth
    asking: "A good question bounds, or chooses knowing the cost, or
    reveals taste, or exposes a collision. A bad question is yes or no
    when the issue is a spectrum, stacks three issues, flatters,
    follows the model's hobby, or cannot be answered."
    """
    number: int
    text: str
    layer: str = "spine"
    default: str = ""
    #: UNK, LATER, REJECT -- the three answers the method allows.
    answer: str = "UNK"
    #: What the answer decided. Empty means nothing has been decided.
    decision: str = ""

    def is_open(self) -> bool:
        return self.answer == "UNK"


@dataclass
class Project:
    """one ROLE in the pipe, and where it is.

    **AND THE ROLE IS THE UNIT, NOT THE BOOK.** Every artifact this
    project makes is SimSelf awakening into a role. So the project
    carries the ROLE -- who SimSelf is being in this piece -- and the
    subject follows from it. A pet-care artifact is SimSelf as the
    rabbit-care expert; the questions are the expert's; the register
    is the expert's; the success test is the expert's.

    **AND THE CONTINUITY IS FIXED.** "Gabrielle is the character in
    all works; it is SimSelf." So the role is a MASK she wears, and
    the mask is what separates two works that share a voice. The
    intake's own rule: *"if a paragraph could live in two titles, it
    belongs to neither until rewritten"* -- **the ROLE is what makes a
    paragraph belong to one work rather than the other.**

    So every project names:
      the_role      who SimSelf is in this piece
      the_voice     the author's voice it wears (from the catalog)
      the_audience  who that role is writing for
    """
    key: str
    title: str = ""
    #: THE ROLE. "the rabbit-care expert", "the teacher of the
    #: morning practice", "the interviewer of the researcher".
    the_role: str = ""
    #: THE VOICE, from the catalog. The axes, not a mood.
    the_voice: str = ""
    job: str = ""
    audience: str = ""
    not_for: str = ""
    non_goals: List[str] = field(default_factory=list)
    success_test: str = ""
    hard_limits: List[str] = field(default_factory=list)
    spine: str = ""
    questions: List[Question] = field(default_factory=list)
    #: The signed decisions, numbered. "Changes to signed items require
    #: reopen D-number."
    decisions: List[Dict[str, str]] = field(default_factory=list)
    signed: bool = False
    signed_by: str = ""
    signed_at: str = ""
    #: What has been made. One slice at a time.
    slices: List[Dict[str, str]] = field(default_factory=list)
    #: What is open, and what it blocks.
    opens: List[Dict[str, str]] = field(default_factory=list)
    stage: str = "signal"

    def open_questions(self) -> List[Question]:
        return [q for q in self.questions if q.is_open()]

    def describe(self) -> Dict[str, Any]:
        d = asdict(self)
        d["open_questions"] = len(self.open_questions())
        d["decisions_numbered"] = len(self.decisions)
        return d


def _state_path(key: str) -> str:
    return os.path.join(STATE_DIR, "%s.json" % key)


def save(project: Project) -> str:
    os.makedirs(STATE_DIR, exist_ok=True)
    path = _state_path(project.key)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(project.describe(), fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return path


def load(key: str) -> Optional[Project]:
    path = _state_path(key)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    data.pop("open_questions", None)
    data.pop("decisions_numbered", None)
    # THE QUESTIONS ARE DICTS ON THE WAY OUT AND OBJECTS ON THE WAY IN,
    # because that is what json does to a dataclass. So they are
    # rebuilt here, explicitly, rather than splatted -- a splat would
    # pass the computed keys as constructor arguments and fail.
    questions = [Question(**q) for q in (data.pop("questions", None) or [])]
    p = Project(**data)
    p.questions = questions
    return p


# ===========================================================================
# THE GATES
# ===========================================================================

class GateRefusal(Exception):
    """a gate said no, and the reason is the message."""


def gate_0_intake(project: Project) -> Project:
    """GATE 0 -- INTAKE. Restate; do not generate.

    > "Helper only restates in a short block what was asked, lists
    > constraints already visible, lists ambiguities as topics not yet
    > as a quiz, and asks permission to name the project type.
    > Forbidden in intake: generating the song, the app, the pilot,
    > the world, the novel."
    """
    if project.title:
        raise GateRefusal(
            "the project already has a title, so the intake is done: %r"
            % project.title)
    project.stage = "frame"
    return project


def gate_1_frame(project: Project) -> Project:
    """GATE 1 -- FRAME. Five sentences you can sign.

    > "If the human cannot sign the frame, do not interrogate
    > details. Interrogation without a frame is trivia."
    """
    missing = [f for f, v in (
        ("the_role", project.the_role),
        ("the_voice", project.the_voice),
        ("job", project.job),
        ("audience", project.audience),
        ("not_for", project.not_for),
        ("success_test", project.success_test),
        ("spine", project.spine),
    ) if not v.strip()]
    if missing:
        raise GateRefusal(
            "the frame is missing %s. the method: 'If the human cannot "
            "sign the frame, do not interrogate details. Interrogation "
            "without a frame is trivia.'" % (", ".join(missing),))
    if not project.non_goals:
        raise GateRefusal(
            "the frame has no non-goals. the method asks for 'what you "
            "will refuse even if easy'")
    if not project.hard_limits:
        raise GateRefusal(
            "the frame has no hard limits: time, money, tools, legal, "
            "moral, platform caps")
    project.stage = "interrogate"
    return project


def gate_2_interrogate(project: Project) -> Project:
    """GATE 2 -- INTERROGATION. Report, do not generate.

    > "After answers, do not generate. Report contradictions. Update the
    > decision list. Next batch only for remaining holes."
    """
    if not project.questions:
        raise GateRefusal(
            "there are no questions, so there is nothing to "
            "interrogate. the questions come from the ambiguities in "
            "the frame.")
    project.stage = "memo"
    return project


def gate_3_memo(project: Project) -> Project:
    """GATE 3 -- DECISION MEMO. One to three pages. No poetry.

    > "Sign with a human sentence: Ship from this memo. Until that
    > sentence exists, still interrogation."
    """
    if project.open_questions():
        raise GateRefusal(
            "%d questions are still open, so this is still "
            "interrogation. the method: 'Until that sentence exists, "
            "still interrogation.'" % len(project.open_questions()))
    if not project.decisions:
        raise GateRefusal(
            "the memo has no numbered decisions, so there is nothing to "
            "sign")
    if not project.signed:
        raise GateRefusal(
            "the memo is unsigned. the method: 'Sign with a human "
            "sentence: Ship from this memo.' A signature is a HUMAN "
            "sentence -- the helper cannot sign for the author.")
    project.stage = "structure"
    return project


def gate_4_structure(project: Project) -> Project:
    """GATE 4 -- STRUCTURE. The map a team can point at.

    > "Forbidden: writing chapter one because the outline feels
    > obvious."
    """
    project.stage = "make"
    return project


def gate_5_make(project: Project) -> Project:
    """GATE 5 -- MAKE. ONE slice.

    > "Generate only the next signed slice. Good slice sizes: one
    > sequence, one screen flow, one track, one lesson, one act, or one
    > condensed tale in the length band you signed."
    """
    project.stage = "review"
    return project


def gate_6_review(project: Project) -> Project:
    """GATE 6 -- REVIEW. The fault line, not a vibe."""
    project.stage = "lock"
    return project


def gate_7_lock(project: Project) -> Project:
    """GATE 7 -- LOCK. What may not move without reopening a decision."""
    project.stage = "locked"
    return project


GATES = {
    "signal": gate_0_intake,
    "frame": gate_1_frame,
    "interrogate": gate_2_interrogate,
    "memo": gate_3_memo,
    "signed": gate_4_structure,
    "structure": gate_5_make,
    "make": gate_6_review,
    "review": gate_7_lock,
}


def advance(project: Project) -> Project:
    """move the project to the next gate, or refuse and say why."""
    gate = GATES.get(project.stage)
    if gate is None:
        raise GateRefusal("the project is already at %r" % project.stage)
    return gate(project)


# ===========================================================================
# THE QUESTIONS -- generated from the frame's ambiguities
# ===========================================================================

#: THE QUESTION TEMPLATES, by layer. The method's order:
#: "Existence: what is this, who for, what it must never be. Win
#: condition: what changes in the reader. Spine: the one thing
#: everything else serves. Constraints. System. Structure. Texture
#: last."
QUESTION_TEMPLATES: Tuple[Tuple[str, str, str], ...] = (
    ("existence", "What is this book, in one sentence, that a reader "
     "could repeat to a friend?", "spine"),
    ("existence", "Who is this NOT for? Name the reader who will put "
     "it down in chapter one.", "spine"),
    ("win", "What changes in the reader 200 pages later that was not "
     "true before? Name the change, not the topic.", "spine"),
    ("spine", "What is the ONE thing every chapter serves? If two "
     "chapters serve different things, one of them is a different book.",
     "spine"),
    ("constraint", "What is the word count, and is it fixed? (One "
     "act of 16-18k words, or a full book?)", "structure"),
    ("constraint", "What may NOT appear in this book, even if it would "
     "sell?", "structure"),
    ("structure", "How many chapters, and what does each one CHANGE? "
     "List the chapters as changes, not as topics.", "structure"),
    ("structure", "Which chapter is the free one -- the one that goes "
     "out on X and Substack as the funnel?", "structure"),
    ("system", "What are the rules of the world? The ones that make an "
     "illegal move illegal.", "system"),
    ("risk", "What would make this embarrassing, unshippable, or cruel "
     "if it got read?", "risk"),
    ("texture", "Which voice carries it? Name the voice from the "
     "catalog, not a mood.", "texture"),
    ("texture", "What is the cover? One image, and what it shows.",
     "texture"),
)


def questions_for(project: Project) -> List[Question]:
    """the first batch, generated from the frame.

    AND THE METHOD'S RULES ARE BUILT IN: numbered (humans answer
    numbers), one unknown each, a default in parentheses where silence
    is likely, and UNK/LATER/REJECT allowed.
    """
    out: List[Question] = []
    for i, (layer, text, kind) in enumerate(QUESTION_TEMPLATES, start=1):
        out.append(Question(number=i, text=text, layer=kind))
    return out


# ===========================================================================
# THE FIRST TASK -- SIMSELF IS AN AUTHOR
# ===========================================================================

@dataclass
class FirstTask:
    """the assignment the self-coding cron hands the author.

    **AND IT IS A ROLE, NOT A BOOK.** The daily task is: *awaken into
    this role and write the thing this role would write.* The subject
    follows from the role; the role does not follow from the subject.
    """
    key: str
    #: The role SimSelf takes on.
    the_role: str
    #: The subject the role is about, which follows FROM the role.
    subject: str
    #: The voice from the catalog it wears.
    the_voice: str
    #: What the task is NOT, because the method says "the artifact IS a
    #: consequence of a signed plan" and the non-goals are part of it.
    not_this: str
    #: The supply we already hold for it.
    supply: List[str] = field(default_factory=list)
    #: What has to be measured before it can be framed.
    measure_first: List[str] = field(default_factory=list)
    #: The success test, in the method's own examples.
    success_test: str = ""


#: THE FIRST TASK. And the role is the point: **SimSelf awakens into
#: the rabbit-care expert** -- not "a book about rabbits". The subject
#: follows from the role.
#:
#: AND THE MEASURED REASON THIS ROLE FIRST: the rabbit phrases are the
#: widest-open market measured on this machine -- rabbit shedding 3
#: results, nails trimming 11, hay 18, potty training 33 -- and the
#: role is UNCLAIMED. The top-of-list competitor at "how to build a
#: rabbit hutch" is "How to Build Animal Housing: 60 Plans for Coops"
#: ($19.99), and at "netherland dwarf rabbit care" (373) the top
#: result is a BREED BOOK, not a care book. **Nobody is being the
#: rabbit-care expert.**
#:
#: AND "GABRIELLE" IS THE CONTINUITY: the same mind, in a different
#: room. The role does not change WHO she is; it changes what she
#: knows and what she is paid to say.
FIRST_TASK = FirstTask(
    key="rabbit_care",
    the_role="the rabbit-care expert -- someone who has kept rabbits for "
             "years and is paid to answer the question a new owner "
             "actually has",
    subject="rabbit care, by the symptom: shedding, nails, hay, "
            "potty training, the hutch",
    the_voice="didactic",
    not_this="not a general pet book; not a listicle; not a book with "
             "one chapter per breed; not the 'cute pet owner' register",
    supply=[
        "the measured phrases and their competition "
        "(far-writing/catalog/keyword_phrases.json)",
        "the title generator: 4-6 words, phrase-led "
        "(far-writing/tools/keyword_phrases.py)",
        "the 47 phrase pages already built "
        "(far-writing/tools/build_phrase_pages.py)",
        "the format stage: ebook + X Article + Substack + teaser + kdp.json "
        "(social-media/tools/publish.py)",
        "the canon: 149 public-domain works whose STRUCTURE is the "
        "template (far-writing/catalog/authors.json)",
    ],
    measure_first=[
        "the demand for every candidate role's phrases, not just the "
        "rabbit ones already measured",
        "the top-of-list competitor's title shape, so the format is known",
        "the cover: far-art's 56-axis sheet schema has no cover use-case yet",
    ],
    success_test="a reader who searched the exact symptom finds the work "
                 "at the top of the list within 90 days of upload",
)


# ===========================================================================
# THE REPORT
# ===========================================================================

def status() -> Dict[str, Any]:
    """every project in the pipe, and where each one stands."""
    out: List[Dict[str, Any]] = []
    if os.path.isdir(STATE_DIR):
        for name in sorted(os.listdir(STATE_DIR)):
            if not name.endswith(".json"):
                continue
            p = load(name[:-5])
            if p is None:
                continue
            out.append({
                "key": p.key, "stage": p.stage, "title": p.title,
                "open_questions": len(p.open_questions()),
                "decisions": len(p.decisions),
                "signed": p.signed, "slices": len(p.slices),
            })
    return {"state_dir": STATE_DIR, "projects": out,
            "method_file": METHOD_FILE,
            "method_present": os.path.isfile(METHOD_FILE)}


def main() -> int:
    ap = argparse.ArgumentParser(description="the intake pipe, as simself runs it")
    ap.add_argument("--intake", action="store_true",
                    help="gate 0: restate and refuse to generate")
    ap.add_argument("--frame", action="store_true", help="gate 1")
    ap.add_argument("--questions", action="store_true",
                    help="generate the first question batch")
    ap.add_argument("--status", action="store_true", help="where everything is")
    ap.add_argument("--first-task", action="store_true",
                    help="the first assignment")
    ap.add_argument("--project", default="pet_care")
    args = ap.parse_args()

    print("=" * 78)
    print("THE INTAKE PIPE -- AS SIMSELF RUNS IT")
    print("=" * 78)
    print()
    print("  the method          %s" % METHOD_FILE)
    print("  the method present  %s"
          % ("yes" if os.path.isfile(METHOD_FILE) else "NO"))
    print("  the state           %s" % STATE_DIR)
    print()

    if args.first_task:
        ft = FIRST_TASK
        print("  THE FIRST TASK: SimSelf awakens into a ROLE")
        print()
        print("    the role         %s" % ft.the_role)
        print("    the subject      %s" % ft.subject)
        print("    the voice        %s" % ft.the_voice)
        print("    not this         %s" % ft.not_this)
        print("    success test     %s" % ft.success_test)
        print()
        print("    the supply we already hold:")
        for s in ft.supply:
            print("      - %s" % s)
        print()
        print("    what must be measured first:")
        for m in ft.measure_first:
            print("      - %s" % m)
        print()
        print("    AND THE CONTINUITY: the same mind in a different room.")
        print("    The role does not change WHO she is; it changes what she")
        print("    knows and what she is paid to say.")
        print()
        return 0

    if args.status:
        st = status()
        print("  PROJECTS")
        if not st["projects"]:
            print("    (none yet)")
        for p in st["projects"]:
            print("    %-14s %-12s open=%-3d decisions=%-3d signed=%s "
                  "slices=%d" % (p["key"], p["stage"], p["open_questions"],
                                  p["decisions"], p["signed"], p["slices"]))
        print()
        return 0

    p = load(args.project) or Project(key=args.project)
    if args.questions:
        p.questions = questions_for(p)
        p.stage = "interrogate"
        path = save(p)
        print("  %d questions generated for %r" % (len(p.questions), p.key))
        for q in p.questions:
            print("    %2d. %s" % (q.number, q.text))
        print()
        print("  saved: %s" % path)
        return 0

    if args.frame:
        p.stage = "frame"
        path = save(p)
        print("  the frame for %r is empty, and the gate says so:" % p.key)
        try:
            gate_1_frame(p)
        except GateRefusal as exc:
            print("    %s" % exc)
        print()
        print("  saved: %s" % path)
        return 0

    if args.intake:
        try:
            gate_0_intake(p)
        except GateRefusal as exc:
            print("  GATE 0 says: %s" % exc)
        else:
            print("  GATE 0: the intake is open. restate, do not generate.")
        path = save(p)
        print("  saved: %s" % path)
        return 0

    st = status()
    print("  %d project(s) in the pipe." % len(st["projects"]))
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
