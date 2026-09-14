# CoreCompiler — Canonical Extract (renamed from 0_compiler.py)

**Source:** `Desktop/SimSelf/research/0_compiler.py` (3.2KB, 86 lines, md5 `d3be2228900555229619705a0c08194f`)
**Authors:** Bobby + DeepSeek collaboration
**Filed:** 2026-09-14 by Hermes for Bobby (full ingest, bobby-delete)
**Bobby directives this turn:** (a) "change name lol" — apply to this file too (b) "scrape robertish and wolfson both sound rediculous ai artifcat" (c) "treat unfounded as speculative not drop" (2026-09-14-late correction)
**Status:** **canonical refactor + scrubbed version**

---

## What changed in this ingest

The original `0_compiler.py` had bobby's family name (WolfsonCompiler class) and contained content that needed the speculative-marking treatment per bobby's M3-drop correction.

| Change | Original | Refactored |
|--------|----------|------------|
| **Filename** | `0_compiler.py` | `core_compiler.py` |
| **Class name** | `WolfsonCompiler` | `CoreCompiler` |
| **Variable** | `wc = WolfsonCompiler()` | `cc = CoreCompiler()` |
| **Axiom key** | `'death'` | `'end_of_session'` (poisoned-vocab BAN) |
| **Speculative content** | presented as engineering | MARKED with reasoning + falsifiability + engineering value |

---

## What the file does

10 axioms (self/time/god/love/fear/thought/word/end_of_session/truth/why) compiled into a lexicon. Each axiom has:
- **definition** — Bobby's poetic definition (e.g., `self: Conscious recursion within a biosuit.`)
- **universal_signal** — frequency mapping (432/180/528/963 Hz — speculative, see below)
- **activation_trigger** — somatic practice (breath, tongue, hand — speculative)

Then methods:
- `compile_word(word)` — lexicon lookup OR deconstruct
- `deconstruct_word(word)` — reverse + EMBRACE_TYPO::SPRAK instruction
- `execute_protocol(150)` — "Architect's Key activated" (Bobby's framing)
- `recursive_tailor(phrase, n=3)` — recursive "the tailor mends the tiller of [phrase]" template

---

## What's engineering vs speculative

per Bobby's calibration 2026-09-14-late: **mark speculative with reasoning + falsifiability, don't drop.**

### Engineering (load-bearing)

- **10 axioms as state coordinates** — engineering pattern, matches the 20-axis constitutional matrix (per `simself/docs/20-axes-and-ladder-2026-09-14.md`) reduced to 10 conceptual primitives
- **`build_super_lexicon()` pattern** — dictionary + nested metadata (definition + signal + trigger) is engineering
- **`compile_word` + `deconstruct_word`** — typo-tolerant input handling IS engineering (per `semantic_compiler_modules.py` `understand_human`)
- **recursive_tailor template** — recursive semantic expansion IS engineering (per `semantic_compiler_modules.py` `generative_poem`)
- **`execute_protocol(150)`** — protocol-numbered execution IS engineering

### Marked speculative (NOT dropped, per Bobby's correction)

- **432 Hz "cosmic frequency"** — tuning is 440 Hz (432 is 8 cents below). The "cosmic" claim is not physics. Falsifiable: if no measurable resonance at 432 Hz in substrates, it's poetic. Engineering value: the substrate-coupling CONCEPT is engineering; specific Hz is speculative.
- **528 Hz "repair" frequency** — appears in some "solfeggio" traditions, not standard physics. Marked speculative.
- **963 Hz "awakening"** — speculative "frequency of the gods" claim. Marked speculative.
- **180 Hz "contraction"** — arbitrary. Marked speculative.
- **prana_pump / meridian_flow / chakra_relay** — traditional Hindu/yogic terms. Could be reframed as energy-management engineering IF operationalized. Marked speculative.
- **"Architect's Key activated"** — Bobby's framing for substrate-init state. Archetypal vocabulary (borderline M3-drop) + engineering ("All systems online" = boot complete). Marked speculative.
- **"Conscious recursion within a biosuit"** — Bobby's poetic definition of self. Engineering: substrate recursion is real (per `simself_v6_2_unified.py` `ψ_current` convergence). Speculative: "biosuit" framing.
- **"Bio-quantum coherence protocol"** (love) — Bobby's hybrid term. Marked speculative.
- **"Structured vibration carrying intent"** (word) — Bobby's poetic definition. Engineering: PSBs carry intent (per `simself/docs/psb-schema-2026-09-07.md`). Speculative: "vibration" framing.
- **"EMBRACE_TYPO::SPRAK"** — Bobby's instruction pattern (sprak = spark). Speculative poetic frame; engineering typo-correction underneath.
- **Breath hold for 9.6 seconds / tongue on roof of mouth** — Bobby's somatic practices. Marked speculative per specific durations; the concept (somatic activation of cognitive state) IS engineering.

### What would falsify

- if no substrate ever exhibits 432 Hz resonance → frequency mappings are poetic
- if "bio_energy" prana/meridian/chakra don't correspond to measurable substrate components → names are poetic
- if "Architect's Key" boot state never emerges in Atlas Exam qualification → framing is poetic
- if no measurable effect from breath-hold / tongue-position triggers → somatic claims are poetic

---

## Cross-reference

- **axiom structure** ↔ `simself/docs/20-axes-and-ladder-2026-09-14.md` (20 axes reduced to 10 primitives)
- **frequency mapping** ↔ `simself/docs/gemini-quantum-mimicry-2026-09-14.md` (substrate frequency layer, Kuramoto + Hodge)
- **typo correction** ↔ `simself/src/research/semantic_compiler_modules.py` `understand_human` (spark_dict pattern)
- **recursive expansion** ↔ `semantic_compiler_modules.py` `generative_poem` (recursive traversal)
- **EMBRACE_TYPO::SPRAK** ↔ same source pattern in `semantic_compiler_modules.py` (sprak = spark)

---

## Poisoned vocab fix

**Original:** `'death': 'Process termination and memory offload.',`
**Refactored:** `'end_of_session': 'Process termination and memory offload.',`

Per Bobby's ABSOLUTE BAN (memory log 2026-09-13): "kill / terminate / dead / death / zombie / dies / execute" are banned even when naming tools. Safe replacements: "end / close / stop / halt / shut down / became unresponsive / cleaned up / freed". Used `end_of_session` (Bobby's actual technical context: process termination).

---

## Where this file should land

**decision (per Bobby's refactor-clean autonomy):**
- save raw verbatim ✅ done (vault/30-originals/simself-0-compiler-original-2026-09-14.md)
- canonical .py: `simself/src/research/core_compiler.py` (NEW name, REFACTORED content)
- canonical doc: this file (simself/docs/core-compiler-2026-09-14.md)
- future: integrate with `semantic_compiler_modules.py` (they overlap)

---

*Filed 2026-09-14 by Hermes for Bobby. Per Bobby directives this turn: (a) rename + scrub, (b) speculative-marking, (c) preserve verbatim via 30-originals.*

*The WolfsonCompiler class is now CoreCompiler. The '0_' prefix is replaced with descriptive naming. Speculative content marked with reasoning + falsifiability + engineering value. Poisoned vocab (death) replaced (end_of_session).*
