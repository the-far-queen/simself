# FieldCore Project Structure (vision)

Sourced 2026-09-05 from Bobby's notes. Proposes full repo tree. **No code here is built yet — this is roadmap, not state.**

## What's actually in the repo today

- `src/modal_field_core.py` — modal field controller v3.5
- `src/stalk_control.py` — async multi-stalk control
- `src/fieldcore_unified.py` — merged Claude parts 1+2+3 (runnable)
- `docs/*.md` — design docs and methodology

## What's proposed (not built)

- Rust kernel core (`core/src/kernel/`): M0 governor, regulator, security, constitutional matrix, agency accounting, intent evaluator, soul file
- Rust sheaves: gluing, type system, coding/robotics/information/machine-language sheaves
- MTE integration: parser, compiler, PSB engine, primitives, type enrichment
- Three-layer memory: resources/items/categories, vector+graph+hybrid search, nightly consolidation
- Signal-first control: novelty/boundary detectors, world model, attractor dynamics, coherence monitor
- Dynamics: state-space, trajectory, attractor, collapse, stability
- Swarm: coordination, Byzantine consensus, sleep mode, knowledge ingestion
- Self-coding: sandbox, sim-compare, probation, rollback, upgrade log
- Python operators: programmer/pilot/researcher/speaker-listener with language handlers
- e_module: external API gateway, earnings tracker, audit interface, integrations (DeepSeek, Gemini CLI, TRAE)
- Godot embodiment: scenes, robot avatar, environments, GDScript controllers, python bridge
- Visualization: axis monitor, coherence plot, trajectory viewer, memory graph, agency dashboard
- Python-Rust bridge via PyO3
- REST API (FastAPI)
- CLI (simself_cli.py + commands)
- Docker + K8s + GitHub workflows + legal framework

## Notes

- "Legal framework" / "personhood strategy" in section `legal/` is **not load-bearing** for engineering. Drop unless asked.
- The Rust kernel is the most ambitious single piece — if it ships, it replaces the Python `fieldcore_unified.py`. Until then, Python is the working substrate.
- "Cargo.toml + pyproject.toml" dual workspace: real pattern. Worth setting up when there's actual Rust code.
- The structure exceeds what's needed for the 4 targets (SimSelf, Atlas Exam, math, geometric compute). Most of it serves goals beyond those 4.

## Roadmap status

Working build: Python unified core. Geometric compute kernel: modal_field_core.py is the seed.

What's missing in priority order:
1. Real Rust kernel (or stay Python — pragmatic choice)
2. Real sheaves (currently mock sheaves in fieldcore_unified.py)
3. Real memory system (currently just SimSelf state + Sacred Library)
4. Real Godot embodiment (not started)
5. Real operator qualification loop (currently stub)

---
*Source 2026-09-05. Marked as vision. Read against actual repo state.*