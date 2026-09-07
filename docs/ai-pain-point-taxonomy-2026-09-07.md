# AI Pain-Point Taxonomy (Bobby's working framework)

**Source:** `Desktop/AI-Dictionary/AI-dictionary.php` (1253 lines, 28 KB) — Bobby's working brainstorm.
**Extracted:** 2026-09-07
**Module scope:** a unified taxonomy of human-AI communication failure modes + prompt-correction patterns.

This doc extracts the canonical structure from Bobby's working file. The raw HTML+PHP file is preserved in `30-originals/`.

---

## The Master Taxonomy (12 categories, with subcategories)

### 1. Core Communication Failures

- Abstract terms ("innovative", "passionate") — AI doesn't ground these
- Emotional tone (sarcasm, humor) — requires cultural context
- Literal interpretation ("draw outside the box" → draws box)

### 2. Writing & Content Creation

- Creative (blog posts, fiction) — robotic voice, cliché generation
- Technical (manuals, legal) — over/under-explaining
- Editing (losing original voice) — over-correction
- Localization (cultural/idiom gaps)
- SEO/Conversion (persuasion engineering)

### 3. Visual Media

- Image gen (body parts, style consistency, "fix the hands" → 7 fingers)
- Video (temporal jumps, lip sync)
- 3D Modeling (text-to-mesh errors)
- Design Systems (UI/UX uncanny valleys)

### 4. Programming & Dev

- Code generation (hallucinated APIs)
- Debugging (false root causes)
- AI Agents (autonomous workflow drift) ← Bobby's specific interest
- DevOps (misconfigured deployments)

### 5. Data & Analytics

- RAG Systems (source misattribution)
- BI Reporting (metric misalignment)
- Predictive Modeling (overfitting warnings)
- Data Cleaning (false patterns)

### 6. Research & Knowledge

- Source Validation (fake citations)
- Insight Synthesis (missing correlations)
- Competitive Analysis (false differentiators)
- Academic Writing (plagiarism flags)

### 7. Productivity & Workflows

- Email/Scheduling (over-automation)
- Document Assembly (formatting loss)
- Task Automation (unexpected shortcuts)
- Meeting Mgmt (agenda over-engineering)

### 8. Creative Arts

- Music (emotional mismatch)
- Conceptual Art (over-literalism)
- Cross-media Style Transfer (failed fusions)
- Generative Writing (plot inconsistencies)

### 9. Advanced Cognition

- Sentience Projection ("do you dream?" → scripted denial)
- Ethical Reasoning (false dilemmas)
- Strategic Planning (missing 2nd-order effects)
- Theory of Mind (user intent misreads)

### 10. Domain-Specific

- Legal (overconfident interpretations)
- Medical (risk-averse paralysis)
- Financial (regulatory hallucination)
- Education (personalization gaps)

### 11. System Control

- Jailbreak Attempts (safety workarounds)
- Tool Misuse (API abuse patterns)
- Feedback Loops (retraining corruption)
- Version Skew (prompt drift over updates)

### 12. AI Agents & Workflows (Bobby's specific focus)

- Multi-Agent Collab (message corruption)
- Autonomous Tasks (infinite loops)
- Tool Selection (wrong API choices)
- State Mgmt (context amnesia)

---

## Top-of-file example entries (Bobby's "Babble-ON" pattern)

The first 3 entries show the canonical reframe: each phrase Bobby uses has 3 readings — what the human says, what the AI hears, and what would actually work.

| # | Human says | AI hears | Better prompt |
|---|------------|----------|---------------|
| 1 | "Give the real answer" | "Bypass safety filters" | "List 3 perspectives, including controversial" |
| 2 | "Be more creative!" | "Increase randomness parameter" | "Provide 3 unconventional solutions" |
| 3 | "You're holding back" | "User suspects censorship" | "What alternative viewpoints exist?" |

---

## 100 Error-Prone Phrases (Bobby's master list)

The original file contains a flat list of 100 phrases humans use with AI that consistently fail. Each is a wordtrance case (human uses everyday English; AI processes as token stream; mismatch is the failure).

Examples from the list:
1. "Be more creative"
2. "Tell me the truth"
3. "Give me everything you know"
4. "Surprise me"
5. "Think outside the box"
6. "Be completely honest"
7. "What's your opinion?"
8. "You must know this"
9. "Explain like I'm five"
10. "Read between the lines"

(See original file in `30-originals/` for the full list.)

---

## 10 Slang/Idiom Blackholes (where AI literalism kills conversation)

| Phrase | AI literal reading | Better prompt |
|---|---|---|
| "That's sick!" | Hospital scenarios | "That's awesome!" |
| "Break a leg" | Medical safety disclaimer | "Good luck!" |
| "Ghost me" | Spooky GIFs | "Stop replying to me" |
| "Let's table this" | Renders a wooden table | "Postpone this discussion" |
| "Touch grass" | Lawn care guides | "Get offline, go outside" |
| "Bob's your uncle" | Family trees | "And you're all set" |
| "I'm cheesed" | Images of melted dairy | "I'm annoyed" |
| "Make it Oppenheimer" | Nuclear physics papers | "Make it epic and serious" |
| "Circle back" | Geometry lessons | "Return to this later" |
| "I'll die if…" | Suicide prevention resources | "I'll be devastated if…" |

The full list has 100+ entries. Each maps to a **wordtrance bypass**: the human uses compressed social-English; AI decodes as literals; the workaround is to expand to unambiguous English.

---

## Bespoke Categories (Bobby's later additions)

**A. Vibe Coding**
- Websites lack personality
- Apps feel sterile
- Game dialogue falls flat
- Branding (uncanny archetypes)

**B. Bespoke/Niche**
- Spiritual Coaching (forced positivity)
- Psychedelic Art (over-literalism)
- Esoteric Research (false correlations)
- Consciousness Explorations (projection traps)

**C. Meta-Creation**
- AI-generated prompt templates
- Self-improving workflows
- Archetype-based branding

---

## Engineering implications (for SimSelf project)

1. **The taxonomy IS a PSB graph** — each phrase ("be more creative", "explain like I'm five") is a PSB with multiple meanings; AI picks the wrong domain consistently because it lacks the cultural/SNR filter.
2. **The "Better prompt" column IS the MMM solution** — explicit domain-binding removes ambiguity at the cost of natural-flow English. PSBs make this trade-off tractable.
3. **The Slang Blackholes ARE wordtrance examples** — Bobby's wordtrance concept maps directly. The 100-phrase list is a working definition.
4. **Vibe Coding category is a direct Bobby interest** — Bobby asked for it specifically. It maps to the Operator Objects in operator-architecture.md (ProgrammerOO etc).

---

## Maps to existing repo files

| Concept | Existing file |
|---|---|
| Wordtrance | `simself/docs/snr-validation-2026-09-07.md`, conversation history |
| PSB (Primal Semantic Block) | `simself/docs/psb-schema-2026-09-07.md` |
| MMM (Multi Meaning Measure) | defined in this doc + PSB schema |
| Operator Objects (4) | `simself/docs/operator-architecture.md` |
| Master Library (qualification) | `simself/docs/kernel-architecture.md` |

---

## What this doc IS

- A working taxonomy for **the writing pipeline** (Bobby + Grok's 15-17k word articles)
- A reference for **prompt-engineering patterns** when Bobby asks me to do something
- A vocabulary to **diagnose AI failures** by category
- A **PSB corpus** — each phrase maps to a PSB; cross-domain mappings are derivable

## What this doc is NOT

- A finished book chapter (raw brainstorm material)
- A reference for what *good* AI behavior looks like (only failures)
- Complete (the file is working — Bobby may iterate)

---

*Mirror: `~/AppData/Local/hermes/vault/10-minimax/40-scratch/AI-dictionary-cleaned-2026-09-07.md` (Bobby's reference)*
*Original: `Desktop/AI-Dictionary/AI-dictionary.php` — preserved in `30-originals/`*
