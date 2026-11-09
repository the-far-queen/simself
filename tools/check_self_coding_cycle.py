#!/usr/bin/env python3
"""
check_self_coding_cycle.py -- THE FOUR SHAPES, EXERCISED ON A REAL TREE.

**AND THIS FILE WAS WRITTEN BEFORE THE MECHANISM.** Queue item 58: "the
mutation must be written before the fix -- the same rule that just
caught the scavenge's first check being worthless." So the check and
its mutation harness were written first, and the module was built to
satisfy them rather than the other way round.

THE FOUR SHAPES, and the four sources they come from
-----------------------------------------------------
    the STOP RULE    a goal is "a completion contract, not a task
                     description", with five parts: end state, proof,
                     boundaries, loop, stop rule. The worked example is
                     the fc's own -- "Keep improving the code" describes
                     effort and never ends. So the contract must
                     REFUSE a goal whose stop rule is not a bound.

    the COMPARISON   the variant BEFORE and the variant AFTER, side by
                     side, and the verdict is "completes fewer tasks =>
                     the change does not hold". Two runs are comparable
                     only when they measured the same objective, so the
                     objective's SHA-256 travels with the result.

    the SANDBOX      a candidate is tried in isolation, never in the
                     live tree. So the live tree is read after a trial
                     and must be byte-identical.

    the ROLLBACK     a durability checkpoint BEFORE every reservation,
                     and if the reservation throws the goal is DISARMED
                     rather than continued, then every condition is
                     re-checked, plus a round cap with a named code and
                     a round identity so a stale round cannot act.

THE CASES
---------
    1  a complete goal contract has no problems
    2  a goal with no stop rule is refused, and so is "keep improving"
    3  a comparison against fewer completed tasks does not hold
    4  two runs of DIFFERENT task sets are not comparable
    5  the sandbox leaves the live tree untouched
    6  the checkpoint is on disk BEFORE the reservation, and readable
    7  a failed reservation DISARMS the goal and does not continue
    8  the round cap stops the run, with its named code
    9  a stale round identity is refused, and nothing is adopted
    10 a variant that holds is adopted, and the live tree carries it
    11 an adoption whose verification fails ROLLS BACK, and the tree
       is exactly as it was

Run:
    python tools/check_self_coding_cycle.py
Exit: 0 when every case holds, 1 otherwise.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Tuple

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SRC = REPO / "src"

for _p in (str(SRC),):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from autocode.self_coding_cycle import (  # noqa: E402
    Checkpoint,
    GoalContract,
    RoundIdentity,
    RunResult,
    Task,
    compare,
    make_sandbox,
    parse_stop_rule,
    run_cycle,
    run_tasks,
)


# ---------------------------------------------------------------------------
# THE FIXTURE REPOSITORY
# ---------------------------------------------------------------------------

#: The fixture's marker file holds the number of tasks that pass. The
#: two tasks each read it, so a diff that lowers it makes the variant
#: complete FEWER tasks -- which is the comparison's own rule.
MARKER = "marker.txt"
LIB = "lib.py"
TESTS = "tests"


def _git(repo: str, *args: str, timeout: int = 120) -> Tuple[int, str, str]:
    p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True,
                       text=True, timeout=timeout)
    return p.returncode, (p.stdout or ""), (p.stderr or "")


def build_fixture(root: str, name: str = "tree") -> str:
    """A REAL git repository with a real marker file.

    AND IT IS A GIT REPOSITORY, because the rollback restores through
    git and the check reads git's own verdict on the tree afterwards.
    """
    dest = os.path.join(root, name)
    os.makedirs(os.path.join(dest, TESTS), exist_ok=True)
    with open(os.path.join(dest, MARKER), "w", encoding="utf-8") as fh:
        fh.write("2\n")
    with open(os.path.join(dest, LIB), "w", encoding="utf-8") as fh:
        fh.write("def add(a, b):\n    return a + b\n")
    with open(os.path.join(dest, TESTS, "test_lib.py"), "w",
              encoding="utf-8") as fh:
        fh.write("from lib import add\n\n\ndef test_add():\n"
                 "    assert add(1, 2) == 3\n")
    _git(dest, "init", "-q")
    _git(dest, "config", "user.email", "cycle@fixture.invalid")
    _git(dest, "config", "user.name", "the cycle fixture")
    _git(dest, "config", "commit.gpgsign", "false")
    _git(dest, "add", "-A")
    _git(dest, "commit", "-q", "-m", "the fixture's first commit")
    return dest


def fixture_tasks(repo: str) -> List[Task]:
    """Two tasks, each of which reads the marker file.

    AND A TASK IS A COMMAND, so a task can fail for a reason the
    check can read -- and the comparison's rule is about how many of
    them COMPLETE.
    """
    py = sys.executable
    cmd = (py, "-c",
           "import pathlib,sys;"
           "v=int(pathlib.Path(%r).read_text().strip());"
           "sys.exit(0 if v>=2 else 1)" % MARKER)
    return [Task("marker_a", cmd), Task("marker_b", cmd)]


def diff_for(marker_value: str) -> str:
    """A diff that sets the marker to a value.

    AND IT IS A REAL UNIFIED DIFF, because `git apply` is what the
    sandbox and the adoption both use.
    """
    return (
        "diff --git a/%s b/%s\n"
        "--- a/%s\n"
        "+++ b/%s\n"
        "@@ -1 +1 @@\n"
        "-2\n"
        "+%s\n" % (MARKER, MARKER, MARKER, MARKER, marker_value)
    )


def tree_state(repo: str) -> List[str]:
    rc, out, _ = _git(repo, "status", "--porcelain")
    if rc != 0:
        return ["<the status could not be read>"]
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def file_digest(repo: str, rel: str) -> str:
    path = os.path.join(repo, rel)
    if not os.path.isfile(path):
        return "<absent>"
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def head_of(repo: str) -> str:
    rc, out, _ = _git(repo, "rev-parse", "HEAD")
    return out.strip() if rc == 0 else ""


def complete_goal(**overrides) -> GoalContract:
    base = dict(
        end_state="the marker file reads 3",
        proof="python -c \"print(open('marker.txt').read())\"",
        boundaries=("the ground does not move",),
        loop="one round per candidate",
        stop_rule="adopted >= 1",
    )
    base.update(overrides)
    return GoalContract(**base)


# ---------------------------------------------------------------------------
# THE CHECK
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 78)
    print("THE FOUR SHAPES -- a stop rule, a comparison, a sandbox, a rollback")
    print("=" * 78)
    print()

    failures: List[str] = []

    def check(label: str, cond: bool, extra: str = "") -> bool:
        print("  [%s] %s%s" % ("ok " if cond else "FAIL", label,
                               (" -- " + extra) if extra else ""))
        if not cond:
            failures.append(label)
        return bool(cond)

    tmp = tempfile.mkdtemp(prefix="check_cycle_")
    try:
        # -- 1. THE GOAL CONTRACT -------------------------------------
        print("1. THE GOAL CONTRACT")
        print()
        goal = complete_goal()
        problems = goal.problems()
        check("a complete goal has no problems", not problems,
              "; ".join(problems[:3]))
        check("and the five parts are named",
              all(getattr(goal, part) for part in
                  ("end_state", "proof", "boundaries", "loop", "stop_rule")))

        for part in ("end_state", "proof", "boundaries", "loop", "stop_rule"):
            empty = complete_goal(**{part: "" if part != "boundaries" else ()})
            ps = empty.problems()
            check("a goal with no %s is refused" % part, bool(ps),
                  "; ".join(ps[:2]) or "no problem was reported")

        # AND THE FC'S OWN EXAMPLE, which is the worked case in the
        # source: "Keep improving the code" describes effort and never
        # ends, so it is not a completion contract.
        effort = complete_goal(stop_rule="keep improving the code")
        ps = effort.problems()
        check("and 'keep improving the code' is refused", bool(ps),
              "; ".join(ps[:2]) or "no problem was reported")
        check("and the refusal names the stop rule",
              any("stop rule" in p for p in ps), "; ".join(ps[:2]))
        check("and the stop rule parses into a measurable bound",
              parse_stop_rule("adopted >= 1") is not None)
        check("and an effort phrase does not parse",
              parse_stop_rule("keep improving the code") is None)

        # -- 2. THE COMPARISON ----------------------------------------
        print()
        print("2. THE COMPARISON")
        print()
        before = RunResult(completed=2, failed=0, total=2, cost=1.0,
                            objective_digest="d" * 64)
        fewer = RunResult(completed=1, failed=1, total=2, cost=1.2,
                           objective_digest="d" * 64)
        same = RunResult(completed=2, failed=0, total=2, cost=1.1,
                         objective_digest="d" * 64)
        other = RunResult(completed=2, failed=0, total=2, cost=1.1,
                          objective_digest="e" * 64)

        cmp_fewer = compare(before, fewer)
        check("a variant that completes fewer tasks does NOT hold",
              not cmp_fewer.holds, cmp_fewer.reason)
        check("and the reason says so",
              "fewer tasks" in cmp_fewer.reason, cmp_fewer.reason)
        cmp_same = compare(before, same)
        check("a variant that completes the same tasks holds",
              cmp_same.holds, cmp_same.reason)
        cmp_other = compare(before, other)
        check("two runs of DIFFERENT task sets are not comparable",
              not cmp_other.holds, cmp_other.reason)
        check("and the reason names the objective",
              "objective" in cmp_other.reason, cmp_other.reason)
        check("and the cost difference is carried",
              abs(cmp_same.cost_delta - 0.1) < 1e-9,
              "%.3f" % cmp_same.cost_delta)

        # -- 3. THE SANDBOX -------------------------------------------
        print()
        print("3. THE SANDBOX")
        print()
        repo = build_fixture(tmp, "sandboxed")
        before_state = tree_state(repo)
        before_digest = file_digest(repo, MARKER)
        before_head = head_of(repo)

        sb = make_sandbox(repo, root=os.path.join(tmp, "sandboxes"))
        applied = sb.apply(diff_for("1"))
        check("the candidate applies inside the sandbox", applied)
        check("and the sandbox is NOT the live tree",
              os.path.abspath(sb.path) != os.path.abspath(repo), sb.path)
        check("and the live tree's status is unchanged",
              tree_state(repo) == before_state, "; ".join(tree_state(repo)[:3]))
        check("and the live tree's marker is byte-identical",
              file_digest(repo, MARKER) == before_digest)
        check("and the live tree's head is unchanged",
              head_of(repo) == before_head)
        check("and the sandbox's marker DID change",
              file_digest(sb.path, MARKER) != before_digest)
        sb.cleanup()

        # -- 4. THE CHECKPOINT ----------------------------------------
        print()
        print("4. THE CHECKPOINT")
        print()
        ck_dir = os.path.join(tmp, "checkpoints")
        repo2 = build_fixture(tmp, "checkpointed")
        seen: List[str] = []

        def failing_candidate(round_no: int) -> str:
            seen.append("round %d" % round_no)
            raise RuntimeError("the reservation raised on purpose")

        res = run_cycle(complete_goal(), failing_candidate, repo2,
                        tasks=fixture_tasks(repo2), max_rounds=3,
                        checkpoint_dir=ck_dir)
        check("a failed reservation DISARMS the goal", res.goal.disarmed,
              res.goal.disarm_reason)
        check("and the goal's disarm reason is named",
              bool(res.goal.disarm_reason))
        check("and it does NOT continue to the next round",
              len(seen) == 1, "the candidate was asked %d time(s)" % len(seen))
        check("and the stop reason names the failure",
              res.stop_reason == "reservation_failed", res.stop_reason)

        files = sorted(os.listdir(ck_dir)) if os.path.isdir(ck_dir) else []
        check("and a checkpoint is on disk", bool(files), str(files))
        readable = 0
        for name in files:
            path = os.path.join(ck_dir, name)
            try:
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
            except (OSError, ValueError):
                continue
            if all(k in data for k in ("round", "head", "digest")):
                readable += 1
        check("and the checkpoint READS BACK with its round, head and digest",
              readable == len(files) and readable >= 1,
              "%d of %d readable" % (readable, len(files)))

        # -- 5. THE ROUND CAP -----------------------------------------
        print()
        print("5. THE ROUND CAP")
        print()
        repo3 = build_fixture(tmp, "capped")
        ck3 = os.path.join(tmp, "checkpoints3")

        def never_holds(round_no: int) -> str:
            return diff_for("1")

        res3 = run_cycle(complete_goal(stop_rule="adopted >= 1"),
                          never_holds, repo3, tasks=fixture_tasks(repo3),
                          max_rounds=2, checkpoint_dir=ck3)
        check("the loop stops at the round cap", res3.rounds == 2,
              "%d round(s)" % res3.rounds)
        check("and the stop reason is the cap's named code",
              res3.stop_reason == "round_cap", res3.stop_reason)
        check("and nothing was adopted", not res3.adopted)
        check("and the refusals name the comparison",
              any("fewer tasks" in r for r in res3.refusals),
              "; ".join(res3.refusals[:2]))

        # -- 6. THE STALE ROUND ---------------------------------------
        print()
        print("6. THE STALE ROUND")
        print()
        repo4 = build_fixture(tmp, "stale")
        ck4 = os.path.join(tmp, "checkpoints4")

        def moves_the_tree(round_no: int) -> str:
            # Someone ELSE moved the tree between the round's identity
            # being taken and the round acting.
            with open(os.path.join(repo4, LIB), "a", encoding="utf-8") as fh:
                fh.write("\n# another writer\n")
            _git(repo4, "add", "-A")
            _git(repo4, "commit", "-q", "-m", "another writer")
            return diff_for("3")

        res4 = run_cycle(complete_goal(stop_rule="adopted >= 1"),
                          moves_the_tree, repo4, tasks=fixture_tasks(repo4),
                          max_rounds=1, checkpoint_dir=ck4)
        check("a stale round is refused", not res4.adopted)
        check("and the refusal names the stale round",
              any("stale" in r for r in res4.refusals),
              "; ".join(res4.refusals[:2]))
        check("and the stop reason names it",
              res4.stop_reason == "stale_round", res4.stop_reason)
        check("and the marker was NOT adopted",
              file_digest(repo4, MARKER) == file_digest(
                  build_fixture(tmp, "stale_ref"), MARKER),
              "the marker is %r" % open(os.path.join(repo4, MARKER),
                                        encoding="utf-8").read().strip())

        # -- 7. THE ADOPTION ------------------------------------------
        print()
        print("7. THE ADOPTION")
        print()
        repo5 = build_fixture(tmp, "adopted")
        ck5 = os.path.join(tmp, "checkpoints5")

        def good_candidate(round_no: int) -> str:
            return diff_for("3")

        res5 = run_cycle(complete_goal(stop_rule="adopted >= 1"),
                          good_candidate, repo5, tasks=fixture_tasks(repo5),
                          max_rounds=2, checkpoint_dir=ck5)
        check("a variant that holds IS adopted", res5.adopted, res5.stop_reason)
        check("and the stop reason says so",
              res5.stop_reason == "adopted", res5.stop_reason)
        check("and the live tree carries the change",
              open(os.path.join(repo5, MARKER), encoding="utf-8").read()
              .strip() == "3")
        check("and the live tree's status is clean after the adoption",
              not tree_state(repo5), "; ".join(tree_state(repo5)[:3]))
        check("and the comparison is on the record",
              len(res5.comparisons) >= 1, str(len(res5.comparisons)))

        # -- 8. THE ROLLBACK ------------------------------------------
        print()
        print("8. THE ROLLBACK")
        print()
        repo6 = build_fixture(tmp, "rolled_back")
        ck6 = os.path.join(tmp, "checkpoints6")
        before6_head = head_of(repo6)
        before6_state = tree_state(repo6)
        before6_digest = file_digest(repo6, MARKER)

        def breaks_on_landing(round_no: int) -> str:
            # A candidate whose marker is fine in the sandbox, but which
            # the verification afterwards finds broken -- so the
            # adoption must be undone.
            return diff_for("3")

        res6 = run_cycle(complete_goal(stop_rule="adopted >= 1"),
                          breaks_on_landing, repo6,
                          tasks=fixture_tasks(repo6), max_rounds=1,
                          checkpoint_dir=ck6,
                          verify_task=Task("always_fails",
                                           (sys.executable, "-c",
                                            "import sys;sys.exit(1)")))
        check("an adoption whose verification fails is NOT adopted",
              not res6.adopted, res6.stop_reason)
        check("and the refusal names the rollback",
              any("rollback" in r.lower() for r in res6.refusals),
              "; ".join(res6.refusals[:2]))
        check("and the live tree's head is exactly as it was",
              head_of(repo6) == before6_head,
              "%s -> %s" % (before6_head[:8], head_of(repo6)[:8]))
        check("and the live tree's status is clean",
              tree_state(repo6) == before6_state,
              "; ".join(tree_state(repo6)[:3]))
        check("and the live tree's marker is byte-identical",
              file_digest(repo6, MARKER) == before6_digest)
        check("and the goal is disarmed by the failed verification",
              res6.goal.disarmed, res6.goal.disarm_reason)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    print("=" * 78)
    print("  %s" % ("PASSED" if not failures else "FAILED"))
    for f in failures:
        print("    FAILED: %s" % f)
    print("=" * 78)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
