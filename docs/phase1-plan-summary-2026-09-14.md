# PHASE 1 IMPLEMENTATION PLAN — SUMMARY

**Source:** Pasted by Robert, 2026-03-03
**Purpose:** Consolidated repo structure + Phase 1 Godot + field-core minimal loop

---

## WHAT IT IS

Phase 1 implementation — a minimal runnable FieldCore agent proving the thesis:
- 2D Godot room with agent, water spout, sensors
- Python field-core with InfoPackets, sheaf graph, mini-LLM stub
- Breakthrough trigger: high multisensory correlation → persistent "water" packet
- Self-play loop generating sentences like "I touch water. Water is cool."

---

## CORE COMPONENTS

| Component | Purpose |
|-----------|---------|
| `src/field/packet.py` | InfoPacket for sensor readings |
| `src/field/graph.py` | InformationField ( sheaf topology) |
| `src/agent/sim_self.py` | SimSelf with curiosity axes |
| `src/agent/governor.py` | M0 invariant enforcer |
| `src/operators/compress.py` | CentroidOperator for compression |
| `src/agent/controller.py` | RecursiveFieldController |
| `src/system/bridge.py` | Godot socket bridge |
| `src/agent/mini_llm.py` | Mini-LLM stub (labeling + sentence gen) |
| `run.py` | Main loop integrating all |

---

## TECH STACK

- **Python 3.11 + uv**
- **Godot 4.3** (GDScript + optional GDextension)
- **HuggingFace transformers** or **llama.cpp** (mini-LLM, 4-bit quantized)
- **NetworkX** for graph field
- **numpy** for vectors

---

## GODOT SCENE STRUCTURE

```
godot_scene/
├── Main.tscn (Node2D root)
├── Walls.tscn (StaticBody2D)
├── WaterSpout.tscn (Area2D)
└── Agent.tscn (KinematicBody2D + sensor script)
```

**Sensor signals:** touch (collision), temperature (proxy), wetness (collision + timer)

---

## MINI-LLM STUB

- Uses Phi-1.5 1.3B quantized 4-bit (or BitNet ternary)
- Two specialists:
  1. Disambiguation/labeling
  2. Curriculum proposal ("next try X")

---

## BREAKTHROUGH TRIGGER

**Condition:** High multisensory correlation + repeated label
**Result:** Create persistent "water" packet (Helen Keller moment)
**Output:** Print "I touch water. Water is cool."

---

## SELF-PLAY LOOP

1. Agent explores → generates utterances
2. Rewards: MMM score + action match
3. High coherence → persist label
4. Loop continues

---

## KILL LIST (CUT FOR SPEED)

- ❌ Full sheaf cohomology (keep only restriction maps / poset topology)
- ❌ "Awakening" narrative framing (systems-first)
- ❌ Overly philosophical axes (keep 3-5 hard constraints)
- ❌ Distributed shards (single process first)

---

## FILES CREATED

```
field-core-agent/
├── README.md
├── requirements.txt
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── field/
│   │   ├── __init__.py
│   │   ├── packet.py      # InfoPacket
│   │   └── graph.py       # InformationField
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── sim_self.py    # SimSelf
│   │   ├── governor.py    # M0 Governor
│   │   └── mini_llm.py    # Mini-LLM stub
│   ├── operators/
│   │   ├── __init__.py
│   │   └── compress.py    # CentroidOperator
│   ├── system/
│   │   ├── __init__.py
│   │   └── bridge.py      # Godot socket bridge
│   └── controller/
│       ├── __init__.py
│       └── controller.py  # RecursiveFieldController
├── godot_scene/           # Godot 4.3 project
│   └── (scene files)
├── tests/
│   ├── __init__.py
│   └── test_field.py
└── run.py                 # Phase 1 main loop
```

---

## DEPENDENCIES

```
numpy==1.26.0
networkx==3.2.1
pytest==7.4.0
```

---

## NOTES

- **Minimal viable:** Proves thesis, not production-ready
- **Extensible:** Add robot actuators, more sensors, real mini-LLM later
- **Godot bridge:** JSON over localhost:5000 (simple, robust)
- **No heavy deps:** No torch unless needed for mini training
- **Open source ready:** MIT license

---

## PHASE 2 (Weeks 4-6)

- Public demo video
- X thread / blog post
- Seed superagent trainer with REP
- DPO-style preference training on high-SNR statements

---

*Summary by Gabby per file-analysis skill*
