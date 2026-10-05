"""
anysphere_patterns.py — Cursor / priompt / tiktoken patterns (anysphere, Cursor creators).

priompt pattern was already adopted into simself/src/constitutional/mltr_prompt.py.

the patterns:
  1. tiktoken-rs: token counting — the load-bearing constraint for LLM calls
  2. gpt-4-for-code: prompt composition via JSON-RPC over stdio
  3. priompt: typed prompts as JSX (already adopted)

simself adoption:
  1. axis token counter: every gate call counts tokens; refuse if over budget
  2. constitutional state snapshot = JSON-RPC prompt for any LLM
  3. mltr_prompt nodes composed declaratively (the JSX pattern)
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# Pattern 1: tiktoken-style token counting
# tiktoken is byte-pair encoding. python equivalent: a regex-based estimator.

# simple approximation: ~4 chars per token. tiktoken is more precise but this is load-bearing enough.
def estimate_tokens(text: str) -> int:
    """the tiktoken estimator. ~4 chars per token for english prose.
    for constitutional state (structured JSON), it's closer to 3.5 chars per token.
    for code, ~3 chars per token."""
    # we use the structured-JSON estimate since constitutional state is JSON
    if text.startswith("{") and text.endswith("}"):
        return max(1, len(text) // 4)
    return max(1, len(text) // 4)


# Pattern 2: gpt-4-for-code — JSON-RPC over stdio
# the constitutional state can be sent to any LLM as a JSON-RPC prompt.
# this is the bridge from simself's constitutional kernel to the LLM world.

@dataclass(frozen=True)
class ConstitutionalPrompt:
    """a JSON-RPC ready constitutional prompt. the bridge to any LLM."""
    method: str  # "constitutional/verdict" | "constitutional/snapshot" | "constitutional/atlas_exam"
    params: Dict[str, Any]

    def to_jsonrpc(self, id: int = 1) -> str:
        """emit JSON-RPC 2.0 string. ready for the wire."""
        return json.dumps({
            "jsonrpc": "2.0",
            "id": id,
            "method": self.method,
            "params": self.params,
        }, sort_keys=True)


# Pattern 3: priompt-style declarative composition (already in mltr_prompt.py)
# cross-reference: src/constitutional/mltr_prompt.py
# 6 MLTR primitives: axiom, evidence, refusal-check, lemma, constraint, context


# Token-budget gate: every constitutional prompt must fit in the model's context window.
@dataclass(frozen=True)
class TokenBudget:
    """the constitutional token budget. every prompt checked against it."""
    max_tokens: int = 8000  # default for 8k-context models
    per_axis_budget: int = 100

    def check(self, prompts: List[ConstitutionalPrompt]) -> Tuple[bool, str]:
        total = 0
        for p in prompts:
            total += estimate_tokens(p.to_jsonrpc())
        if total > self.max_tokens:
            return False, f"total_tokens={total} > max={self.max_tokens}"
        return True, f"total_tokens={total} within budget"


if __name__ == "__main__":
    # Pattern 1: tiktoken-style
    short = "hello world"
    long_text = "x" * 4000
    assert estimate_tokens(short) < 10
    assert estimate_tokens(long_text) > 900
    print(f"P1: ok (estimator: '{short}' → {estimate_tokens(short)} tokens; 4000 chars → {estimate_tokens(long_text)})")

    # Pattern 2: JSON-RPC
    p = ConstitutionalPrompt(
        method="constitutional/verdict",
        params={"axes": {"coherence": 0.9}, "target": "/x", "witness": "w"},
    )
    jsonrpc_str = p.to_jsonrpc()
    assert '"jsonrpc": "2.0"' in jsonrpc_str
    assert '"method": "constitutional/verdict"' in jsonrpc_str
    print(f"P2: ok (JSON-RPC: {len(jsonrpc_str)} chars)")

    # Pattern 3: token budget
    budget = TokenBudget(max_tokens=8000)
    ok, msg = budget.check([p])
    assert ok
    print(f"P3.a: ok (budget: {msg})")
    # huge budget break
    many_prompts = [p] * 5000  # ~5000 prompts × ~120 tokens = 600K tokens
    ok, msg = budget.check(many_prompts)
    assert not ok
    print(f"P3.b: ok (over budget: {msg})")

    print("\nALL ANYSPHERE_PATTERNS TESTS PASS")
