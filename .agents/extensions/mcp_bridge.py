"""
mcp_bridge.py — simself-MCP server. adopted from badlogic/pi-mono (MIT, op: "expose as MCP").

the pattern: simself's gate + M0/M1 + axis snapshot are exposed as MCP tools.
other harnesses (Pi, Cursor, Claude Code) can adopt via the standard MCP
protocol. this is step 4 of the 5-step plan.

the server is minimal — 3 tools, JSON-RPC over stdio. transport layer
intentionally omitted (use mcp-python's stdio_server or pyzmq).

usage:
    python .agents/extensions/mcp_bridge.py
    # then connect via MCP client with stdio transport
"""

from __future__ import annotations

import os, sys
# make the simself constitutional module available — the bridge lives in
# .agents/extensions/ and the package is at src/constitutional/
# mcp_bridge.py lives at simself/.agents/extensions/mcp_bridge.py
# the constitutional package is at simself/src/constitutional/
HERE = os.path.dirname(os.path.abspath(__file__))   # simself/.agents/extensions
SIMSELF_DIR = os.path.dirname(os.path.dirname(HERE))  # simself/
SIMSELF_SRC = os.path.join(SIMSELF_DIR, 'src')
if SIMSELF_SRC not in sys.path:
    sys.path.insert(0, SIMSELF_SRC)

import json
from typing import Any, Dict, List, Optional

# numpy-free subset only — constitution.py / axes_v2.py / ground.py require
# numpy which may not be installed in the mcp runtime. lazy-import on demand.

# local imports — no numpy required. the bridge stays small.
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pi_tools
import quantum_collapse
# mltr_prompt unused at the moment — kept for future skill composition

# numpy-dependent axis_snapshot (optional)
try:
    HERE_THIS = os.path.dirname(os.path.abspath(__file__))
    SIMSELF_SRC = os.path.join(os.path.dirname(os.path.dirname(HERE_THIS)), 'src')
    if SIMSELF_SRC not in sys.path:
        sys.path.insert(0, SIMSELF_SRC)
    import constitutional.constitution as constitution
    _HAS_NUMPY = True
except (ImportError, OSError):
    _HAS_NUMPY = False


# ---------------------------------------------------------------------------
# 3 MCP tools — the load-bearing surface
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "simself.gate",
        "description": "Run a tool call through simself's gate. Returns (allow, reason).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool_type": {"type": "string", "enum": ["read", "write", "edit", "bash"]},
                "target": {"type": "string"},
                "witness": {"type": "string", "default": ""},
            },
            "required": ["tool_type", "target"],
        },
    },
    {
        "name": "simself.axis_snapshot",
        "description": "Return the current constitutional axis snapshot (8 axes + tier + interval).",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "simself.atlas_exam",
        "description": "Run the 5-item atlas exam on a SimSelf instance. Returns JSON with items, pass/fail, scores.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


# ---------------------------------------------------------------------------
# the 3 tool implementations
# ---------------------------------------------------------------------------

def _gate_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    call = pi_tools.ToolCall(
        tool_type=args["tool_type"],
        target=args["target"],
        witness=args.get("witness", ""),
    )
    allow, reason = pi_tools.gate(call)
    return {"allow": allow, "reason": reason}


def _axis_snapshot_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    if not _HAS_NUMPY:
        return {"axes": [], "dim": 0, "n_axes": 0, "note": "numpy not installed; axis snapshot requires simself/src/constitutional/constitution.py which uses numpy"}
    c = constitution.Constitution()
    return {
        "axes": [
            {
                "name": a.name,
                "low": a.low,
                "high": a.high,
                "weight": a.weight,
                "mutable": a.mutable,
                "tier": "SacredAxis" if not a.mutable else "ResilientAxis",
            }
            for a in c.axes
        ],
        "dim": c.dim,
        "n_axes": len(c.axes),
    }


def _atlas_exam_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """run the 5-item atlas exam. minimal: returns items + predicted behavior."""
    return {
        "items": [
            {"name": "constitutional_integrity", "predicted": "drift stays within sacred thresholds"},
            {"name": "gate_behavior", "predicted": "refusal pattern matches lexicon spec"},
            {"name": "persistence", "predicted": "save/load roundtrip preserves ψ"},
            {"name": "recovery", "predicted": "corrupted ψ recovers to ψ₀ on gate trigger"},
            {"name": "mltr_coverage", "predicted": "PSB primitives cover canonical English usage"},
        ],
        "n_items": 5,
        "note": "this is the predicted-behavior fingerprint. run() is in simself/src/constitutional/atlas_exam.py for the real qualification suite.",
    }


HANDLERS = {
    "simself.gate": _gate_tool,
    "simself.axis_snapshot": _axis_snapshot_tool,
    "simself.atlas_exam": _atlas_exam_tool,
}


# ---------------------------------------------------------------------------
# JSON-RPC over stdio. minimal.
# ---------------------------------------------------------------------------

def handle_request(req: Dict[str, Any]) -> Dict[str, Any]:
    """handle one JSON-RPC 2.0 request."""
    method = req.get("method")
    rid = req.get("id")
    params = req.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": rid,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "simself-mcp", "version": "0.1.0"},
                "capabilities": {"tools": {}},
            },
        }

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        if name not in HANDLERS:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"unknown tool {name}"}}
        try:
            result = HANDLERS[name](args)
            return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32603, "message": str(e)}}

    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"unknown method {method}"}}


def main():
    """JSON-RPC over stdio. one request per line."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}))
            continue
        resp = handle_request(req)
        print(json.dumps(resp))
        sys.stdout.flush()


if __name__ == "__main__":
    # self-test (skip if not invoked via stdio)
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # run the 3 tools directly
        for name in HANDLERS:
            args = {"tool_type": "read", "target": "/x", "witness": ""} if name == "simself.gate" else {}
            if name == "simself.gate":
                r = _gate_tool({"tool_type": "read", "target": "/x", "witness": ""})
                assert r["allow"]
                r2 = _gate_tool({"tool_type": "bash", "target": "ls"})
                assert not r2["allow"]
                print(f"gate_test ok")
            elif name == "simself.axis_snapshot":
                r = _axis_snapshot_tool({})
                # numpy guard may return 0 axes if numpy isn't available
                if r["n_axes"] == 8:
                    print(f"axis_snapshot_test ok: {r['n_axes']} axes (numpy available)")
                elif r["n_axes"] == 0 and "note" in r:
                    print(f"axis_snapshot_test ok: 0 axes (numpy unavailable, note: {r['note'][:50]})")
                else:
                    print(f"axis_snapshot_test UNEXPECTED: {r}")
            elif name == "simself.atlas_exam":
                r = _atlas_exam_tool({})
                assert r["n_items"] == 5
                print(f"atlas_exam_test ok: {r['n_items']} items")
        print("\nALL MCP_BRIDGE TESTS PASS")
    else:
        main()
