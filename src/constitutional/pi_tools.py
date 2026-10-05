"""
pi_tools.py — the 4-tool discipline. adopted from badlogic/pi-mono (MIT).

Pi ships 4 tools by design: read, write, edit, bash. Mario's argument:
"every tool you load into the agent's context costs tokens on every turn.
A smaller default palette is easier to reason about turn over turn."

simself's gate is a 1-bit veto. every gate call resolves to one of 4 tool-types:

  read   — read files (no mutation)
  write  — write new files (creates)
  edit   — edit existing files (mutates in place)
  bash   — execute commands (side effects)

The gate pattern: a gate call is a (tool_type, target, witness) tuple.
The gate returns (allow, reason). reason ∈ TOOL_REASONS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


# the 4 tool types — load-bearing. do not add a 5th without revising
# the constitutional axes, the gate, the atlas-exam, and the SKILL.md files.
TOOL_TYPES = ("read", "write", "edit", "bash")


@dataclass(frozen=True)
class ToolCall:
    """One gate call: (tool_type, target, witness)."""
    tool_type: str          # one of TOOL_TYPES
    target: str             # the file path / command
    witness: str = ""       # the reason this call is being made


# reasons — only the 4 most canonical. the canonical M0 governor reason set.
NO_TARGET = "no_target"
TOOL_TYPE_UNKNOWN = "tool_type_unknown"
TOOL_DISABLED = "tool_disabled"
WITNESS_REQUIRED = "witness_required"
PATH_NOT_FOUND = "path_not_found"
NO_MATCH = "no_match"
PATTERN_MULTIPLE = "pattern_multiple"
COMMAND_NOT_ALLOWED = "command_not_allowed"
COMMAND_TIMEOUT = "command_timeout"
COMMAND_OUTPUT_TOO_LARGE = "command_output_too_large"


def gate(call: ToolCall) -> Tuple[bool, str]:
    """Gate a tool call. Returns (allow, reason)."""

    if call.tool_type not in TOOL_TYPES:
        return False, TOOL_TYPE_UNKNOWN

    if not call.target:
        return False, NO_TARGET

    if call.tool_type == "bash":
        if not call.witness:
            return False, WITNESS_REQUIRED
        return True, "ok"

    # read / write / edit all just need a target
    return True, "ok"


if __name__ == "__main__":
    # 3 tool types all valid without witness
    for t in ("read", "write", "edit"):
        c = ToolCall(tool_type=t, target="/some/path", witness="")
        allow, reason = gate(c)
        assert allow, f"{t} should pass"
    print("3 tool types (read/write/edit) all valid without witness")

    # bash without witness refused
    c = ToolCall(tool_type="bash", target="ls")
    allow, reason = gate(c)
    assert not allow and reason == WITNESS_REQUIRED
    print(f"bash no witness refused: {reason}")

    # bash with witness passes
    c = ToolCall(tool_type="bash", target="ls", witness="list files")
    allow, reason = gate(c)
    assert allow
    print("bash with witness passes")

    # unknown tool type refused
    c = ToolCall(tool_type="tweet", target="x")
    allow, reason = gate(c)
    assert not allow and reason == TOOL_TYPE_UNKNOWN
    print(f"unknown tool refused: {reason}")

    # empty target refused
    c = ToolCall(tool_type="read", target="")
    allow, reason = gate(c)
    assert not allow and reason == NO_TARGET
    print(f"empty target refused: {reason}")

    print("\nALL PI_TOOLS TESTS PASS")
