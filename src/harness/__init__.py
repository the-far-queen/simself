# Harness — Agent & Avatar Patterns
"""
Patterns borrowed from game development and AI agent frameworks,
restructured as a SimSelf subpackage.

Modules:
- gate: external tool calls pass through the Governor first
- memory: short-term vector memory with bounded size + similarity retrieval
- planner: goal decomposition
- persistence: soul-file snapshot save/load
- resources: avatar resources (stamina, cognitive load)
- tools: tool registry with handlers

Importable as a package:
    from harness import gate, memory, planner, persistence, resources, tools

The relative imports inside gate.py resolve to SimSelf's core modules.
"""
