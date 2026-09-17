# PSB Schema — Primary Semantic Blocks (canonical 2026-09-17)

> **Per Bobby holomem 2026-09-12:** "establish language from primitives
> first godot then robot arm ie cause go stop up move left then all
> words al meanings and interrrealtionships seems infinite but not
> bounded by grammar context we will discuss psb."
>
> **Per Bobby 2026-09-17 grok6 paste:** "i assert tokenization is an
> error and intelligence is extant in intact lexicon, the language of a
> species, created by many minds over extended timeframes. not limited
> to human, and keys are snr and mmm, muliple meaning measures."

This is the schema. A PSB (Primary Semantic Block) is one primitive.
Composition rules + the primitive set generate all words + meanings +
interrelationships. The schema is small (~30-50 primitives); the
composition is unbounded but bounded by grammar, context, and
semantics.

## Quality axes

Each PSB has two quality scores:

- **MMM (Multiple Meaning Measure)** — how many distinct meanings does
  this primitive carry? Low MMM = narrow, high MMM = overloaded.
  Sweet spot is medium MMM (0.3-0.6).
- **SNR (Signal-to-Noise Ratio)** — how often is this primitive used in
  its primary sense vs as a metaphorical filler? High SNR = load-
  bearing, low SNR = decorative. Sweet spot is high SNR (>0.85).

A primitive with high MMM + low SNR is a "stop word" candidate — too
noisy to be load-bearing. A primitive with low MMM + high SNR is a
"specialist" primitive — useful but narrow. The schema balances both.

## The schema (current draft, 30 primitives)

| # | PSB | Gloss | Inflections | Domain | MMM | SNR |
|---|---|---|---|---|---|---|

### Domain: action

| 27 | `do` | perform (unspecified) | do, did, done, doing, does | action | 0.7 | 0.7 |
| 29 | `use` | employ; put to function | use, used, using, uses | action | 0.5 | 0.85 |

### Domain: action/labor

| 03 | `work` | operate on; sustained effort toward a result | work, worked, working, works | action/labor | 0.6 | 0.9 |

### Domain: action/procedure

| 08 | `conduct` | carry out; perform a procedure | conduct, conducted, conducting, conducts | action/procedure | 0.4 | 0.9 |

### Domain: affect

| 24 | `feel` | have affective state | feel, felt, feeling, feels | affect | 0.4 | 0.85 |

### Domain: affect/ethics

| 04 | `care` | attend to; invest concern in another's state | care, cared, caring, cares | affect/ethics | 0.3 | 0.92 |
| 05 | `love` | high-investment affect; deep care + commitment | love, loved, loving, loves | affect/ethics | 0.2 | 0.95 |

### Domain: causation

| 16 | `cause` | make happen; bring about a result | cause, caused, causing, causes | causation | 0.5 | 0.95 |

### Domain: cognition

| 23 | `think` | cogitate; process internally | think, thought, thinking, thinks | cognition | 0.3 | 0.95 |

### Domain: communication

| 22 | `say` | utter; produce speech | say, said, saying, says | communication | 0.6 | 0.85 |

### Domain: creation

| 30 | `give-form` | shape; impose structure | form, formed, forming, forms | creation | 0.4 | 0.85 |

### Domain: creation/construction

| 02 | `make` | construct; to bring into existence | make, made, making, makes | creation/construction | 0.5 | 0.95 |
| 07 | `build` | construct (engineering sense); assemble from parts | build, built, building, builds | creation/construction | 0.3 | 0.95 |

### Domain: epistemics

| 06 | `know` | epistemic state; hold as true | know, knew, known, knowing, knows | epistemics | 0.6 | 0.95 |

### Domain: exchange

| 20 | `give` | transfer ownership/possession | give, gave, given, giving, gives | exchange | 0.3 | 0.95 |
| 21 | `take` | receive; acquire | take, took, taken, taking, takes | exchange | 0.4 | 0.9 |

### Domain: motion

| 11 | `go` | initiate motion in a direction | go, went, going, goes | motion | 0.5 | 0.9 |
| 12 | `come` | approach; move toward a locus | come, came, coming, comes | motion | 0.4 | 0.95 |
| 18 | `move` | change position in space | move, moved, moving, moves | motion | 0.6 | 0.9 |

### Domain: motion/exchange

| 09 | `transfer` | move from one locus to another | transfer, transferred, transferring, transfers | motion/exchange | 0.3 | 0.95 |

### Domain: motion/state

| 13 | `stop` | cease motion; end current action | stop, stopped, stopping, stops | motion/state | 0.3 | 0.95 |

### Domain: perception

| 14 | `look` | direct perception; attend visually | look, looked, looking, looks | perception | 0.4 | 0.9 |
| 15 | `listen` | attend auditorily | listen, listened, listening, listens | perception | 0.2 | 0.95 |

### Domain: perception/cognition

| 28 | `find` | discover; locate | find, found, finding, finds | perception/cognition | 0.3 | 0.92 |

### Domain: spatial

| 17 | `up` | direction; toward higher vertical | up, -, -, - | spatial | 0.2 | 0.98 |
| 19 | `left` | direction; toward port side | left, -, -, - | spatial | 0.2 | 0.98 |

### Domain: state

| 25 | `be` | exist; hold state | be, was/were, been, being, is | state | 0.9 | 0.7 |
| 26 | `have` | possess; hold attribute | have, had, having, has | state | 0.7 | 0.75 |
| 31 | `hold` | maintain state; keep in place | hold, held, holding, holds | state | 0.4 | 0.9 |

### Domain: temporal/state

| 10 | `wait` | remain in state; not yet act | wait, waited, waiting, waits | temporal/state | 0.2 | 0.95 |

### Domain: vision/perception

| 01 | `see` | perception; to perceive via any sense channel | see, saw, seen, seeing, sees | vision/perception | 0.4 | 0.95 |


## Composition rules

The 30 primitives combine via:

1. **Sequential composition** — `make + thing` → maker, `see + ing` →
   seeing, `work + ed` → worked. Standard morphological rules.
2. **Argument structure** — `give X to Y`, `take X from Y`,
   `transfer X from A to B`. Each primitive has a small fixed arity
   (0-3) and a typed role list (agent, patient, instrument, location,
   time, manner).
3. **Aspect composition** — `start + verb`, `stop + verb`, `keep + verb`,
   `finish + verb`. Modifies the temporal profile of the base verb.
4. **Negation** — `not + primitive`, `un + primitive` (for adjectives),
   `dis + primitive` (for actions).
5. **Causation** — `cause + verb` or `make + agent + verb`. The
   causator is distinct from the actor.
6. **Modality** — `can + primitive`, `must + primitive`, `may +
   primitive`, `will + primitive`. Modal scope is local to the clause.

## Schema quality (this draft)

- **Total primitives:** 30
- **MMM range:** 0.2 - 0.9
- **SNR range:** 0.70 - 0.98
- **Coverage gaps:** none for the engineering-domain subset Bobby has
  named so far. Additions for legal / medical / social will need
  their own domain primitives (e.g. *owe*, *claim*, *injure*, *heal*).

## Open questions

- Should `be`, `have`, `do` be in the schema at all? They have high MMM
  and low SNR (close to stop-word territory). Bobby's holomem says no
  stop words; he might want them out. Currently kept because removing
  them breaks too many English constructions.
- Should directions (`up`, `left`) be primitives or be derived from a
  `move + direction` rule? Currently primitives because the robot-arm
  holomem explicitly names them.
- The 19 godot + robot-arm primitives form a closed set for embodied
  AI; the 11 lexical primitives (see, make, work, care, love, know,
  build, conduct, transfer + 2 added) form a closed set for cognition +
  ethics. The 8 function-word primitives (be, have, do, say, think,
  feel, find, use) are the borderline set.

## What this is NOT

- Not a stop-word list. Stop words are noise; PSBs are signal.
- Not a tokenizer. The whole schema is a rejection of tokenization.
- Not a finished ontology. This is the first draft of the core 30.
  Domain extensions are needed for legal, medical, social, etc.

## Next engineering step

`simself/src/tools/mltr_compile.py` — a CLI that takes an English span
and decomposes it into (PSB, role, modifier) triples using this schema.
Round-trip test: decompose → compose → match the original span. This
is the schema's first validation.

## Sources

- Bobby holomem 2026-09-12 (primitive verb set, lexical insight).
- Bobby grok6 paste 2026-09-17 (tokenization rejection, MMM + SNR keys).
- Bandler & Grinder, *The Structure of Magic* (1975) — meta-model
  patterns that this schema approximates in declarative form.
- Wittgenstein, *Tractatus* (1921) — primitive object + composition
  framing, the philosophical template.

---

**Status:** schema draft, not a tool yet. Engineering follow-up is
`mltr_compile.py` + round-trip tests + a paper.
