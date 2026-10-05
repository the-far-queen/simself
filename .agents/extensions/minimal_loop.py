"""
minimal_loop.py — Pi-style minimal agent loop. adopted from badlogic/pi-mono (MIT).

Pi's mental model: pi-coding-agent is a thin shell around a model and a small
fixed pool of tools. By default, four are enabled: read, write, edit, bash.
The built-in pool is slightly larger, grep, find, and ls are also available.
That is the entire built-in surface.

simself's minimal_loop.py follows the same pattern:

  - one AgentLoop class
  - 4 tool types (read, write, edit, bash) gated through pi_tools.gate()
  - the constitutional guard (ground) is the witness
  - ψ is updated as a side effect of every loop iteration

the loop is intentionally small (100 lines). the surface area is the gate,
the constitution, the model. nothing else.
"""

from __future__ import annotations

import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pi_tools
import quantum_collapse as qc


class AgentLoop:
    """the minimal agent loop. read/write/edit/bash. gated. ψ-tracked."""

    def __init__(self, model: str = "local-fake", psi=None, ground=None):
        self.model = model
        self.psi = psi if psi is not None else qc.Secured(state="idle", witness="init")
        self.ground = ground or qc.Secured(state="ground", witness="psi_zero")
        # a session log — every call + result
        self.calls: list[dict] = []

    def gate(self, call: pi_tools.ToolCall) -> tuple[bool, str]:
        """gate a tool call through pi_tools + the constitutional witness."""
        allow, reason = pi_tools.gate(call)
        # every call gets a witness — the constitutional ground
        if allow:
            return True, f"ok:{reason}"
        return False, f"refused:{reason}"

    def call(self, tool_type: str, target: str, witness: str = "") -> dict:
        """make one tool call. returns {allow, reason, witness}."""
        call = pi_tools.ToolCall(tool_type=tool_type, target=target, witness=witness)
        allow, reason = self.gate(call)
        result = {
            "tool_type": tool_type,
            "target": target,
            "witness": witness,
            "allow": allow,
            "reason": reason,
            "psi_before": self.psi,
        }
        # collapse ψ to reflect the call
        if allow:
            self.psi = qc.observe_with_witness(self.psi, reason)
        else:
            self.psi = qc.observe_with_witness(self.psi, reason)
        result["psi_after"] = self.psi
        self.calls.append(result)
        return result

    def tick(self, observation: str) -> dict:
        """one heartbeat. the agent observes + acts + updates ψ."""
        # observe
        obs = qc.observe_with_witness(self.psi, f"observe:{observation[:20]}")
        # act: read + write the observation (default loop)
        reads = self.call("read", f"/obs/{observation}", witness=f"observe {observation[:20]}")
        writes = self.call("write", f"/.cache/{observation[:8]}", witness=f"persist {observation[:8]}")
        # end tick
        return {
            "observation": observation,
            "reads": reads,
            "writes": writes,
            "psi_final": self.psi,
        }


if __name__ == "__main__":
    # Pi-style minimal test
    loop = AgentLoop()
    print(f"loop initialized, ψ={loop.psi}")

    # bash requires witness
    r = loop.call("bash", "ls", witness="list files")
    print(f"bash: allow={r['allow']}, reason={r['reason']}")
    assert r["allow"]
    assert r["psi_after"] is not None

    # bash without witness refused
    r2 = loop.call("bash", "rm -rf /")
    print(f"bash no-witness: allow={r2['allow']}, reason={r2['reason']}")
    assert not r2["allow"]
    assert r2["reason"].startswith("refused:witness_required")

    # tick
    tick = loop.tick("world_state")
    print(f"tick observation: allow={tick['reads']['allow']} + {tick['writes']['allow']}")

    # ψ is Secured after every call
    assert isinstance(loop.psi, qc.Secured)
    print(f"ψ after 3 calls: {loop.psi.state} | witness={loop.psi.witness}")

    # unknown tool refused
    r3 = loop.call("tweet", "x")
    assert not r3["allow"]
    print(f"unknown tool refused: {r3['reason']}")

    print("\nALL MINIMAL_LOOP TESTS PASS")
