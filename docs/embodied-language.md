# Language acquisition — embodied signal path

**Captured 2026-09-05 from Bobby in chat. Design intent, no implementation.**

## Core insight

Language starts as embodied signal, not symbolic tokens. The Helen Keller water-moment is the prototype: a physical sensation ("water flowing over hand") paired with a finger-spelled token ("w-a-t-e-r") in the body of another person. The token indexes the experience, not the other way around.

Standard LLM training: tokens in → tokens out. Symbol ↔ symbol mapping, no embodiment.

SimSelf path: physical signal ↔ token, learned in a sim where the agent has a body. Godot sim is the candidate substrate.

## Stages

1. **Motor primitives (PSB level)** — up, down, stop, grasp, release, near, far. Each PSB = (A, ΔW, ΔS, τ) tuple. Action + world-change + self-perturbation + temporal span. No symbols.
2. **Sensorimotor pairing** — finger-spelled token arrives at the same moment as a physical signal (water, lift, push). Agent learns token indexes signal.
3. **Composition** — token sequences map to PSB bundles. "up" = lift + stability. "stop" = containment + decay.
5. **Wrap LLM as stalk** — frozen LLM provides language backbone; learnable projection head maps to shared space Z (per the LanguageStalk design). LLM never writes directly. Same as the governor rule in core2.txt.
6. **Geometric backbone** — SimSelf sits on egg toroid; language lives along the axial gradient (mid-body for working semantic, base for constitutional).

## Implementation paths

| Path | Substrate | When |
|---|---|---|
| Geometric only | Egg toroid + sheaves + Python | first — proves the math runs |
| Hybrid wrap | Frozen LLM + learnable projection | second — adds language without breaking invariants |
| Godot sim embodiment | Godot robot sim + finger-spelling | third — proves embodied learning works |
| Real robot | ROS + stalk control + verifier | fourth — proves the loop closes physically |

## Tradeoffs

- Geometric-only SimSelf = no language. Useful for proving the constitutional kernel.
- LLM wrap = fast language, but inherits LLM's symbolic bias. Risk: language re-imposes symbol-first.
- Godot embodiment = slow to set up, but gives the Keller-style grounding. No shortcuts.
- Real robot = validates everything but expensive.

## Open

- Does projection head need its own pre-training corpus, or does gluing success/failure suffice as the only signal?
- Is the Godot sim enough, or does it need to be a real embodied agent before the grounding counts?
- Where does MMM (multiple-meaning measure) live — in the projection head, in the stalk, or in the SimSelf kernel?

## Helen Keller framing — concrete test

Build a minimal loop in Godot:
- Agent has a body (avatar with a hand)
- Physical signals available (water, lift, light)
- Another agent finger-spells tokens at signal moments
- Measure: does the embodied agent learn to predict which signal arrives from the token, before the signal happens?
- If yes → embodied language acquisition works.
- If no → something is missing (signal bandwidth, agency, temporal coupling).

---
*Captured 2026-09-05 in conversation. No implementation yet. Four-path plan is a sequence, not parallel.*