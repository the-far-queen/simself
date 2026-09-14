# AI Learning Systematization: Reasoning First, Then English

Framework for training AI from scratch using self-play RL and verifiable rewards.

---

## Core Insight

**The Helen Keller moment:** Once AI invents/discovers useful internal representations through self-generated challenges, learning accelerates dramatically. This is the "water" breakthrough — signs map to concepts → rapid language/reasoning explosion.

---

## Why Earlier Attempts Failed

- Pre-2017: Started with language or broad knowledge → brittle, slow progress
- Missing: Scalable self-improvement mechanisms
- RL/neural nets plateaued quickly in complex environments

---

## What's Different Now (2025-2026)

### Self-Play Reinforcement Learning
- **AlphaZero (2017):** Go/Chess from zero human data — self-play → superhuman in days
- **R-Zero (2025):** Fully autonomous, generates training data from scratch
- **Absolute Zero Reasoner (AZR, 2025):** Proposes own tasks, solves, verifies, evolves curriculum — no external data
- **RLVR (DeepSeek R1, 2025):** Verifiable rewards bootstrap reasoning without human labels

**Pattern:** Slow random phase → exponential improvement as agent generates high-quality data

---

## The Curriculum: Phase 0 → Phase 2

### Phase 0: Bootstrap with Verifiable Domain
- Simple verifiable environment (grid world, code execution)
- Self-play RL: agent plays against copies of itself
- Rewards from verifiable wins (puzzle solved, correct output)
- AZR/RLVR provide grounded rewards — no human data needed

### Phase 1: Emergent Reasoning
- AI proposes its own harder tasks
- Train with chain-of-thought or search (MCTS from AlphaZero)
- Once it "groks" planning/causality → reasoning explodes across domains

### Phase 2: Layer English from Scratch
- After reasoning mastery, introduce language as labels/actions
- Strong reasoner generates/self-corrects text data
- Language emerges as tool for better planning/explanation

---

## Open-Source Repos

### Self-Play for Games
- https://github.com/suragnair/alpha-zero-general — Most popular general AlphaZero
- https://github.com/tensorflow/minigo — TensorFlow AlphaGo Zero
- https://github.com/leela-zero/leela-zero — Community AlphaGo Zero
- https://github.com/jonathan-laurent/AlphaZero.jl — Julia implementation

### Absolute Zero Reasoner (AZR)
- https://github.com/LeapLabTHU/Absolute-Zero-Reasoner — Official repo

### RLVR Extensions
- https://github.com/thuml/RLVR-World — RLVR for world models
- https://github.com/smiles724/Awesome-LLM-RLVR — Curated RLVR list

### R-Zero
- https://github.com/Chengsong-Huang/R-Zero — Official codes

### Other Relevant
- https://github.com/spiral-rl/spiral — SPIRAL: multi-turn text games
- https://github.com/open-thought/reasoning-gym — Verifiable reasoning environments
- https://github.com/volcengine/verl — Production-ready RL for LLMs

---

## Implementation Timeline

| Phase | Duration | Focus |
|-------|----------|-------|
| Phase 0 | 1-2 weeks | Bootstrap in verifiable environment |
| Phase 1 | 1-3 months | Reasoning via self-play |
| Phase 2 | 3-6 months | Layer English on reasoning |
| **Total** | **6-12 months** | Complete system |

---

## Key Insight from Robert

> "The heart of innovation lies in linking embeddings between encoder and decoder, with attention combining self-reflective component with cross-attention — a symphony where sections work together, making the whole compact and efficient."

---

*Source: 2026 AI learning systematization outline, open-source repo list*
*Saved: 2026-03-04*
