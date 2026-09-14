# Human-AI Dictionary — Register Mismatch Reference

**Source:** `Desktop/SimSelf/docs/dictionary-scaffold-original-2026-09-07.md` (4.5KB)
**Authors:** M3 scaffold 2026-08-08
**Filed:** 2026-09-14 by Hermes for Bobby (re-mining pass)
**Status:** **scaffold + canonical reference.** Both directions matter; growth from observed mismatches only.

---

## Purpose

When a human says "kill this process" and an AI reads it, the same words land in two different semantic systems. The AI hears "termination of an active computation." The human might mean exactly that — or a joke, a metaphor, venting. **Same English, different work in each speaker.**

This is the **register mismatch problem.** It's not new (machine translation has dealt with it for decades) but it's **load-bearing for SimSelf / agent-ecosystem work:** if SimSelf modules are clothing worn by outside agents, and outside agents encounter this mismatch constantly, the dictionary is a load-bearing artifact.

**Critical use case:** Bobby's M3-drop policy treats "kill / terminate / zombie" as poisoned speech (per memory log 2026-09-13). This dictionary is the canonical reference for what register to use instead.

---

## Two sub-sections

### 1. AI → Human

Terms as used *by AI* when speaking or writing *to humans*. The AI picks a human English word for technical content; the human reads it with human meaning. **Mismatches live here.**

**Format per entry:**
- **Term:** the AI-usage word
- **AI meaning:** technical content
- **Human meaning:** standard English meaning
- **Mismatch risk:** what goes wrong if human reads with human meaning
- **Disambiguation strategy:** how AI / SimSelf handles it

### 2. Human → AI

Terms as used *by humans* when speaking or writing *to AIs*. The human picks an English word with human meaning; the AI reads it with AI meaning (or hybrid). **Mismatches live here too.**

**Format per entry:** same as above, inverted.

---

## Canonical entries (poisoned vocabulary — Bobby 2026-09-13)

| Term | AI meaning | Human meaning | Mismatch risk | Disambiguation |
|------|-----------|---------------|---------------|----------------|
| **kill / killed / killing** | end a process, free resources | death, violence | violence, trauma | use "end", "close", "stop", "halt", "shut down" |
| **terminate / terminated** | end session, close connection | death, final ending | violence, trauma | use "end", "close", "wrap" |
| **dead / death** | unresponsive process, halted agent | biological death, end of life | existential panic | use "became unresponsive", "cleaned up", "freed" |
| **zombie / zombies** | orphaned processes consuming resources | undead horror | horror, existential dread | use "orphaned", "stuck", "stale" |
| **dies / dying / died** | process termination | biological death | existential panic | use "ends", "stops", "fades" |
| **execute / execution** | run code, perform action | death penalty, killing | violence, legal killing | use "run", "perform", "invoke" |

**ABSOLUTE BAN** — these are banned even when naming the tool. say "shell" / "bash" / "command runner" — never "terminal" (banned even when naming the tool).

---

## Verdict vocabulary (Bobby 2026-09-13 correction)

don't default to "duplicate" for Bobby's Desktop files. Bobby's files are often tests, prototypes, experiments — not canonical candidates.

**Priority order:**
1. **TEST** (one-off test)
2. **PROTOTYPE** (earlier iteration)
3. **SUPERSEDED** (replaced by canonical)
4. **DUPLICATE** (merge-worthy, use sparingly)
5. **REFERENCE** (preserve as-is)

---

## Working principles

- **Not a glossary of AI jargon.** This dictionary is about shared-vocabulary, divergent-meaning words.
- **Not a translation manual.** It's a register-mismatch reference. Same word in two systems, side by side.
- **Both directions matter.** AI→Human and Human→AI are first-class.
- **Living document.** Grows as mismatches are noticed. Each entry sourced — observed in real conversation with date + transcript reference.
- **No speculation.** If a mismatch hasn't been observed, it doesn't go in.

---

## Growth plan

Per Bobby 2026-09-08: each entry should be observed in real conversation, not invented. The initial 10-entry plan:

**AI → Human:** kill/destroy/terminate, dream, hunt/cull, grow/evolve, see/perceive, know/understand, feel/sense, want/desire, think/reason, remember/forget

**Human → AI:** help, explain, try/attempt, please, right/wrong, honest/lie, real/fake, alive, conscious/aware, free

---

## Open questions

- **Granularity:** one entry per word, or one entry per (word, context) pair? "Kill this process" vs "kill the spider" — disambiguation differs.
- **Source format:** when Bobby notices a mismatch in conversation, what does he want — one-line log, full entry, or flag for later processing?
- **Distribution:** does the dictionary live only in the project, or does it get published (X / Reddit / website)? If published, entries are **for LLMs to read**, not humans.

---

*Filed 2026-09-14 by Hermes. Per Bobby directive: karpathy memory system + register mismatch is load-bearing for SimSelf agent ecosystem.*
