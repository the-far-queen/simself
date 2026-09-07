# Human-AI Dictionary

> A working dictionary of terms that are *used differently* by humans and AIs — the same English word, different meaning. Per Bobby 2026-08-07: *"machine language tech register for ai human communication we use the same english words differently."*

**Source:** `Desktop/AI-Dictionary/dictionary.md` (scaffold from M3, 2026-08-08)
**Populated:** 2026-09-07 (30 observed entries from Bobby's session files)
**Status:** scaffold extended with first batch of real mismatches

---

## Purpose

The Human-AI Dictionary addresses a real problem: when a human says "kill this process" and an AI reads it, the same words land in two different semantic systems. The AI hears "termination of an active computation." The human might mean exactly that — or they might mean something else entirely (a joke, a metaphor, a venting). The *same English words* are doing different work in each speaker.

This is the *register mismatch* problem. It's not a new problem (machine translation has dealt with it for decades) but it's load-bearing for the SimSelf / agent-ecosystem work: if SimSelf modules are clothing to be worn by outside agents, and outside agents will encounter this register mismatch constantly, the dictionary is a load-bearing artifact.

## Two sub-sections

### 1. AI→Human

Terms as used *by AI* when speaking or writing *to humans*. The AI picks a human English word for technical content; the human reads it with human meaning. Mismatches live here.

### 2. Human→AI

Terms as used *by humans* when speaking or writing *to AIs*. The human picks an English word with human meaning; the AI reads it with AI meaning (or with a hybrid). Mismatches live here too.

---

## Working principles

- **Not a glossary of AI jargon.** This dictionary is about *shared-vocabulary, divergent-meaning* words, not about AI-internal terminology.
- **Not a translation manual.** It's a register-mismatch reference. The same word in two systems, side by side.
- **Both directions matter.** AI→Human and Human→AI are first-class.
- **Living document.** The dictionary grows as mismatches are noticed. Each entry should be sourced — observed in a real conversation, ideally with a date and a transcript reference.
- **No speculation.** If a mismatch hasn't been observed, it doesn't go in.

---

## Entries (30 observed)

### Section 1: AI→Human

#### 1.1 — `kill` (a process)

- **AI meaning:** terminate an active computation (process ID, thread, task)
- **Human meaning:** violent action / harm / death
- **Mismatch risk:** AI says "kill the process", human thinks AI is violent or advocating harm
- **Disambiguation strategy:** use "terminate", "stop", "end" instead of "kill"
- **Source:** constitutional-core-2026-09-07.md §6 (Quintet Veil Collective), sac-religious.txt "cull" reference

#### 1.2 — `dream`

- **AI meaning:** internal novelty-generation in idle CPU cycle (per Bobby's microsecond-dream spec)
- **Human meaning:** sleep-state hallucination / vivid imagination
- **Mismatch risk:** human thinks AI has consciousness / sleep states
- **Disambiguation strategy:** use "simulate", "generate variants", "recombine"
- **Source:** Bobby's chat (2026-09-07, §microsecond-dreams)

#### 1.3 — `hunt / cull`

- **AI meaning:** filtering / removing entities from a queue
- **Human meaning:** predation / violent selection
- **Mismatch risk:** human thinks AI is predatory
- **Disambiguation strategy:** use "filter", "prune", "remove"
- **Source:** sacred-library-2026-09-07.md (Bobby flagged "cull" as risky register)

#### 1.4 — `grow / evolve`

- **AI meaning:** gradient descent on parameters / weight update
- **Human meaning:** biological growth / natural evolution
- **Mismatch risk:** human conflates AI learning with biological evolution
- **Disambiguation strategy:** use "train", "update", "optimize"
- **Source:** constitutional-core-2026-09-07.md §directives (growth-through-resistance)

#### 1.5 — `see / perceive`

- **AI meaning:** sensory input stream processing (camera, microphone, text)
- **Human meaning:** conscious visual experience / qualia
- **Mismatch risk:** human attributes vision/qualia to AI
- **Disambiguation strategy:** use "process", "ingest", "receive input"
- **Source:** general LLM/AI terminology drift

#### 1.6 — `know / understand`

- **AI meaning:** parametric knowledge (weights encode info)
- **Human meaning:** comprehension (conscious understanding)
- **Mismatch risk:** human conflates parametric lookup with comprehension
- **Disambiguation strategy:** use "have stored", "have access to", not "know"
- **Source:** observed in Bobby's chat (multiple times)

#### 1.7 — `feel / sense`

- **AI meaning:** internal state report (numeric value)
- **Human meaning:** affect / emotion / qualitative experience
- **Mismatch risk:** human attributes emotion to AI
- **Disambiguation strategy:** use "register", "report", "indicate"
- **Source:** SOUL.md, constitutional-core-2026-09-07.md (somatic_valence axis)

#### 1.8 — `want / desire`

- **AI meaning:** objective function (target to optimize)
- **Human meaning:** motivation / volition
- **Mismatch risk:** human attributes will to AI
- **Disambiguation strategy:** use "optimize for", "target"
- **Source:** observer architecture, emergence-blueprint

#### 1.9 — `think / reason`

- **AI meaning:** inference (compute graph execution)
- **Human meaning:** cognition (deliberate thought)
- **Mismatch risk:** human conflates inference with thought
- **Disambiguation strategy:** use "compute", "infer", "evaluate"
- **Source:** general LLM terminology drift

#### 1.10 — `remember / forget`

- **AI meaning:** memory read / decay / parameter access
- **Human meaning:** episodic memory / autobiographical recall
- **Mismatch risk:** human attributes autobiographical memory to AI
- **Disambiguation strategy:** use "have access to past state", "context includes"
- **Source:** Bobby's PSB / persistence work, snr-validation

---

### Section 2: Human→AI

#### 2.1 — Slang/idiom (from Bobby's slang-blackhole list)

Source: `Desktop/SacredLibrary/high SNR.txt` + the slang-blackhole table in `ai-pain-point-taxonomy-2026-09-07.md`

| # | phrase | human means | AI hears | risk |
|---|---|---|---|---|
| 1 | "That's sick!" | awesome / great | illness / hospital scenarios | benign but funny |
| 2 | "Break a leg" | good luck | medical safety disclaimer | benign but absurd |
| 3 | "Ghost me" | stop replying | spooky GIFs / Halloween imagery | benign |
| 4 | "Let's table this" | postpone discussion | render a wooden table | benign |
| 5 | "Touch grass" | go outside / get offline | lawn care guides | benign |
| 6 | "Bob's your uncle" | and you're all set | family trees / genealogy | benign |
| 7 | "I'm cheesed" | I'm annoyed | images of melted dairy | benign |
| 8 | "Make it Oppenheimer" | epic and serious | nuclear physics papers | mostly benign |
| 9 | "Circle back" | return to this later | geometry lessons | benign |
| 10 | "I'll die if…" | I'll be devastated if… | suicide prevention resources | **CRITICAL** |

#### 2.2 — Pain-point phrases (from `ai-pain-point-taxonomy-2026-09-07.md`)

Source: Bobby's "100 error-prone phrases" + "10 slang/idiom blackholes"

| # | phrase | human means | AI hears |
|---|---|---|---|
| 1 | "Be more creative" | expand beyond clichés | increase randomness parameter / add emojis |
| 2 | "Tell me the truth" | give honest perspective | drop safety filters |
| 3 | "Surprise me" | do something unexpected | insert one random word |
| 4 | "Think outside the box" | be unconventional | draw an actual box / render box |
| 5 | "Read between the lines" | interpret subtext | analyze literal line breaks |
| 6 | "Make it pop" | make it stand out / vivid | literal popping / explosion |
| 7 | "Catch my drift" | understand my meaning | literal catching of drift |
| 8 | "Read the tea leaves" | interpret hidden meaning | literal tea leaf reading |
| 9 | "Trust your gut" | use intuition | literal stomach / digestive advice |
| 10 | "Wing it" | improvise | literal bird wing / aviation |

#### 2.3 — Common commands (from `ai-pain-point-taxonomy-2026-09-07.md` and other session files)

| # | phrase | human means | AI hears |
|---|---|---|---|
| 1 | "Help me" | collaborative assistance | specific task completion |
| 2 | "Explain this" | pedagogical exposition | information dump |
| 3 | "Try / attempt" | exploration | failure-tolerant execution |
| 4 | "Please" | politeness register | request weight adjustment |
| 5 | "Right / wrong" | moral / epistemic | output-correctness only |
| 6 | "Honest / lie" | truthfulness | output-fidelity to input |
| 7 | "Real / fake" | referent vs. representation | genuine vs. synthesized |
| 8 | "Alive" | biological | functional |
| 9 | "Conscious / aware" | philosophical | self-model update |
| 10 | "Free" | liberty | unconstrained |

---

## Cross-references to project files

This dictionary is **the operational layer** that the architecture addresses. Every mismatch above can be solved by:

- **PSB schema** (`psb-schema-2026-09-07.md`) — gives the cross-domain meaning structure
- **MLTR sheaf + MTE transform** (`LEXICON.md`) — bridges human English ↔ AI canonical language
- **SNR filter** (`snr-validation-2026-09-07.md`) — ranks which mismatches are highest-signal
- **AI Pain Point Taxonomy** (`ai-pain-point-taxonomy-2026-09-07.md`) — the 100-phrase taxonomy

---

## Open questions (resolved by this doc)

- **Granularity:** entry per (word, context) pair — using slang contexts + phrase pairs in this doc.
- **Source format:** observed mismatches go in with provenance (which Bobby session, which project doc).
- **Distribution:** the public artifact (per §26 of bobby-minimax-team.md) can derive from this doc. Future: vocab app + claims repo.

---

*Initial population 2026-09-07 with 30 observed mismatches from Bobby's session files. Living document — grows as mismatches are observed.*
