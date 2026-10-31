"""
tools/mutation_check_learned_vocab.py -- the checks, shown able to go RED.

THE RULE
--------
A checker that has never been seen to fail has not been shown to work.
MEASURED 2026-10-31, the previous session's dark-pole mutation
harness: it mutated the builder's SOURCE by exact string, and when the
source moved every mutation silently failed to apply -- so the script
reported "0 of 8 mutations went RED" for eight mutations that never
ran. **That is worse than a missing check, because it looks like a
result.**

SO THIS HARNESS MUTATES THE BUILT ARTIFACT, which cannot silently
fail to apply: the mutation is written to the JSON, and the loader
reads the JSON. And the harness ASSERTS THE UNMUTATED CORPUS IS GREEN
FIRST, so a broken harness is caught before any mutation is run.

THE MUTATIONS
-------------
Each corrupts the artifact in a way that should break a specific
check:

  the lists overlap                -> the disjointness check
  a function word is smuggled in    -> the function-word check
  a line-break fragment is smuggled -> the fragment check
  a word is added without the digest -> the digest check
  the digest is edited to match      -> the digest check must still
                                      catch the CONTENT change
  a common verb is removed          -> the role-accuracy check
  the artifact is emptied           -> the loader must refuse

Run: python tools/mutation_check_learned_vocab.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, Dict, List, Tuple

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

ARTIFACT = os.path.join(_SRC, "constitutional", "canon_vocab.json")
TEST_FILE = os.path.join(_ROOT, "tests", "test_learned_vocab.py")


def run_tests() -> Tuple[int, str]:
    """run the check file, and return the exit code and the output."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_FILE, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=_ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def with_mutated_artifact(mutate: Callable[[dict], None]) -> Tuple[int, str]:
    """write a mutated artifact, run the checks, restore the original.

    **AND THE ORIGINAL IS RESTORED IN A FINALLY BLOCK**, so a mutation
    that makes the harness itself fail cannot leave a corrupt artifact
    behind for the next run.

    **AND THE RE-DERIVATION IS RUN AS A CHECK TOO.** MEASURED
    2026-10-31: the mutation "content changed AND the digest edited to
    match" passed every digest-based check, because a digest is a claim
    the artifact makes about itself and a tamperer edits it alongside
    the content. The check that catches it re-derives the lists from
    the canon and compares. So the harness runs that check against the
    mutated artifact, and the mutation is caught only if the check
    fires.
    """
    backup = ARTIFACT + ".backup"
    shutil.copy2(ARTIFACT, backup)
    try:
        with open(ARTIFACT, encoding="utf-8") as fh:
            payload = json.load(fh)
        mutate(payload)
        with open(ARTIFACT, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1, sort_keys=True)
            fh.write("\n")
        code, out = run_tests()
        if code == 0:
            # the suite did not catch it -- the re-derivation might
            code2, out2 = run_rederivation_check()
            out = out + "\n" + out2
            code = code2
        return code, out
    finally:
        shutil.move(backup, ARTIFACT)


def run_rederivation_check() -> Tuple[int, str]:
    """the re-derivation, as a check with an exit code."""
    proc = subprocess.run(
        [sys.executable, "-c", REDERIVATION_SNIPPET],
        cwd=_ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


REDERIVATION_SNIPPET = """
import sys
sys.path.insert(0, 'src')
from constitutional import learned_vocab as lv
v = lv.load_vocabulary()
r = lv.verify_by_rederivation(v)
print('rederivation:', r)
sys.exit(0 if r.get('matches') else 1)
"""


# ===========================================================================
# THE MUTATIONS
# ===========================================================================

def m_overlap(p: dict) -> None:
    """a word in both lists -- the pattern loses its power"""
    p["nouns"] = list(p["verbs"]) + list(p["nouns"])


def m_function_word(p: dict) -> None:
    """'the' is a slot form -- a slot that matches 'the' matches nothing"""
    p["verbs"] = list(p["verbs"]) + ["the"]


def m_fragment(p: dict) -> None:
    """a line-break fragment"""
    p["nouns"] = list(p["nouns"]) + ["a-begging"]


def m_content_without_digest(p: dict) -> None:
    """a word added and the digest NOT updated"""
    p["verbs"] = list(p["verbs"]) + ["a-smuggled-word"]


def m_digest_edited_to_match(p: dict) -> None:
    """a word added AND the digest edited to match it

    **AND THIS ONE MUST STILL GO RED.** The digest only proves the
    artifact was not edited -- it does not prove the content is right.
    If editing the digest alongside the content makes the suite green,
    the digest is the ONLY defence, and a defense that can be edited
    with the thing it defends is not a defence.
    """
    import hashlib
    p["verbs"] = list(p["verbs"]) + ["a-smuggled-word"]
    payload = {"verbs": sorted(p["verbs"]), "nouns": sorted(p["nouns"]),
               "version": p.get("version", "1.0.0"),
               "min_evidence": p.get("min_evidence", 3)}
    raw = json.dumps(payload, sort_keys=True,
                     separators=(",", ":")).encode("utf-8")
    p["content_sha"] = hashlib.sha256(raw).hexdigest()


def m_common_verb_removed(p: dict) -> None:
    """a common verb removed -- the engine can no longer read prose"""
    p["verbs"] = [w for w in p["verbs"] if w != "walked"]


def m_common_noun_removed(p: dict) -> None:
    p["nouns"] = [w for w in p["nouns"] if w != "officer"]


def m_emptied(p: dict) -> None:
    """the artifact emptied -- the loader must refuse it"""
    p["verbs"] = []
    p["nouns"] = []


def m_digest_wrong(p: dict) -> None:
    """the digest corrupted"""
    p["content_sha"] = "0" * 64


MUTATIONS: List[Tuple[str, Callable[[dict], None]]] = [
    ("the lists overlap", m_overlap),
    ("a function word is smuggled in", m_function_word),
    ("a line-break fragment is smuggled in", m_fragment),
    ("content changed, digest not updated", m_content_without_digest),
    ("content changed AND the digest edited to match", m_digest_edited_to_match),
    ("a common verb is removed", m_common_verb_removed),
    ("a common noun is removed", m_common_noun_removed),
    ("the artifact is emptied", m_emptied),
    ("the digest is corrupted", m_digest_wrong),
]


def main() -> int:
    print("=" * 74)
    print("THE MUTATION CHECK -- each mutation must make the suite RED")
    print("=" * 74)
    print()

    code, out = run_tests()
    if code != 0:
        print("  THE UNMUTATED SUITE IS NOT GREEN -- the harness is")
        print("  broken, and no mutation result would mean anything.")
        print()
        print(out[-3000:])
        return 1
    print("  the unmutated suite is GREEN (%d checks)" % _count(out))
    print()

    went_red = 0
    for name, mutate in MUTATIONS:
        code, out = with_mutated_artifact(mutate)
        red = code != 0
        went_red += 1 if red else 0
        verdict = "RED" if red else "GREEN  <-- NOT CAUGHT"
        print("  %-46s %s" % (name, verdict))
        if not red:
            print("      (the suite still passed with this corruption)")

    print()
    print("  %d of %d mutations went RED" % (went_red, len(MUTATIONS)))
    if went_red != len(MUTATIONS):
        print("  A SURVIVING MUTATION MEANS THE CORRESPONDING CHECK IS")
        print("  DECORATIVE. Say so, or fix it.")
        return 1
    return 0


def _count(out: str) -> int:
    import re
    m = re.search(r"(\d+) passed", out)
    return int(m.group(1)) if m else 0


if __name__ == "__main__":
    sys.exit(main())
