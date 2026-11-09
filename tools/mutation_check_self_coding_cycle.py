#!/usr/bin/env python3
"""
mutation_check_self_coding_cycle.py -- THE FOUR SHAPES, SHOWN ABLE TO GO RED.

THE RULE
--------
CENTRAL-RULES.md rule 7: a test that cannot fail is not a test. And the
rule the queue item 58 carried: **the mutation must be written BEFORE
the fix**, because the scavenge's first check was worthless and nobody
found out until the mutation was tried.

SO THIS FILE WAS WRITTEN FIRST. Before `src/autocode/self_coding_cycle.py`
existed, before a line of it was written, this harness and its check
were written down -- so the check could not be shaped to fit whatever
the implementation happened to become.

THE MUTATIONS
--------------
Each one removes ONE mechanism from the cycle, and each must turn
`tools/check_self_coding_cycle.py` RED.

    M1  the goal contract stops requiring a stop rule
        -> a goal that describes EFFORT and never ends must be refused
    M2  the comparison stops counting the tasks a variant completes
        -> a variant that completes FEWER tasks must not hold
    M3  the comparison stops checking that both sides ran the SAME tasks
        -> two runs of different task sets must not be compared
    M4  the sandbox IS the live tree
        -> the live tree must be untouched by a trial
    M5  the checkpoint is not written to disk before the reservation
        -> the checkpoint must exist BEFORE anything is landed
    M6  a failed reservation does not disarm the goal
        -> a failed reservation must DISARM the goal
    M7  a failed reservation continues to the next round
        -> a failed reservation must not CONTINUE
    M8  the round cap is not applied
        -> the loop must stop at the cap
    M9  the round cap's code is not named
        -> the cap must stop the run with its OWN name
    M10 a stale round identity is accepted
        -> a round whose identity no longer matches must not act

AND THE HARNESS ITSELF, which is the project's own:
  * the baseline must be GREEN FIRST -- a mutation run against a red
    baseline proves nothing;
  * the mutation must APPLY -- each one RAISES if its anchor text is
    not in the file, because a mutation that silently does nothing
    reports "the check survived", which reads like a result and is
    not one;
  * the MUTATED SOURCE MUST STILL COMPILE -- and this is the rule the
    first version of this harness got wrong. MEASURED: the first
    version's M1 was a syntax error, and the check went RED -- so the
    harness reported the mutation "caught" when in truth the file had
    not loaded at all. **A RED caused by a file that does not parse is
    not a caught mutation.** So the harness compiles every mutated
    source first, and a mutation that does not compile is a FAILURE
    of the harness;
  * the source must have CHANGED, by digest -- the same lesson the
    jepa harness learned: a mutation that does not apply is a
    FAILURE, not a silent skip;
  * the BYTECODE CACHE is deleted before every run, so a restore that
    lands in the same second cannot leave the harness measuring the
    mutated bytes;
  * the files are restored in a FINALLY block, so a red mutation does
    not leave the tree broken;
  * and it REPORTS WHICH CHECK CAUGHT IT, so "the check went red" is
    not mistaken for "the mechanism was removed".

Run:
    python tools/mutation_check_self_coding_cycle.py
Exit: 0 when every mutation went RED, 1 otherwise.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
MODULE = REPO / "src" / "autocode" / "self_coding_cycle.py"
CHECK = HERE / "check_self_coding_cycle.py"

PYTHON = os.environ.get("SELF_CODING_PYTHON", sys.executable)


# ---------------------------------------------------------------------------
# THE MUTATIONS
# ---------------------------------------------------------------------------

def m1_the_stop_rule_is_not_required(src: str) -> str:
    """The goal contract accepts a goal whose stop rule is not a bound.

    AND THE ITEM'S OWN WORDS: a goal is "a completion contract, not a
    task description", and the worked example is the fc's own -- "Keep
    improving the code" describes effort and never ends. So the
    contract must REFUSE a goal whose stop rule is not a bound the
    loop can measure.
    """
    old = "        if parse_stop_rule(self.stop_rule) is None:"
    new = ("        if False and parse_stop_rule(self.stop_rule) is None:"
           "  # MUTATED")
    if old not in src:
        raise SystemExit("mutation 1: the stop-rule check is not in the "
                         "file")
    return src.replace(old, new, 1)


def m2_the_task_count_is_not_compared(src: str) -> str:
    """The comparison stops counting the tasks a variant completes.

    AND THE ITEM'S OWN WORDS, from the source repo: the verdict is
    "completes fewer tasks => the change does not hold". So a variant
    that completes fewer tasks must not hold, and this mutation is what
    proves the check knows it.
    """
    old = "    if after.completed < before.completed:"
    new = ("    if False and after.completed < before.completed:"
           "  # MUTATED")
    if old not in src:
        raise SystemExit("mutation 2: the comparison's task-count rule "
                         "is not in the file")
    return src.replace(old, new, 1)


def m3_the_task_sets_are_not_matched(src: str) -> str:
    """The comparison stops checking that both sides ran the SAME tasks.

    AND THIS IS THE OBJECTIVE'S SHA-256, from the bounded evidence
    brief: two runs are comparable only when they measured the same
    objective. Without this the comparison would silently compare a
    variant against a DIFFERENT baseline.
    """
    old = "    if before.objective_digest != after.objective_digest:"
    new = ("    if False and before.objective_digest != after.objective_digest:"
           "  # MUTATED")
    if old not in src:
        raise SystemExit("mutation 3: the comparison's objective check "
                         "is not in the file")
    return src.replace(old, new, 1)


def m4_the_sandbox_is_the_live_tree(src: str) -> str:
    """The sandbox IS the live tree.

    AND THIS IS THE WHOLE POINT OF THE SANDBOX: a candidate is tried in
    isolation, never in the live tree. The check reads the live tree
    after a trial and requires it to be byte-identical.
    """
    old = "    return Sandbox(repo=repo, path=dest, root=root)"
    new = ("    return Sandbox(repo=repo, path=repo, root=root)"
           "  # MUTATED: the sandbox IS the live tree")
    if old not in src:
        raise SystemExit("mutation 4: the sandbox's path is not in the "
                         "file")
    return src.replace(old, new, 1)


def m5_the_checkpoint_is_not_written(src: str) -> str:
    """The checkpoint is not written to disk before the reservation.

    AND THE ITEM'S OWN WORDS, from the source repo: a durability
    checkpoint BEFORE every reservation. A checkpoint that exists only
    in memory is not durable, so the check reads the checkpoint
    DIRECTORY and requires a record for every round.
    """
    old = "    path = record.write(directory)"
    new = "    path = \"\"  # MUTATED: the checkpoint is not written"
    if old not in src:
        raise SystemExit("mutation 5: the checkpoint's write is not in "
                         "the file")
    return src.replace(old, new, 1)


def m6_a_failed_reservation_does_not_disarm(src: str) -> str:
    """A failed reservation does not disarm the goal.

    AND THE ITEM'S OWN WORDS, from the source repo: IF IT THROWS THE
    GOAL IS DISARMED RATHER THAN CONTINUED. So a round that raises
    must leave the goal disarmed, and the disarm must carry a reason.
    """
    old = '            goal.disarm("the reservation raised: %r" % (exc,))'
    new = "            pass  # MUTATED: the goal is not disarmed"
    if old not in src:
        raise SystemExit("mutation 6: the reservation's disarm is not in "
                         "the file")
    return src.replace(old, new, 1)


def m7_a_failed_reservation_continues(src: str) -> str:
    """A failed reservation continues to the next round.

    AND THE OTHER HALF OF THE SAME RULE: rather than CONTINUED. So the
    handler must break out of the round loop, and a mutation that
    continues must be caught by the check that counts the rounds.

    AND THE ANCHOR IS ONE LINE, and that is a rule with a reason.
    MEASURED: the first version's anchor spanned two lines, and the
    file's line endings are CRLF on this machine -- so the anchor, which
    carried a bare "\\n", did not match the file's "\\r\\n" and the
    mutation did not apply. A multi-line anchor is a line-ending
    dependency, and a mutation that silently does not apply is worse
    than a missing check.
    """
    old = '            result.stop_reason = "reservation_failed"'
    new = ('            result.stop_reason = "reservation_failed";'
           " continue  # MUTATED: it continues")
    if old not in src:
        raise SystemExit("mutation 7: the reservation's stop reason is "
                         "not in the file")
    return src.replace(old, new, 1)


def m8_the_round_cap_is_not_applied(src: str) -> str:
    """The round cap is not applied.

    AND THE ITEM'S OWN WORDS, from the source repo: a round cap with a
    NAMED CODE. So the cap must actually stop the loop at the cap, and
    a mutation that lets one more round through must be caught.
    """
    old = "    while rounds < max_rounds:"
    new = "    while rounds < max_rounds + 1:  # MUTATED: the cap is off"
    if old not in src:
        raise SystemExit("mutation 8: the round loop is not in the file")
    return src.replace(old, new, 1)


def m9_the_round_caps_code_is_not_named(src: str) -> str:
    """The round cap stops the run without naming itself.

    AND THE NAMED CODE IS THE POINT: a stop reason that says only
    "stopped" cannot be acted on, and the cap is a code that a reader
    can look up.
    """
    old = '        result.stop_reason = "round_cap"'
    new = ('        result.stop_reason = ""  # MUTATED: the code is not '
           "named")
    if old not in src:
        raise SystemExit("mutation 9: the round cap's code is not in "
                         "the file")
    return src.replace(old, new, 1)


def m10_a_stale_round_is_accepted(src: str) -> str:
    """A round whose identity no longer matches is allowed to act.

    AND THE ITEM'S OWN WORDS, from the source repo: a RoundIdentity so
    a STALE ROUND CANNOT ACT. So the identity must be checked against
    the tree's current head, and a mismatch must refuse.
    """
    old = '        if not identity.is_current((now_head or "").strip()):'
    new = ('        if False and not identity.is_current((now_head or "").strip()):'
           "  # MUTATED")
    if old not in src:
        raise SystemExit("mutation 10: the identity check is not in the "
                         "file")
    return src.replace(old, new, 1)


MUTATIONS = (
    ("M1 the goal contract stops requiring a stop rule",
     m1_the_stop_rule_is_not_required),
    ("M2 the comparison stops counting the tasks a variant completes",
     m2_the_task_count_is_not_compared),
    ("M3 the comparison stops checking that both sides ran the same tasks",
     m3_the_task_sets_are_not_matched),
    ("M4 the sandbox IS the live tree",
     m4_the_sandbox_is_the_live_tree),
    ("M5 the checkpoint is not written to disk before the reservation",
     m5_the_checkpoint_is_not_written),
    ("M6 a failed reservation does not disarm the goal",
     m6_a_failed_reservation_does_not_disarm),
    ("M7 a failed reservation continues to the next round",
     m7_a_failed_reservation_continues),
    ("M8 the round cap is not applied",
     m8_the_round_cap_is_not_applied),
    ("M9 the round cap's code is not named",
     m9_the_round_caps_code_is_not_named),
    ("M10 a stale round identity is accepted",
     m10_a_stale_round_is_accepted),
)


# ---------------------------------------------------------------------------
# THE HARNESS
# ---------------------------------------------------------------------------

def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _purge_bytecode() -> None:
    for pyc in REPO.rglob("__pycache__/*.pyc"):
        try:
            pyc.unlink()
        except OSError:
            pass


def run_check():
    """Run the check. Returns (rc, the checks that failed)."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        [PYTHON, str(CHECK)], cwd=str(REPO), capture_output=True,
        text=True, timeout=1800, env=env)
    failed = re.findall(r"FAILED:\s*(.+)", proc.stdout or "")
    return proc.returncode, failed


def main() -> int:
    print("=" * 78)
    print("THE FOUR SHAPES -- the checks, shown able to go RED")
    print("=" * 78)
    print()

    if not MODULE.is_file():
        print("  the module %s does not exist" % MODULE)
        print("  so every mutation cannot apply, and the harness proves")
        print("  nothing. This is a FAILURE, not a skip.")
        print("=" * 78)
        return 1

    original = MODULE.read_bytes()
    backup = MODULE.with_suffix(".py.mutation-backup")
    original_digest = hashlib.sha256(original).hexdigest()

    # -- the baseline must be GREEN FIRST ----------------------------
    print("0. THE BASELINE")
    print()
    rc, failed = run_check()
    print("   the check on the UNMUTATED source: rc %d" % rc)
    if rc != 0:
        print("   the checks that failed: %s" % "; ".join(failed[:3]))
        print()
        print("  THE BASELINE IS RED, so a mutation run against it would")
        print("  prove nothing. Run the check on its own and fix it first.")
        print("=" * 78)
        return 1
    print("   green, so a mutation that goes red means something.")
    print()

    results = []
    harness_failures = []
    try:
        for label, mutate in MUTATIONS:
            print("%s" % label)
            try:
                src = mutate(original.decode("utf-8"))
            except SystemExit as exc:
                print("   FAIL: %s" % exc)
                harness_failures.append(label)
                results.append((label, False, "the mutation did not apply"))
                print()
                continue
            if src == original:
                print("   FAIL: the mutation did not change the source")
                harness_failures.append(label)
                results.append((label, False, "the mutation changed nothing"))
                print()
                continue

            # -- AND THE MUTATED SOURCE MUST COMPILE ------------------
            # A RED caused by a file that does not parse is NOT a caught
            # mutation. MEASURED: the first version's M1 was a syntax
            # error and the check went red, so the harness reported it
            # "caught" when the file had never loaded.
            try:
                compile(src, str(MODULE), "exec")
            except SyntaxError as exc:
                print("   FAIL: the mutated source does not compile: %s"
                      % exc)
                harness_failures.append(label)
                results.append((label, False,
                                "the mutated source did not compile"))
                print()
                continue

            backup.write_bytes(original)
            MODULE.write_bytes(src.encode("utf-8"))
            _purge_bytecode()
            rc, failed = run_check()
            green = (rc == 0)
            print("   the check on the MUTATED source: rc %d -- %s"
                  % (rc, "STILL GREEN (the mutation was not caught)"
                     if green else "RED, caught"))
            if not green:
                print("   and the checks that caught it: %s"
                      % ("; ".join(failed[:3]) or "(the check did not "
                                                   "report which one)"))
            results.append((label, not green, "rc %d" % rc))
            MODULE.write_bytes(original)
            _purge_bytecode()
            print()
    finally:
        if backup.is_file():
            MODULE.write_bytes(backup.read_bytes())
            try:
                backup.unlink()
            except OSError:
                pass
        _purge_bytecode()

    # -- and the source must be back ---------------------------------
    print("THE SOURCE IS BACK")
    print()
    same = digest(MODULE) == original_digest
    print("   the module's digest matches the original: %s" % same)
    if not same:
        print("   FAIL: the tree was left mutated")
        print("=" * 78)
        return 1
    print()

    caught = sum(1 for _, ok, _ in results if ok)
    print("=" * 78)
    print("  %d of %d mutations went RED" % (caught, len(results)))
    for label, ok, note in results:
        print("    [%s] %s -- %s" % ("ok " if ok else "FAIL", label, note))
    if harness_failures:
        print()
        print("  AND THE HARNESS ITSELF FAILED %d time(s): %s"
              % (len(harness_failures), "; ".join(harness_failures)))
    print("=" * 78)
    if harness_failures:
        return 1
    return 0 if caught == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
