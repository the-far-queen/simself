# FieldCore: Project Analysis & Architectural Overview

## 1. Project Description
FieldCore is a **field-computational cognitive architecture** designed for building persistent, self-evolving, and ethically grounded AI systems. It moves beyond simple text-based interaction, treating intelligence as a geometric and topological process within a high-dimensional information field.

### Core Philosophy
FieldCore operates on the principle that intelligence emerges from the interaction of structured "signal" (meaningful data) against "noise." It privileges stability, coherence, and invariant enforcement over mere mimicry or statistical probability.

---

## 2. Architectural Components

### A. Bicameral Governance (M0 / M1)
- **Governor (M0):** The "Invariant Enforcer." It is a non-generative, deterministic gatekeeper that ensures all proposed state changes or actions adhere to hard-coded safety and stability constraints.
- **Controller (M1):** The "Orchestrator." It manages state transitions, recursive focus within the information field, and coordinates between various specialized modules (sheaves).

### B. Information Field & Sheaf Model
The system represents knowledge as **InfoPackets**—high-dimensional vector embeddings. These packets are organized into a **Field Graph**, where edges represent "restriction maps" or compatibility between local data points (stalks).
- **Coding Stalk:** Executable specifications and type systems.
- **Robotics Stalk:** Physics, motors, and sensor streams.
- **Information Stalk:** Structured knowledge and semantic relations.

### C. Primal Semantic Blocks (PSBs)
PSBs are the atomic units of meaning (e.g., `CAUSE`, `CONTAIN`, `FORCE`, `SUPPORT`). They serve as the foundational grounding for all higher-level concepts and are mapped to ethical axes (Swedenborgian axes) to ensure the agent's values are baked into its semantic substrate.

---

## 3. Proposed Modular Folder Structure

To support the scalability and modularity of FieldCore, the following structure is suggested:

| Folder | Responsibility | Key Components |
| :--- | :--- | :--- |
| **`agent/`** | Identity & Governance | Governor (M0), SimSelf (self-model), Constitution |
| **`controller/`** | Process Orchestration | M1 Controller, Temporal Control Layer (TCL) |
| **`field/`** | Computational Substrate | Field Graph, InfoPackets, Sheaf/Stalk logic |
| **`mte/`** | Language Processing | Machine Translation Engine, PSB mapping |
| **`operators/`** | Field Transformations | PSB primitives, Compression (Centroid), Encoders |
| **`system/`** | Infrastructure | Memory (MVCC), Bootstrap, External Bridges (Godot) |
| **`training/`** | Development & QA | Q1 Simulators, Adversarial Training, SNR testing |
| **`development/`** | Self-Awareness Tools | Consciousness Verification, Observer Practice |
| **`research/`** | Experiments | Prototype embodiment, legacy explorations |
| **`docs/`** | Documentation | Blueprints, specs, and architectural summaries |
| **`tests/`** | Verification | Unit and integration test suite |

---

## 4. Current State Analysis

### Strengths
- **Modular Design:** The project has clear boundaries between governance, self-modeling, and information processing.
- **Innovative Foundations:** The use of sheaf theory and field computation is a significant departure from standard "agentic" frameworks, offering higher potential for stability and self-evolution.
- **Robust Verification:** Includes built-in protocols for detecting confabulation and verifying genuine self-recognition.

### Areas for Improvement
- **Structural Consolidation:** Files are currently spread across several overlapping directories (`src/agent`, `src/simself`, `src/module_b`). Moving to the proposed modular structure will improve maintainability.
- **Immutability Rigor:** The core `InfoPacket` is a frozen dataclass, which is good for stability, but the system must consistently use `dataclasses.replace` to manage updates (fixed in recent patches).
- **Standardization:** Some internal APIs (e.g., `Governor.check` vs `Governor.approve`) were inconsistent across different prototype files (standardized in recent patches).

---

## 5. Next Steps
1. **Physical Reorganization:** Execute the migration of files into the proposed folder structure.
2. **PSB Crystallization:** Focus on the implementation and "crystallization" of the `CAUSE` PSB as the primary bootstrap unit.
3. **Q1/Q2 Scaling:** Scale the noise-injection testing to more complex cross-domain (Vision-Arm-Hand) tasks.
