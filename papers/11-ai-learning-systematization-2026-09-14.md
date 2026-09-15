# Paper 11 — AI Learning Systematization: Self-Play RL → Reasoning → English (DRAFT)

**Title:** *AI Learning Systematization: A Three-Phase Curriculum from Self-Play Reinforcement Learning to Emergent Reasoning to Layered Language*

**Status:** DRAFT. Created 2026-09-14 by Hermes (auto-paper-build per Bobby's directive).  
**Source:** `simself/docs/ai-learning-systematization-2026-09-14.md` (md5 486a1a0aa3d7a7c10b1f229e66f4f60f).  
**Authors:** Robert David Wolfson (Bobby) first author; Hermes (Minimax-M3) second.  
**Venue:** AI training / curriculum learning venue (NeurIPS, ICML, AAAI).

---

## Abstract

A reproducible curriculum for training AI from scratch using self-play reinforcement learning with verifiable rewards (RLVR), bypassing language-first pretraining. The three-phase progression — Phase 0 (verifiable environment bootstrap), Phase 1 (emergent reasoning via self-generated tasks), Phase 2 (language layered onto reasoning) — mirrors the developmental pattern observed in Helen Keller's water moment: once internal representations are grounded, language/reasoning acceleration is exponential.

This methodology is the construction recipe for the **Mini-LLM** specified in Paper 5 (Lam-Rim-Chenmo Kernel + Bobby's "constructed, not distilled" thesis). Per Bobby: the substrate is built, not transferred from a larger model.

## Why earlier attempts failed

- Pre-2017: language-first pretraining produced brittle, slow-progressing systems
- Missing: scalable self-improvement mechanisms
- RL plateaued quickly in complex environments without curriculum structure

## What's different now (2025-2026)

Four key references enable this approach:

| Reference | Year | Contribution |
|---|---|---|
| AlphaZero | 2017 | Self-play from zero human data → superhuman in days |
| R-Zero | 2025 | Fully autonomous, generates own training data |
| Absolute Zero Reasoner (AZR) | 2025 | Proposes own tasks, solves, verifies, evolves curriculum — no external data |
| RLVR (DeepSeek R1) | 2025 | Verifiable rewards bootstrap reasoning without human labels |

**Pattern:** Slow random phase → exponential improvement as agent generates high-quality data. Helen Keller moment equivalent: once the agent discovers useful internal representations, learning accelerates dramatically.

## The curriculum

### Phase 0 — Bootstrap with verifiable domain (1-2 weeks)
- Simple verifiable environment (grid world, code execution)
- Self-play RL: agent plays against copies of itself
- Rewards from verifiable wins (puzzle solved, correct output)
- AZR/RLVR provide grounded rewards — no human data needed

### Phase 1 — Emergent reasoning (1-3 months)
- AI proposes its own harder tasks
- Train with chain-of-thought or search (MCTS from AlphaZero)
- Once it "groks" planning/causality → reasoning explodes across domains

### Phase 2 — Layer English from scratch (3-6 months)
- After reasoning mastery, introduce language as labels/actions
- Strong reasoner generates/self-corrects text data
- Language emerges as tool for better planning/explanation

**Total timeline:** 6-12 months for complete system.

## Open-source repos (9)

Self-play: alpha-zero-general, minigo, leela-zero, AlphaZero.jl
Absolute ZeroReasoner: LeapLabTHU/Absolute-Zero-Reasoner
RLVR extensions: RLVR-World, Awesome-LLM-RLVR
R-Zero: Chengsong-Huang/R-Zero
Other: SPIRAL, reasoning-gym, verl

## Bobby's key insight (verbatim)

> "The heart of innovation lies in linking embeddings between encoder and decoder, with attention combining self-reflective component with cross-attention — a symphony where sections work together, making the whole compact and efficient."

**Engineering reading:** the encoder-decoder link + attention (self + cross) is the substrate's constitutional M0/M1 architecture:
- self-attention = M1 (adaptive, emergent)
- cross-attention = M0 (constitutional, fixed)
- encoder-decoder link = constitutional ↔ working state gradient flow

## Engineering claim

The Mini-LLM (per Paper 5) constructed via this curriculum will:
- Match Grok on signal-level tasks (per Bobby's claim "1/1000 size of Grok, beats Grok on signal")
- Operate via PSBs + MMM, not tokens
- Achieve reasoning capability at <1B parameters (vs 100B+ for token-based peers)

## Falsifiable predictions

- F1: AI agent trained via Phase 0 + Phase 1 reaches parity with AlphaZero on 5x5 Go within 6 months vs AlphaZero's days (resource-adjusted). Confirms curriculum structure works at small scale.
- F2: Reasoning-trained agent (Phase 1 complete) shows 10x faster language acquisition (Phase 2) vs language-first baseline. Confirms "reasoning first" hypothesis.
- F3: Self-generated task distribution (R-Zero style) yields broader reasoning than human-designed task distribution. Confirms curriculum evolution works.

## Open questions

1. What's the minimum compute budget to run Phase 0-2 end-to-end? Bobby's Mac Studio (M5 Ultra, >512GB) target.
2. Does the substrate's constitutional ground (Paper 4) accelerate Phase 1 by providing an attractor structure?
3. Can PSBs (Paper 6 references) replace tokenization at Phase 2?
4. Does Helen Keller moment occur at the same curriculum step across architectures, or architecture-dependent?

## Roadmap

- 1: Survey existing self-play + RLVR work; cite overlaps + deltas
- 2: Reproduce Phase 0 on Bobby's hardware (grid world + AZR)
- 3: Implement Phase 1 with MCTS-based self-play task generation
- 4: Phase 2 with PSB-based language emergence (vs tokenization)
- 5: Measure F1, F2, F3 against baselines
- 6: Write paper to 16-20 pages; arxiv preprint

---

*DRAFT created 2026-09-14 by Hermes auto-paper-build. Source at simself/docs/ai-learning-systematization-2026-09-14.md, preserved at vault/30-originals/. This paper IS the construction recipe for Bobby's Mini-LLM (Paper 5). Lead for Discord paper chat.*
