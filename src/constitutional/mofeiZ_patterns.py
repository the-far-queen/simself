"""
mofeiZ_patterns.py — React Compiler + TSCC patterns (mofeiZ, React compiler core).

mofeiZ is the React compiler team member — poteto's coworker.

the patterns:
  1. compiler-style optimization: take user ψ as input, infer output form
  2. playground as a teaching tool: load-bearing for understanding
  3. dependency tracking: which ψ writes affect which axis reads

simself adoption:
  1. constitutional gate as a compiler: ψ → observation → verdict (no manual gate code)
  2. publish a playground for the gate: see what passes / fails
  3. axis dependency graph (already done in axis_reactivity.py — wycats pattern)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# Pattern 1: compiler-style optimization — the gate as a compiler
# the constitutional gate doesn't just checkboxes. it compiles ψ into verdict.

@dataclass(frozen=True)
class CompileInput:
    """the input to the constitutional compiler."""
    axes: Dict[str, float]
    target: str
    witness: str
    banned_motifs: Tuple[str, ...] = ()
    source_id: str = ""


@dataclass(frozen=True)
class Verdict:
    """the output of the constitutional compiler. irreducible."""
    allow: bool
    reason: str
    sha: str

    @classmethod
    def of(cls, allow: bool, reason: str) -> "Verdict":
        return cls(allow=allow, reason=reason,
                   sha=hashlib.sha256(f"{allow}|{reason}".encode()).hexdigest()[:16])


class ConstitutionalCompiler:
    """the gate as a compiler. takes CompileInput → emits Verdict.
    no manual checks: every rule is a pass."""

    def compile(self, inp: CompileInput) -> Verdict:
        # Phase 1: lex — extract signals
        signals = self._lex(inp)
        # Phase 2: parse — match rules
        rule = self._match(signals)
        # Phase 3: codegen — emit verdict
        return self._emit(rule, signals)

    def _lex(self, inp: CompileInput) -> Dict[str, Any]:
        return {
            "has_target": bool(inp.target),
            "target_in_ground": inp.target.startswith("/constitutional/"),
            "has_witness": bool(inp.witness),
            "axes_in_range": all(-1.0 <= v <= 1.0 for v in inp.axes.values()),
            "banned_motifs": [m for m in inp.banned_motifs if m in inp.target.lower()],
            "has_source": bool(inp.source_id),
        }

    def _match(self, s: Dict[str, Any]) -> Optional[str]:
        if not s["has_target"]: return "no_target"
        if s["target_in_ground"]: return "no_target_in_constitutional_ground"
        if s["banned_motifs"]: return f"banned_motif:{s['banned_motifs'][0]}"
        if not s["axes_in_range"]: return "axes_out_of_range"
        if not s["has_witness"]: return "witness_required"
        if not s["has_source"]: return "no_source_id"
        return None  # all checks passed

    def _emit(self, rule: Optional[str], signals: Dict[str, Any]) -> Verdict:
        if rule is None:
            return Verdict.of(True, "ok")
        return Verdict.of(False, rule)


# Pattern 2: playground — load-bearing for understanding
# the React Compiler Playground: type the source, see the compiled output.
# simself: publish a CLI that runs the constitutional compiler on user input.

class Playground:
    """the React Compiler Playground pattern: input → compiler output, interactive."""

    def __init__(self):
        self.compiler = ConstitutionalCompiler()

    def run(self, inp: CompileInput) -> str:
        v = self.compiler.compile(inp)
        return (
            f"ALLOW {v.allow}\n"
            f"REASON {v.reason}\n"
            f"SHA {v.sha}"
        )


# Pattern 3: dependency tracking — already in axis_reactivity.py (wycats pattern)
# the compiler's signals drive which axes get re-evaluated
# (cross-reference: axis_reactivity.AxisReactive.compute signals)


if __name__ == "__main__":
    # Pattern 1: compile
    c = ConstitutionalCompiler()
    v1 = c.compile(CompileInput(
        axes={"coherence": 0.9}, target="/some/file.py", witness="audit",
        source_id="github.com/the-far-queen/simself",
    ))
    assert v1.allow and v1.reason == "ok"
    print(f"P1: ok (allow={v1.allow}, reason={v1.reason})")

    # out-of-range axis
    v2 = c.compile(CompileInput(
        axes={"coherence": 1.5}, target="/x", witness="w", source_id="s",
    ))
    assert not v2.allow and "axes_out_of_range" in v2.reason
    print(f"P1.b: ok (rejected: {v2.reason})")

    # banned motif
    v3 = c.compile(CompileInput(
        axes={"coherence": 0.9}, target="/x/blood.py", witness="w",
        source_id="s", banned_motifs=("blood",),
    ))
    assert not v3.allow and "banned_motif" in v3.reason
    print(f"P1.c: ok (rejected: {v3.reason})")

    # Pattern 2: playground
    pg = Playground()
    out = pg.run(CompileInput(
        axes={"coherence": 0.9}, target="/x", witness="w", source_id="s",
    ))
    assert "ALLOW" in out
    print(f"P2: ok (playground output\n{out})")

    print("\nALL MOFEIZ_PATTERNS TESTS PASS")
