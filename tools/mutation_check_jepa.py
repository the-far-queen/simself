#!/usr/bin/env python3
"""
mutation_check_jepa.py -- the checks, shown able to go RED.

THE RULE
--------
A checker that has never been seen to fail has not been shown to work.
CENTRAL-RULES.md rule 7: "a test that cannot fail is not a test."

**AND THIS PROJECT HAS ALREADY PAID FOR THE LESSON TWICE.** The
dark-pole harness mutated the builder's SOURCE by exact string, and
when the source moved every mutation silently failed to apply -- so the
script reported "0 of 8 mutations went RED" for eight mutations that
never ran. **That is worse than a missing check, because it looks like
a result.** So this harness does three things the dark-pole one did
not:

  1. it ASSERTS THE UNMUTATED SUITE IS GREEN FIRST, so a broken
     harness is caught before any mutation is run;
  2. it ASSERTS THE SOURCE ACTUALLY CHANGED after each mutation, by
     digest -- so a mutation that does not apply is a FAILURE and not a
     silent skip;
  3. it DELETES THE BYTECODE CACHE before every run.

**AND THE THIRD ONE IS NOT A MATTER OF TIDINESS.** MEASURED
2026-11-07: this harness's own author was bitten by it. The source
was mutated, the suite went RED (correctly), the source was restored
with a copy, and the suite went RED AGAIN -- with the unmutated
source. Python keeps the compiled module in `__pycache__` and decides
whether to reuse it from the SOURCE'S MTIME; a restore that lands in
the same second leaves the cache valid, and the suite then measures
the MUTATED code while reading the RESTORED file. **A mutation
harness that can test the wrong bytes is not a mutation harness.**

THE MUTATIONS
--------------
Each one breaks a specific property the checks rely on, and each one
names the check that must catch it:

  the gradient's 1/||p|| factor removed  -> the finite-difference check
  the encoder's backprop transposed      -> the finite-difference check
  the encoder dropped from the forward   -> the finite-difference check
  the prediction's centring removed      -> the finite-difference check
  the probe's ridge scaled down          -> the ridge system's check
  the sized partition's filter removed   -> the partition's checks
  the two views read as the same view    -> the control's check
  the no-op steps report a loss of zero  -> the accounting's check

**AND EVERY MUTATION HERE WAS MEASURED BEFORE IT WAS WRITTEN DOWN.**
Four of the first candidates did not work, and the harness would have
reported them as GREEN:

  * the probe's ridge SCALED DOWN changed the weight norm from 1.87 to
    2.72 and the separation from -1.03 to -1.40, and NEITHER the train
    accuracy (which stayed at 0.7833) NOR the score bound (which is
    100, and the mutant's scores only reach 11.48) saw it. So the
    check is ALGEBRAIC now: the probe's direction must solve the ridge
    system it claims to solve, (X'X + I) w = X'y. MEASURED, the
    residual is 2.2e-15 for the real ridge, 1.50 for the scaled-down
    one and 39.3 for the sign-flipped one.
  * changing the partition's `elif` to `if` is VACUOUS -- the two
    conditions are mutually exclusive at threshold 0, so the
    behaviour does not change at all. The real risk is
    `partition_sized`'s filter, and it only bites when the two halves
    OVERLAP: MEASURED, at 3,351 of 6,700 words the overlap without the
    filter is 2, and at 4,466 it is 2,232. So the check uses a size
    where the halves overlap.
  * the alignment control CANNOT be checked on the real corpus, where
    the cross and within alignments are EQUAL -- that is the finding,
    and it is why the good-views claim is not tested. So the check is
    that the control CAN FIRE: on a synthetic pair whose two views
    genuinely differ it must see a difference. MEASURED: +0.0068 on
    the synthetic pair, +0.0000 on the real one.
  * dropping the encoder from the forward pass made the analytic
    gradient ZERO and the central difference ZERO -- they AGREED, so
    every comparison in the check passed. **A CHECK THAT COMPARES TWO
    ZEROS IS VACUOUS**, so the check now also requires the gradient
    not to be identically zero. MEASURED: the unmutated d_ctx's norm
    is 1.762, so the bound has twelve orders of magnitude of margin.

Run:
    python tools/mutation_check_jepa.py
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from typing import List, Optional, Tuple

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

TEST_FILE = os.path.join(_ROOT, "tests", "test_jepa_canon.py")
SOURCE = os.path.join(_SRC, "jepa_canon.py")
CACHE = os.path.join(_SRC, "__pycache__")


def _clear_cache() -> None:
    """**DELETE THE BYTECODE CACHE, OR THE SUITE MAY MEASURE THE WRONG
    BYTES.** Python reuses a compiled module when the SOURCE'S MTIME
    matches the one recorded in the cache, and a restore that lands in
    the same second matches it. So the cache is deleted before every
    run -- MEASURED 2026-11-07, this harness's author restored the
    source and the suite stayed RED, because it was still running the
    mutated code out of the cache.
    """
    if not os.path.isdir(CACHE):
        return
    for name in os.listdir(CACHE):
        if name.startswith("jepa_canon.") and name.endswith(".pyc"):
            try:
                os.remove(os.path.join(CACHE, name))
            except OSError:
                pass


def run_tests(only: Optional[str] = None) -> Tuple[int, str]:
    """run the check file, and return the exit code and the output."""
    _clear_cache()
    cmd = [sys.executable, "-m", "pytest", TEST_FILE, "-q", "--no-header",
           "-p", "no:cacheprovider"]
    if only:
        cmd += ["-k", only]
    proc = subprocess.run(cmd, cwd=_ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _digest(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _replace_once(text: str, original: str, replacement: str) -> Optional[str]:
    """the text with the replacement made, or None if it did not apply."""
    if original not in text:
        return None
    return text.replace(original, replacement, 1)


# ===========================================================================
# THE MUTATIONS: each replaces a source string with a broken one
# ===========================================================================
MUTATIONS: List[Tuple[str, str, str, str, str]] = [
    # (label, original, replacement, the -k selector, what it breaks)
    ("the gradient's 1/||p|| factor removed",
     "    return [x / n_p for x in w]",
     "    return list(w)",
     "E0",
     "the gradient stops being the gradient of the loss"),

    ("the encoder's backprop transposed",
     "                acc += dp[j] * row[j]",
     "                acc += dp[i] * row[j]",
     "E0",
     "the gradient lands on the wrong index"),

    ("the encoder dropped from the forward pass",
     "        for w in context:\n"
     "            row = self.enc[w]\n"
     "            for j in range(dim):\n"
     "                z_ctx[j] += row[j]",
     "        for w in context:\n"
     "            row = self.enc[w]\n"
     "            for j in range(dim):\n"
     "                z_ctx[j] += 0.0 * row[j]",
     "E0",
     "the encoder is not read, so nothing can be learned"),

    ("the prediction's centring removed",
     "        p_c = [p_hat[j] - m_hat[j] * dot(p_hat, m_hat) for j in range(dim)]",
     "        p_c = list(p_hat)",
     "E0",
     "the prediction collapses onto the corpus mean"),

    ("the probe's ridge scaled down a thousandfold",
     "        ata[i][i] += l2",
     "        ata[i][i] += l2 * 0.001",
     "E5",
     "the probe stops solving the ridge system it claims to solve"),

    ("the sized partition's filter removed",
     "    names = [word for word in names if word not in chosen]",
     "    names = list(names)",
     "E10",
     "a word lands in both lists"),

    ("the two views read as the same view",
     "        for mode, tgt_tokens in ((\"cross\", b[cut_b:]), (\"within\", a[cut_a:])):",
     "        for mode, tgt_tokens in ((\"cross\", a[cut_a:]), (\"within\", a[cut_a:])):",
     "E7",
     "the control cannot see a difference between the views"),

    ("the no-op steps report a loss of zero",
     "        if out is None:\n            return None",
     "        if out is None:\n            return 0.0",
     "E18",
     "a step that learned nothing reports PERFECTION"),
]


def main() -> int:
    print("=" * 74)
    print("THE BASELINE -- the checks must be GREEN before anything is broken")
    print("=" * 74)
    code, out = run_tests()
    if code != 0:
        print(out[-3000:])
        print()
        print("THE BASELINE IS RED. Every mutation below would 'go red' for")
        print("the wrong reason, so the harness refuses to run.")
        return 1
    print("  baseline green")

    with open(SOURCE, "rb") as fh:
        original_bytes = fh.read()
    original_text = original_bytes.decode("utf-8").replace("\r\n", "\n")
    original_digest = _digest(SOURCE)

    print()
    print("=" * 74)
    print("THE MUTATIONS -- each must go RED, and each must ACTUALLY APPLY")
    print("=" * 74)
    caught = 0
    total = 0
    failures: List[str] = []
    for label, original, replacement, selector, breaks in MUTATIONS:
        total += 1
        mutated = _replace_once(original_text, original, replacement)
        if mutated is None:
            failures.append("%s -- THE SOURCE STRING DID NOT MATCH, so the "
                            "mutation never ran" % label)
            print("  NOT APPLIED  %-46s" % label)
            print("      (the source moved: this mutation is STALE)")
            continue
        try:
            with open(SOURCE, "wb") as fh:
                fh.write(mutated.replace("\n", "\r\n").encode("utf-8"))
            if _digest(SOURCE) == original_digest:
                failures.append("%s -- the mutation did not change the file"
                                % label)
                print("  NOT APPLIED  %-46s" % label)
                continue
            code, out = run_tests(only=selector)
        finally:
            with open(SOURCE, "wb") as fh:
                fh.write(original_bytes)
            _clear_cache()

        if code != 0:
            caught += 1
            print("  RED          %-46s  (%s)" % (label, selector))
        else:
            failures.append("%s -- the suite stayed green (it breaks: %s)"
                            % (label, breaks))
            print("  GREEN        %-46s  <-- NOT CAUGHT" % label)
            print("      (it breaks: %s)" % breaks)

    print()
    print("  %d of %d mutations went RED" % (caught, total))
    if failures:
        print()
        print("  THE SURVIVORS, and what each one means:")
        for f in failures:
            print("    - %s" % f)
        print()
        print("  A SURVIVING MUTATION MEANS THE CORRESPONDING CHECK IS")
        print("  DECORATIVE. Say so, or fix it.")
        return 1

    # the baseline must still be green after every revert
    code, out = run_tests()
    if code != 0:
        print()
        print("THE BASELINE IS RED AFTER THE MUTATIONS WERE REVERTED.")
        print(out[-2000:])
        return 1
    print("  the baseline is green again after every revert")
    return 0


if __name__ == "__main__":
    sys.exit(main())
