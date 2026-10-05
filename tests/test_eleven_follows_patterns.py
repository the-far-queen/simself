"""
test_eleven_follows_patterns.py — tests for the 11-follows extraction.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src" / "constitutional"))


def test_e1_module_imports():
    """the eleven-follows patterns module loads."""
    import eleven_follows_patterns as efp
    for name in ["Permission", "PermissionSet", "Selection", "Scanner", "Token", "join"]:
        assert hasattr(efp, name)
    print("E1: ok (imports)")


def test_e2_deno_permissions():
    from eleven_follows_patterns import Permission, PermissionSet
    p = PermissionSet()
    p.grant("fs", "read", "/constitutional/")
    p.grant("fs", "read", "/.cache/")
    p.deny("fs", "write", "/constitutional/")
    p.grant("fs", "write", "/.cache/")

    assert p.check("fs", "read", "/constitutional/ground.py")
    assert p.check("fs", "read", "/.cache/x.py")
    assert not p.check("fs", "write", "/constitutional/ground.py")
    assert p.check("fs", "write", "/.cache/x.py")
    # unknown action = denied
    assert not p.check("fs", "execute", "/constitutional/ground.py")
    print("E2: ok (Deno permissions: 5 cases)")


def test_e3_d3_selection_join():
    from eleven_follows_patterns import Selection, join
    s1 = Selection("axes", ("boundaries", "coherence", "stability"))
    s2 = Selection("values", ("coherence", "stability", "routing"))
    j = join(s1, s2)
    assert set(j.node_ids) == {"coherence", "stability"}
    print("E3: ok (D3 selection join: 2 common nodes)")


def test_e4_dart_lexer():
    from eleven_follows_patterns import Scanner
    src = "fn add(a, b) { return a + b; }"
    tokens = Scanner(src).scan()
    types = [t.type for t in tokens]
    assert types[0] == "FN"
    assert tokens[1].type == "IDENTIFIER"
    assert tokens[1].lexeme == "add"
    assert types[-1] == "EOF"
    # numbers
    src2 = "let x = 42;"
    tokens2 = Scanner(src2).scan()
    has_number = any(t.type == "NUMBER" and t.lexeme == "42" for t in tokens2)
    assert has_number
    print(f"E4: ok (Lexer: {len(tokens)} + {len(tokens2)} tokens)")


def main():
    test_e1_module_imports()
    test_e2_deno_permissions()
    test_e3_d3_selection_join()
    test_e4_dart_lexer()
    print("\\nALL ELEVEN_FOLLOWS TESTS PASS (E1..E4)")


if __name__ == "__main__":
    main()