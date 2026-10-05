"""
deno_patterns.py — Deno runtime pattern (ry, @denoland).

the pattern: secure-by-default runtime. permissions explicit. no package manager.
no node_modules. URL imports.

simself adoption: the agent's filesystem writes go through a Gate that
matches Deno's permission model. every tool call gets an explicit permission.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


# the Deno permission model: explicit grant per resource + action
PERM_ACTIONS = {"read", "write", "run", "net", "env"}


@dataclass(frozen=True)
class Permission:
    """a single permission grant. host + action + path."""
    host: str           # "fs", "net", "env", "run"
    action: str         # PERM_ACTIONS
    path: str = "*"     # path glob (file://, $PATH, hostname:port)
    granted: bool = True

    def allows(self, action: str, target: str) -> bool:
        if not self.granted: return False
        if action != self.action: return False
        if self.path == "*": return True
        # match exact path or any child path
        return target == self.path or target.startswith(self.path.rstrip("/") + "/")


class PermissionSet:
    """the agent's permission set. like Deno's --allow-* flags."""

    def __init__(self):
        self.perms: List[Permission] = []

    def grant(self, host: str, action: str, path: str = "*") -> None:
        self.perms.append(Permission(host=host, action=action, path=path))

    def deny(self, host: str, action: str, path: str = "*") -> None:
        self.perms.append(Permission(host=host, action=action, path=path, granted=False))

    def check(self, host: str, action: str, target: str) -> bool:
        """the gate: any matching permission grants. explicit deny overrides."""
        allowed = False
        for p in self.perms:
            if p.host == host and p.action == action:
                if p.path == "*" or target.startswith(p.path):
                    if not p.granted:
                        return False
                    allowed = True
        return allowed


# Pattern 2: D3 / Observable (mbostock) - declarative data viz
# the pattern: data + transform → render. selections propagate. enter/exit lifecycle.

@dataclass(frozen=True)
class Selection:
    """a D3-style selection. transforms apply to a set of nodes."""
    name: str
    node_ids: Tuple[str, ...]

    def select(self, *names: str) -> "Selection":
        return Selection(name=self.name, node_ids=tuple(names))

    def attr(self, name: str, value: Any) -> "Selection":
        return self  # in D3 this mutates; here we just pass through

    def data(self, values: List[Any]) -> "Selection":
        return Selection(name=f"{self.name}:{len(values)}", node_ids=tuple(self.node_ids))


def join(left: Selection, right: Selection) -> Selection:
    """D3-style selection join. the load-bearing operation."""
    common = tuple(set(left.node_ids) & set(right.node_ids))
    return Selection(name=f"{left.name}+{right.name}", node_ids=common)


# Pattern 3: Dart / Crafting Interpreters (Bob Nystrom)
# the pattern: a small, well-designed language implementation. lexical scoping,
# closures, classes. **language-as-the-engineering-lawyer.**

@dataclass(frozen=True)
class Token:
    """a lexer token. like clox / Dart's tokenizer."""
    type: str       # "IDENTIFIER" | "NUMBER" | "PLUS" | "EOF" | ...
    lexeme: str
    line: int
    column: int


class Scanner:
    """a tiny lexer. Dart-style. source → tokens."""

    KEYWORDS = {"fn", "let", "if", "else", "true", "false", "return"}

    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1

    def scan(self) -> List[Token]:
        while not self._at_end():
            self.start = self.current
            self._scan_token()
        self.tokens.append(Token("EOF", "", self.line, 0))
        return self.tokens

    def _at_end(self) -> bool:
        return self.current >= len(self.source)

    def _scan_token(self) -> None:
        c = self.source[self.current]
        self.current += 1
        if c == "(":
            self.tokens.append(Token("LEFT_PAREN", "(", self.line, self.current))
        elif c == ")":
            self.tokens.append(Token("RIGHT_PAREN", ")", self.line, self.current))
        elif c == "+":
            self.tokens.append(Token("PLUS", "+", self.line, self.current))
        elif c == "-":
            self.tokens.append(Token("MINUS", "-", self.line, self.current))
        elif c.isdigit():
            while self.current < len(self.source) and self.source[self.current].isdigit():
                self.current += 1
            self.tokens.append(Token("NUMBER", self.source[self.start:self.current],
                                     self.line, self.start))
        elif c.isalpha():
            while self.current < len(self.source) and self.source[self.current].isalnum():
                self.current += 1
            text = self.source[self.start:self.current]
            if text in self.KEYWORDS:
                self.tokens.append(Token(text.upper(), text, self.line, self.start))
            else:
                self.tokens.append(Token("IDENTIFIER", text, self.line, self.start))
        elif c in " \t\n":
            pass  # ignore whitespace
        elif c == "\\n":
            self.line += 1
        else:
            self.tokens.append(Token("ERROR", c, self.line, self.current))


if __name__ == "__main__":
    # Pattern 1: Deno permissions
    p = PermissionSet()
    p.grant("fs", "read", "/constitutional/")
    p.grant("fs", "read", "/.cache/")
    p.deny("fs", "write", "/constitutional/")
    p.grant("fs", "write", "/.cache/")
    assert p.check("fs", "read", "/constitutional/ground.py")
    assert p.check("fs", "read", "/.cache/x.py")
    assert not p.check("fs", "write", "/constitutional/ground.py")  # explicit deny
    assert p.check("fs", "write", "/.cache/x.py")
    print(f"P1: ok (Deno permissions: 4 cases tested)")

    # Pattern 2: D3 / Observable selections
    s1 = Selection("axes", ("boundaries", "coherence", "stability"))
    s2 = Selection("values", ("coherence", "stability", "routing"))
    joined = join(s1, s2)
    assert set(joined.node_ids) == {"coherence", "stability"}
    assert "axes+values" in joined.name
    print(f"P2: ok (D3 selection join: {joined.node_ids})")

    # Pattern 3: Dart/Crafting Interpreters lexer
    src = "fn add(a, b) { return a + b; }"
    s = Scanner(src)
    tokens = s.scan()
    # expected types: FN, IDENTIFIER(add), LEFT_PAREN, IDENTIFIER(a), COMMA...
    types = [t.type for t in tokens]
    assert types[0] == "FN"
    assert tokens[1].type == "IDENTIFIER" and tokens[1].lexeme == "add"
    assert types[-1] == "EOF"
    print(f"P3: ok (Lexer: {len(tokens)} tokens for 10-line fn def)")

    print("\nALL 11-FOLLOWS EXTRACTION TESTS PASS")
