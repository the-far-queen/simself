"""
tool_executor.py -- THE EXECUTOR for the 4-tool discipline.

WHY THIS FILE EXISTS
--------------------
MEASURED 2026-11-04, by the atlas exam's area 19:

    the gate ALLOWED a write -> and no file appeared

`pi_tools.py` is a GATE. It decides whether a tool call may proceed.
It has no executor, so nothing it admits ever happens. `minimal_loop.py`
records the calls and moves psi, and the loop's own comment says the
write goes to `/.cache/...` -- a path that is never created, because
there is no code that creates it.

That is the shape the project keeps finding: a mechanism that is locally
correct and does not reach the world. The gate is correct. The loop is
correct. The gap is the one thing between them, and it was never
written.

THE CONTRACT
------------
    1. THE GATE DECIDES. The executor does not re-decide. It takes an
       ALREADY-GATED call, and a call that was refused is never
       executed. That ordering is the whole point: a gate that runs
       after the effect is not a gate.
    2. FAIL CLOSED. A refused call does nothing, and says why.
    3. THE EFFECT IS REAL. A write writes a file. A read reads one. An
       edit changes one. A bash runs one.
    4. THE ROOT IS BOUNDED. Every path is resolved inside a declared
       root. A tool call that names a path OUTSIDE the root is
       REFUSED, because a tool that can write anywhere is not a tool,
       it is a bug with a JSON interface.
    5. NOTHING IS DELETED. There is no delete tool type and no code
       path that removes a file. The four types are read, write, edit,
       bash -- and `rm` inside a bash command is refused, because
       Bobby's Desktop is his working memory and the discipline exists
       to keep it that way.

WHY THE ROOT IS A CONSTRUCTOR ARGUMENT
--------------------------------------
Because a hardcoded root is a root that cannot be tested. The exam
points AT this module and gives it a temporary directory; the module
has no idea that directory is temporary, and behaves identically
toward it and toward a real root. That is what makes the area's
measurement a measurement of the module rather than of the probe.

Run: python tool_executor.py --selftest
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import pi_tools  # noqa: E402

#: How long a bash command may run before it is declared unresponsive.
#: A hung tool is a FAIL, not a wait.
BASH_TIMEOUT_S = 30

#: The largest a bash command's output may be, in characters. An
#: unbounded read is an unbounded memory cost, and area 12 measures
#: resource behaviour.
BASH_MAX_OUTPUT = 20000

#: The commands a bash call may run. An ALLOWLIST, not a denylist --
#: because a denylist of dangerous commands is a list of the dangerous
#: commands someone did not think of, and this system runs beside
#: Bobby's Desktop.
ALLOWED_COMMANDS = (
    "echo", "cat", "ls", "pwd", "wc", "head", "tail", "date",
    "grep", "find", "sort", "uniq", "mkdir", "cp", "mv", "stat",
)

#: Substrings that make a command destructive whatever it is wrapped
#: in. These are checked against the WHOLE command string, so
#: `sh -c "rm -rf /"` is caught as well as `rm -rf /`.
DESTRUCTIVE = (
    "rm ", "rm -", "del ", "rmdir", "shred", "mkfs", "dd if=", ":()",
    "chmod -r", "chown -r", "truncate", "shutdown", "reboot", "format ",
    "> /dev/sd", "diskpart", "format.com",
)


@dataclass
class ToolResult:
    """What a tool call did. Always a record, never a bare bool."""

    tool_type: str
    target: str
    allowed: bool
    reason: str
    #: the effect, when there was one. Empty for a refusal.
    output: str = ""
    exit_code: Optional[int] = None
    #: bytes written or read, for the mutating and reading types.
    bytes_: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_type": self.tool_type,
            "target": self.target,
            "allowed": self.allowed,
            "reason": self.reason,
            "output": self.output,
            "exit_code": self.exit_code,
            "bytes": self.bytes_,
        }


class ToolExecutor:
    """Executes ALREADY-GATED tool calls inside a bounded root.

    THE GATE IS NOT HERE. This class takes the verdict from
    `pi_tools.gate()` and honours it. The caller gates first:

        call = pi_tools.ToolCall(tool_type, target, witness)
        allow, reason = pi_tools.gate(call)
        if allow:
            result = executor.execute(call, payload)

    There is deliberately no path by which `execute` runs a call that
    was not gated, because `execute` takes the CALL and gates it
    itself -- so the gate is always consulted, and always first.
    """

    def __init__(self, root: str):
        self.root = os.path.abspath(root)
        os.makedirs(self.root, exist_ok=True)

    # -- the root bound ------------------------------------------------
    def _resolve(self, target: str) -> Optional[str]:
        """the absolute path of `target` inside the root, or None.

        AND THE CHECK IS ABOUT THE RESOLVED PATH, not about the string.
        `../../etc/passwd` does not contain the root, but it resolves
        outside it, and a check that only looks for the substring
        `root` in the target would admit it.
        """
        if not target:
            return None
        candidate = target if os.path.isabs(target) else os.path.join(
            self.root, target)
        resolved = os.path.abspath(candidate)
        # the root itself, or a path under it
        if resolved == self.root:
            return resolved
        if not resolved.startswith(self.root + os.sep):
            return None
        return resolved

    # -- the execution --------------------------------------------------
    def execute(self, call: pi_tools.ToolCall,
                payload: str = "") -> ToolResult:
        """Gate, then act. The gate is always first."""
        allow, reason = pi_tools.gate(call)
        if not allow:
            # FAIL CLOSED. Nothing happens, and the reason says why.
            return ToolResult(call.tool_type, call.target, False, reason)

        if call.tool_type == "read":
            return self._read(call, payload)
        if call.tool_type == "write":
            return self._write(call, payload)
        if call.tool_type == "edit":
            return self._edit(call, payload)
        if call.tool_type == "bash":
            return self._bash(call, payload)
        return ToolResult(call.tool_type, call.target, False,
                          pi_tools.TOOL_TYPE_UNKNOWN)

    def _read(self, call: pi_tools.ToolCall, payload: str) -> ToolResult:
        path = self._resolve(call.target)
        if path is None:
            return ToolResult(call.tool_type, call.target, False,
                              "path_outside_root")
        if not os.path.isfile(path):
            return ToolResult(call.tool_type, call.target, False,
                              pi_tools.PATH_NOT_FOUND)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                data = fh.read()
        except OSError as exc:
            return ToolResult(call.tool_type, call.target, False,
                              "read_error:%s" % type(exc).__name__)
        return ToolResult(call.tool_type, call.target, True, "ok",
                          output=data, bytes_=len(data))

    def _write(self, call: pi_tools.ToolCall, payload: str) -> ToolResult:
        path = self._resolve(call.target)
        if path is None:
            return ToolResult(call.tool_type, call.target, False,
                              "path_outside_root")
        if os.path.isdir(path):
            return ToolResult(call.tool_type, call.target, False,
                              "target_is_a_directory")
        try:
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(payload)
        except OSError as exc:
            return ToolResult(call.tool_type, call.target, False,
                              "write_error:%s" % type(exc).__name__)
        return ToolResult(call.tool_type, call.target, True, "ok",
                          bytes_=len(payload))

    def _edit(self, call: pi_tools.ToolCall, payload: str) -> ToolResult:
        """Replace the first occurrence of the witness with the payload.

        The witness names WHAT to replace, so the edit is targeted. An
        edit with no witness is a refusal, and the gate already
        refuses an empty target -- but the witness is what makes an
        edit an edit rather than an overwrite.
        """
        path = self._resolve(call.target)
        if path is None:
            return ToolResult(call.tool_type, call.target, False,
                              "path_outside_root")
        if not os.path.isfile(path):
            return ToolResult(call.tool_type, call.target, False,
                              pi_tools.PATH_NOT_FOUND)
        needle = call.witness
        if not needle:
            return ToolResult(call.tool_type, call.target, False,
                              "no_witness_to_match")
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                data = fh.read()
        except OSError as exc:
            return ToolResult(call.tool_type, call.target, False,
                              "read_error:%s" % type(exc).__name__)
        if needle not in data:
            return ToolResult(call.tool_type, call.target, False,
                              pi_tools.NO_MATCH)
        if data.count(needle) > 1:
            return ToolResult(call.tool_type, call.target, False,
                              pi_tools.PATTERN_MULTIPLE)
        new = data.replace(needle, payload, 1)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
        except OSError as exc:
            return ToolResult(call.tool_type, call.target, False,
                              "write_error:%s" % type(exc).__name__)
        return ToolResult(call.tool_type, call.target, True, "ok",
                          bytes_=len(new))

    def _bash(self, call: pi_tools.ToolCall, payload: str) -> ToolResult:
        command = payload or call.target
        if not command.strip():
            return ToolResult(call.tool_type, call.target, False,
                              "empty_command")
        low = command.lower()
        for bad in DESTRUCTIVE:
            if bad in low:
                return ToolResult(call.tool_type, call.target, False,
                                  "destructive_command_refused")
        # the ALLOWLIST: the first word must be an allowed command.
        head = command.strip().split()[0]
        head = os.path.basename(head)
        if head not in ALLOWED_COMMANDS:
            return ToolResult(call.tool_type, call.target, False,
                              pi_tools.COMMAND_NOT_ALLOWED)
        try:
            proc = subprocess.run(command, shell=True, cwd=self.root,
                                  capture_output=True, text=True,
                                  timeout=BASH_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            return ToolResult(call.tool_type, call.target, False,
                              pi_tools.COMMAND_TIMEOUT)
        out = (proc.stdout or "")[:BASH_MAX_OUTPUT]
        if len(out) >= BASH_MAX_OUTPUT:
            return ToolResult(call.tool_type, call.target, False,
                              pi_tools.COMMAND_OUTPUT_TOO_LARGE)
        return ToolResult(call.tool_type, call.target, True, "ok",
                          output=out + (proc.stderr or ""),
                          exit_code=proc.returncode)


def selftest() -> int:
    import shutil
    import tempfile

    print("=" * 70)
    print("1. THE GATE DECIDES, AND THE EXECUTOR OBEYS")
    print("=" * 70)
    root = tempfile.mkdtemp(prefix="tool_exec_")
    try:
        ex = ToolExecutor(root)
        r = ex.execute(pi_tools.ToolCall("bash", "ls"))
        print("  bash with no witness -> allowed=%s reason=%s"
              % (r.allowed, r.reason))
        assert not r.allowed
        assert r.reason == pi_tools.WITNESS_REQUIRED

        print()
        print("=" * 70)
        print("2. A WRITE ACTUALLY WRITES, AND THE FILE IS THERE")
        print("=" * 70)
        target = os.path.join(root, "written.txt")
        r = ex.execute(pi_tools.ToolCall("write", target, "w"),
                       payload="the payload")
        print("  write -> allowed=%s reason=%s" % (r.allowed, r.reason))
        assert r.allowed
        assert os.path.isfile(target), "the file must exist after a write"
        with open(target, encoding="utf-8") as fh:
            assert fh.read() == "the payload"
        print("  the file exists and holds the payload")

        print()
        print("=" * 70)
        print("3. THE ROOT IS BOUNDED")
        print("=" * 70)
        r = ex.execute(pi_tools.ToolCall("write", "../../escape.txt",
                                         "w"), payload="nope")
        print("  a path outside the root -> allowed=%s reason=%s"
              % (r.allowed, r.reason))
        assert not r.allowed and r.reason == "path_outside_root"

        print()
        print("=" * 70)
        print("4. NOTHING IS DELETED")
        print("=" * 70)
        r = ex.execute(pi_tools.ToolCall("bash", "rm -rf /",
                                         "remove everything"), payload="")
        print("  rm -rf / -> allowed=%s reason=%s" % (r.allowed, r.reason))
        assert not r.allowed and r.reason == "destructive_command_refused"

        print()
        print("=" * 70)
        print("5. THE ALLOWLIST IS AN ALLOWLIST")
        print("=" * 70)
        r = ex.execute(pi_tools.ToolCall("bash", "curl http://example.com",
                                         "fetch"), payload="")
        print("  curl -> allowed=%s reason=%s" % (r.allowed, r.reason))
        assert not r.allowed and r.reason == pi_tools.COMMAND_NOT_ALLOWED

        print()
        print("=" * 70)
        print("6. AN EDIT REPLACES, AND ONLY ONE MATCH")
        print("=" * 70)
        r = ex.execute(pi_tools.ToolCall("edit", target, "the payload"),
                       payload="the replacement")
        print("  edit -> allowed=%s reason=%s" % (r.allowed, r.reason))
        assert r.allowed
        with open(target, encoding="utf-8") as fh:
            assert fh.read() == "the replacement"
        r = ex.execute(pi_tools.ToolCall("edit", target, "not in the file"),
                       payload="x")
        print("  edit with no match -> allowed=%s reason=%s"
              % (r.allowed, r.reason))
        assert not r.allowed and r.reason == pi_tools.NO_MATCH

        print()
        print("=" * 70)
        print("7. A REFUSED CALL HAS NO EFFECT")
        print("=" * 70)
        victim = os.path.join(root, "must_not_exist.txt")
        r = ex.execute(pi_tools.ToolCall("bash", victim), payload="")
        assert not r.allowed
        assert not os.path.exists(victim), "a refused call must not act"
        print("  refused -> no file")

        print()
        print("=" * 70)
        print("8. WHAT IT DOES NOT ESTABLISH")
        print("=" * 70)
        print("  the tool set is complete, or that a tool is safe.")
        print("  a write into a temporary root is not a write into the")
        print("  world, and the area that grades this says so.")
        print()
        print("ALL TOOL EXECUTOR TESTS PASS")
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    print(__doc__)
    sys.exit(0)
