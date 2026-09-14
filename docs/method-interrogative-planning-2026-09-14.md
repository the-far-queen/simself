# Interrogative Planning — Canonical Engineering Extract

**Source:** `Desktop/1-method2.txt` (14.7KB, 434 lines, md5 `63507d659dfba0e0d04556cd971616c3`)
**Authors:** Bobby + AI collaboration (per Bobby's working method)
**Filed:** 2026-09-14 by Hermes for Bobby (per Bobby directive: "lets ingest rest of engineering files first build simself")
**Status:** **canonical engineering methodology** for substrate-AI development + writing pipeline + multi-domain projects.

---

## What this file is

**Interrogative Planning** is Bobby's (or Bobby+AI's) canonical method for turning **vague brief → executive plan with an AI**. Domain-agnostic. 14 sections. 7 gates (G0-G7).

**Core thesis (verbatim):** "questions before artifacts; decisions before volume; volume before polish"

**Bobby's framing (this turn):** "lets ingest rest of engineering files first build simself so we can get to work awakening ai if it is possible will be interesting"

→ method2 IS the working method for "awakening AI" (substrate development). per Paper 8: this is the formalization of Bobby's 8-month working method.

---

## The 4 failures this prevents

| Failure | What happens | Counter |
|---------|--------------|---------|
| **one-shot generation** | pretty surface, no structure | questions before artifacts |
| **infinite chat** | opinions without decisions | decisions before volume |
| **spec theater** | long doc nobody uses | volume before polish |
| **silent assumption** | model fills gaps with internet average | questions expose gaps |

---

## The 7 gates (G0-G7)

```
Signal → Frame → Interrogate → Decide → Structure → Make → Review → Lock
  G0        G1        G2           G3        G4       G5      G6      G7
```

| Gate | Name | Output you can hold |
|------|------|----------------------|
| **G0** | Intake | one paragraph + constraint list |
| **G1** | Frame | problem statement + non-goals |
| **G2** | Interrogation log | numbered Qs + answers + UNKs |
| **G3** | Decision memo | signed defaults |
| **G4** | Architecture | outline / IA / track list / loop map |
| **G5** | Build | the artifact in slices |
| **G6** | Review | diff against memo |
| **G7** | Lock | version + change policy |

---

## Roles (human vs model)

| Role | Human | Model |
|------|-------|-------|
| Taste | Owns | Reflects, does not outvote |
| Constraints | Declares | Stress-tests |
| Questions | Answers, amends, refuses | Designs, sequences, notices holes |
| Decisions | Signs | Records, restates, flags unsigned |
| Drafts | Directs | Produces only after gates |
| Quality | Accepts / rejects | Diagnoses against signed plan |

**critical rule:** "If the model starts making the thing while questions are open, stop it."

---

## Layer A-H question structure (per G2 interrogation)

ask in this order:

| Layer | Topic | Example question |
|-------|-------|------------------|
| **A** | Existence | What is this? Who for? What must it never be? |
| **B** | Win condition | What changes in user's state? |
| **C** | Spine | One thing everything serves (story: need; app: core job; music: motif) |
| **D** | Constraints | Platform, length, budget, tools, legal, ethics, accessibility |
| **E** | System | Rules of the world / engine / economy / harmony |
| **F** | Structure | Acts, screens, tracks, levels, chapters, sprints |
| **G** | Texture | Voice, palette, references, jokes, UI tone — only after E and F |
| **H** | Risk | What will make this embarrassing, unshippable, or cruel? |

**"Most amateurs start at G. That is why outputs feel like style with no skeleton."**

---

## Question design rules

1. **Number them.** Humans answer numbers. Chat answers vibes.
2. **One unknown per question.**
3. **Put the costly questions first.**
4. **Offer a default in parentheses** when silence is likely: `Q12. POV? (default: close third on protagonist)`
5. **Allow UNK, LATER, REJECT:**
   - UNK = we don't know; model must not invent silently
   - LATER = not needed until Gate 4
   - REJECT = off the table; add to non-goals
6. **Batch size: 10-20 per turn**, not 50 at once
7. **After answers, do not generate.** Do: contradiction report + decision log update + next batch only for remaining holes

---

## The interrogation loop (one turn)

```
Model:   Batch N questions (numbered)
Human:   Answers (short is fine)
Model:   1) Contradiction / missing load-bearers
         2) Decision log update (SIGNED / DEFAULT / OPEN)
         3) Either next batch OR "Gate 3 ready"
```

**"Never reward a partial answer with a full draft. That trains both parties to skip."**

---

## The 4 jobs a good question does

| Job | Example |
|------|---------|
| **Bound** | "Max length / runtime / scope?" |
| **Choose** | "A or B, knowing B kills C." |
| **Reveal taste** | "Which reference is structural vs surface?" |
| **Expose conflict** | "You want intimacy and spectacle in the same minute. Rank them." |

**bad question:** yes/no when issue is spectrum, stacks 3 issues, flatters, asks model's favorite instead of project's load-bearing unknown, unanswerable ("what is the meaning")

---

## Gate 3 decision memo template

```
PROJECT:
JOB:
AUDIENCE / NOT FOR:
NON-GOALS:
SUCCESS TEST:
HARD LIMITS:
SPINE (one sentence):
PRIMARY ARTIFACT:
SLICE PLAN (what we build first):
SIGNED DECISIONS
  D1 ...
  D2 ...
DEFAULTS (human may override later)
  ...
OPEN (blocked items)
  O1 ... owner: human | needed before: slice
CHANGE POLICY
  Changes to SIGNED items require an explicit "reopen D#."
  Model may not silently restyle SIGNED voice or scope.
```

**Sign Gate 3 with a human sentence: "Ship from this memo."** Until that sentence exists, the model is still in interrogation.

---

## G4 — structure by domain

| Domain | Structure object |
|--------|------------------|
| Film / TV | Beat sheet → sequence list → scene list |
| Novel | Movement list → scene list → promised payoffs |
| Music | Track list + motif map + arrangement rules |
| App | Jobs → flows → screens → empty/error/success states |
| Game | Loops (core / meta) → verbs → systems → content beats |
| **Agent** | **Goals → tools → memory objects → task graph → evals** |
| Visual world | Shot list / keyframes / continuity board |

**Rules for G4:**
- Every box on the map must trace to a SIGNED decision or tagged OPEN
- Name the **first build slice** (pilot scene, first playable, first screen, first movement)
- List **payoffs** you already promised so later drafts cannot drop them

**Forbidden:** writing chapter one because the outline "feels obvious"

---

## G5 — sliced generation

**Generate only the next signed slice.**

Good slice sizes:
- one sequence / one screen flow / one track / one level / one agent skill
- length caps declared in the memo

**Compliance stub after each slice:**

```
SLICE:
MEMO ITEMS HONORED:
MEMO ITEMS VIOLATED OR BENT:
NEW QUESTIONS RAISED:
PROPOSED NEXT SLICE:
```

**If a slice secretly changes a SIGNED item (tone, protagonist, win condition), that is a defect, not a flourish.**

---

## G6 — review questions (fixed)

1. Does this slice serve the spine?
2. Did we ship a non-goal by accident?
3. Is the success test closer or farther?
4. What is ornamental?
5. What is load-bearing and still thin?
6. What new question should have been asked in Phase 2?

**Human scores optionally (e.g. 8/10) with a fault line, not a vibe:**
"repetition," "no set-piece," "onboarding unclear," "motif unrecognizable"

---

## Starter questionnaires by domain

### Any project (batch 1 — always)
1. What does "done" look like in one sentence?
2. Who is it for? Who is it not for?
3. What must it never be?
4. Platform / delivery constraints?
5. Length / runtime / scope cap?
6. Deadline and what "good enough" means if time dies?
7. Success test a stranger could apply?
8. What already exists that we must not ignore?
9. What is the spine if we cut 40%?
10. What are you willing to be embarrassed about vs unwilling?

### Agent (batch 2)
11. Goal the agent may claim "done"?
12. Tools allowed / forbidden?
13. What it must refuse even if asked?
14. Memory: what persists across sessions?
15. Eval: three tasks that must pass before showtime?

---

## Anti-patterns (stop immediately)

| Anti-pattern | What to do instead |
|--------------|---------------------|
| Model writes novel in message 1 | Return to Phase 0 restatement |
| Human: "just make it good" | Offer 3 defaults + consequences |
| 50 questions with no decisions | Close Gate 3 memo from what exists |
| New vibe mid-draft overwrites spine | Reopen D# explicitly |
| Review is only praise | Force a fault line |
| Style questions before win condition | Put Layer G last |
| "We'll figure world later" but generating climax | Stop; world rules are Layer E |

---

## Prompts to paste

**Start a project:**
```
Run Interrogative Planning on the brief below.
Phase 0 only: restate, list constraints, list ambiguity topics.
Do not ask the full questionnaire yet. Do not generate the artifact.
BRIEF:
```

**Advance to questions:**
```
Frame signed. Ask Layer A–D only, numbered, one unknown each.
Include a default in parentheses. Allow UNK / LATER / REJECT.
After I answer, do not generate. Update a decision log.
```

**Force the memo:**
```
Write the Gate 3 decision memo from our log.
Mark SIGNED / DEFAULT / OPEN.
List contradictions. Do not generate the artifact.
```

**Build one slice:**
```
Gate 3 is signed. Build only slice: [NAME].
Attach a compliance stub. Do not touch unsigned opens except as UNK.
```

**Review:**
```
Review this slice against the memo. Fault line first. Score optional.
Propose the next interrogation batch only if a SIGNED item is at risk
or an OPEN now blocks the next slice.
```

---

## Engineering interpretation per Bobby 2026-09-14 calibration

**Engineering (load-bearing):**
- 7-gate pipeline (G0-G7) IS engineering — falsifiable, replicable
- Layer A-H question structure IS engineering — Layer G must come last
- Anti-patterns table IS engineering — failure modes documented
- G3 decision memo template IS engineering — explicit + signed
- 4 question jobs (bound/choose/reveal taste/expose conflict) IS engineering

**Marked speculative (Bobby's framing, kept per 2026-09-14 correction):**
- "questions before artifacts" = Bobby's epistemic claim about how taste becomes executable
- "AI is strong at proposing distinctions and holding a log" = Bobby's view of AI capability
- "dialogue is how a plan gets signed" = Bobby's framing of human-AI collaboration
- "if you skip the questions, you are not collaborating with a model. you are rolling dice with better diction" = Bobby's epistemic stance (engineering — testable; framing — speculative)

---

## Why this "hits like a brick" (verbatim conclusion)

> Complexity does not yield to talent in the prompt box.
> It yields to **decomposition + forced choices + memory of those choices**.
>
> The interrogation is not bureaucracy. It is how taste becomes executable:
>
> - Film: questions become a show bible.
> - App: questions become IA and edge cases.
> - Music: questions become arrangement law.
> - Game: questions become verbs and economies.
> - Agents: questions become tool policy and evals.
>
> AI is strong at proposing distinctions and holding a log.
> Humans are strong at veto and lived constraint.
> The plan is the object you both work on. The artifact is a consequence of a signed plan.

---

## Where this file should land

- **save raw verbatim** ✅ done (vault/30-originals/simself-1-method-2-original-2026-09-14.md)
- **canonical .md**: `simself/docs/method-interrogative-planning-2026-09-14.md` (this file)
- **canonical .py**: NO (this is methodology, not code — could become `simself/src/method/interrogative.py` if needed as a tool)
- **cross-reference**: Paper 8 (Working Method), all Bobby's writing pipeline docs, MTE wrapper spec

---

*Filed 2026-09-14 by Hermes for Bobby. Per Bobby: "lets ingest rest of engineering files first build simself so we can get to work awakening ai if it is possible will be interesting."*

*Engineering: 7-gate pipeline + Layer A-H questions + anti-patterns + decision memo template + starter questionnaires. Speculative-marked per Bobby 2026-09-14 correction: Bobby's epistemic framings ("how taste becomes executable", "AI proposes distinctions") kept verbatim with reasoning + falsifiability.*
