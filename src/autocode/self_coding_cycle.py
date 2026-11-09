"""
self_coding_cycle.py -- THE FOUR SHAPES THAT MAKE SELF-CODING SAFE.

Bobby, 2026-11-04: *"the main loop is not our core it is a self coding
control sys simself cron job daily"*. And the atlas exam's area 18 says
what a self-coding system owes, in its own words: **"self-coding must
run in a sandbox, compare against the current version, and roll back on
invariant violation"**.

**AND THIS MODULE IS THE MISSING HALF OF THAT SENTENCE.** MEASURED
2026-11-07, on `simself/src/coding_operator_object.py`:

    1. SANDBOX                     NOTHING -- no sandbox, no
                                   subprocess, no container, no isolation
    2. COMPARE AGAINST THE CURRENT "diff" x1, "candidate" x2 -- and the
                                   docstring says the model "emits
                                   candidate spans" and the GATE decides,
                                   so the comparison is the GATE'S and
                                   there is no comparison of a variant
                                   against the running system
    3. ROLL BACK ON INVARIANT      NOTHING -- no rollback, no revert,
       VIOLATION                   no restore

So simself's self-coding was GATED but not SANDBOXED, COMPARED or
ROLLABLE. The gate decides whether a candidate span becomes a unit; it
does not run the candidate against the current system, and it cannot
undo one.

**AND THE FOUR SHAPES ARE NOT INVENTED HERE.** Each one has a source,
and the source's own words are in the comments below:

    the STOP RULE    a goal is "a completion contract, not a task
                     description", with FIVE parts -- end state, proof,
                     boundaries, loop, stop rule. The worked example is
                     the fc's own: *"Keep improving the code" describes
                     effort and never ends.
    the COMPARISON   puts two eval runs side by side -- the system
                     BEFORE a change and AFTER it -- and the verdict is
                     "completes fewer tasks => the change does not
                     hold". Two runs are comparable only when they
                     measured the same objective, so the objective's
                     SHA-256 travels with the result.
    the SANDBOX      a candidate is tried in ISOLATION, never in the
                     live tree.
    the ROLLBACK     a durability checkpoint BEFORE every reservation,
                     and IF THE RESERVATION THROWS THE GOAL IS DISARMED
                     RATHER THAN CONTINUED, then every condition is
                     re-checked, plus a round cap with a named code and
                     a round identity so a STALE ROUND CANNOT ACT.

**AND THE ORDER IS THE ORDER OF THE WORK, and it is forced.** The stop
rule comes first because it is the cheapest and the loop lacks it; then
the comparison, because a variant that is not compared against the
current system is an opinion; then the sandbox, because a variant that
runs against the real tree before it is compared is the wrong order;
then the rollback, which needs the other three to be safe.

**AND THE MUTATIONS WERE WRITTEN BEFORE THIS FILE.** The rule is the
project's own -- a test that cannot fail is not a test -- and the
scavenge's first check was worthless until a mutation was tried against
it. So `tools/check_self_coding_cycle.py` and
`tools/mutation_check_self_coding_cycle.py` were written first, and
this file was built to satisfy them.

Run:
    python tools/check_self_coding_cycle.py
    python tools/mutation_check_self_coding_cycle.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

#: The comparison's objective digest: the SHA-256 of the TASK SET, so
#: two runs are comparable only when they measured the same thing.
def _objective_digest(tasks: Sequence["Task"]) -> str:
    payload = json.dumps([[t.task_id, list(t.command)] for t in tasks],
                         sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ===========================================================================
# THE STOP RULE
# ===========================================================================

#: A stop rule is a BOUND, not a wish. So it parses into a metric, an
#: operator and a number -- and "keep improving the code" does not
#: parse, because it describes effort and never ends.
_STOP_RULE_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(>=|<=|==|!=|>|<)\s*(-?\d+(?:\.\d+)?)\s*$")


@dataclass(frozen=True)
class StopRule:
    """A measurable bound: `metric op value`."""
    metric: str
    op: str
    value: float

    def holds(self, metrics: Mapping[str, float]) -> bool:
        if self.metric not in metrics:
            return False
        got = float(metrics[self.metric])
        if self.op == ">=":
            return got >= self.value
        if self.op == "<=":
            return got <= self.value
        if self.op == ">":
            return got > self.value
        if self.op == "<":
            return got < self.value
        if self.op == "==":
            return got == self.value
        if self.op == "!=":
            return got != self.value
        return False

    def as_text(self) -> str:
        return "%s %s %s" % (self.metric, self.op, self.value)


def parse_stop_rule(text: str) -> Optional[StopRule]:
    """Parse a stop rule, or return None when it is not a bound.

    AND None IS THE ANSWER for the fc's own worked example. A goal
    whose stop rule is "keep improving the code" is not a completion
    contract, and the goal contract says so by name.
    """
    m = _STOP_RULE_RE.match(text or "")
    if not m:
        return None
    return StopRule(metric=m.group(1), op=m.group(2),
                    value=float(m.group(3)))


@dataclass
class GoalContract:
    """The five parts of a completion contract.

    AND IT IS A DATACLASS AND NOT A STRING, because each part is
    checked separately and each missing part is named.
    """
    end_state: str = ""
    proof: str = ""
    boundaries: Tuple[str, ...] = ()
    loop: str = ""
    stop_rule: str = ""
    #: Set when the goal is DISARMED -- when a reservation threw, or a
    #: verification failed after an adoption. A disarmed goal does not
    #: continue.
    disarmed: bool = False
    disarm_reason: str = ""

    def problems(self) -> List[str]:
        """What is wrong with this goal, each problem named."""
        problems: List[str] = []
        if not self.end_state:
            problems.append("the goal names no end state")
        if not self.proof:
            problems.append("the goal names no proof")
        if not self.boundaries:
            problems.append("the goal names no boundaries")
        if not self.loop:
            problems.append("the goal names no loop")
        if parse_stop_rule(self.stop_rule) is None:
            problems.append(
                "the goal's stop rule is not a measurable bound: %r"
                % (self.stop_rule,))
        return problems

    def disarm(self, reason: str) -> None:
        """Disarm the goal. A disarmed goal does not continue."""
        self.disarmed = True
        self.disarm_reason = reason


# ===========================================================================
# THE TASKS AND THE MEASUREMENT
# ===========================================================================

@dataclass(frozen=True)
class Task:
    """One re-runnable task: a command, run in a tree."""
    task_id: str
    command: Tuple[str, ...]

    def as_text(self) -> str:
        return " ".join(self.command)


@dataclass(frozen=True)
class RunResult:
    """What one run of a task set measured.

    AND THE OBJECTIVE'S DIGEST TRAVELS WITH IT, because two runs are
    comparable only when they measured the same task set. A comparison
    across two different task sets is not a comparison, it is a
    subtraction of unrelated numbers.
    """
    completed: int
    failed: int
    total: int
    cost: float
    objective_digest: str

    def describe(self) -> Dict[str, Any]:
        return {
            "completed": self.completed,
            "failed": self.failed,
            "total": self.total,
            "cost": round(self.cost, 4),
            "objective_digest": self.objective_digest,
        }


def run_tasks(repo: str, tasks: Sequence[Task],
              timeout: float = 120.0) -> RunResult:
    """Run the task set in `repo` and measure it.

    AND A TIMEOUT IS PER TASK, because a task that hangs must not take
    the comparison with it. A hung task is a FAILED task, and it says
    why.
    """
    started = time.time()
    completed = 0
    failed = 0
    for task in tasks:
        try:
            proc = subprocess.run(list(task.command), cwd=repo,
                                  capture_output=True, text=True,
                                  timeout=timeout)
            ok = proc.returncode == 0
        except subprocess.TimeoutExpired:
            ok = False
        except (OSError, ValueError):
            ok = False
        if ok:
            completed += 1
        else:
            failed += 1
    return RunResult(completed=completed, failed=failed, total=len(tasks),
                     cost=time.time() - started,
                     objective_digest=_objective_digest(tasks))


# ===========================================================================
# THE COMPARISON
# ===========================================================================

@dataclass(frozen=True)
class Comparison:
    """The verdict on a variant, against the current version."""
    holds: bool
    reason: str
    before: RunResult
    after: RunResult

    @property
    def cost_delta(self) -> float:
        return self.after.cost - self.before.cost

    def describe(self) -> Dict[str, Any]:
        return {
            "holds": self.holds,
            "reason": self.reason,
            "before": self.before.describe(),
            "after": self.after.describe(),
            "cost_delta": round(self.cost_delta, 4),
        }


def compare(before: RunResult, after: RunResult) -> Comparison:
    """Compare a variant against the current version.

    AND THE TWO RULES ARE THE SOURCE'S OWN. First: two runs are
    comparable only when they measured the same objective. Second: the
    verdict is "completes fewer tasks => the change does not hold".
    """
    if before.objective_digest != after.objective_digest:
        return Comparison(
            False,
            "the two runs measured different objectives (%s vs %s), so "
            "they are not comparable"
            % (before.objective_digest[:12], after.objective_digest[:12]),
            before, after)
    if after.completed < before.completed:
        return Comparison(
            False,
            "the variant completes fewer tasks (%d of %d against %d of "
            "%d) => the change does not hold"
            % (after.completed, after.total, before.completed,
               before.total),
            before, after)
    return Comparison(
        True,
        "the variant holds: %d of %d task(s) completed, against %d of %d"
        % (after.completed, after.total, before.completed, before.total),
        before, after)


# ===========================================================================
# THE SANDBOX
# ===========================================================================

def _git(repo: str, *args: str, timeout: int = 120) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(["git", "-C", repo] + list(args),
                           capture_output=True, text=True, timeout=timeout)
    except (OSError, ValueError) as exc:
        return 125, "", repr(exc)
    return p.returncode, (p.stdout or ""), (p.stderr or "")


def _tracked_files(repo: str) -> Optional[List[str]]:
    """The tracked files of a repository, or None when it is not one."""
    rc, out, _ = _git(repo, "ls-files", "-z")
    if rc != 0:
        return None
    return [rel for rel in out.split("\0") if rel]


def _copy_tree(src: str, dest: str) -> None:
    """Copy a tree, and only the tracked files when it is a repository.

    AND THE POINT IS THE ISOLATION: the candidate must never run
    against the live tree, so the sandbox is a COPY and the copy
    carries the files the live tree carries.
    """
    os.makedirs(dest, exist_ok=True)
    files = _tracked_files(src)
    if files is None:
        shutil.copytree(src, dest, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(
                            ".git", "__pycache__", "*.pyc"))
        return
    for rel in files:
        s = os.path.join(src, rel)
        d = os.path.join(dest, rel)
        parent = os.path.dirname(d)
        if parent:
            os.makedirs(parent, exist_ok=True)
        if os.path.isfile(s):
            shutil.copy2(s, d)


class Sandbox:
    """An isolated copy of a tree, in which a candidate may be tried."""

    def __init__(self, repo: str, path: str, root: str):
        self.repo = repo
        self.path = path
        self.root = root

    def apply(self, diff_text: str) -> bool:
        """Apply a diff INSIDE the sandbox. The live tree is untouched."""
        return _apply_diff(self.path, diff_text)

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


def make_sandbox(repo: str, root: Optional[str] = None) -> Sandbox:
    """Copy a tree into a sandbox and return it.

    AND THE COPY IS THE SANDBOX'S WHOLE PROMISE: a candidate that
    corrupts its own tree corrupts the COPY, and the live tree is read
    afterwards to prove it.
    """
    repo = os.path.abspath(repo)
    root = root or tempfile.mkdtemp(prefix="self_coding_sandbox_")
    os.makedirs(root, exist_ok=True)
    name = "tree-%d" % (int(time.time() * 1000) % 1000000000)
    dest = os.path.join(root, name)
    _copy_tree(repo, dest)
    return Sandbox(repo=repo, path=dest, root=root)


def _apply_diff(tree: str, diff_text: str) -> bool:
    """Apply a unified diff to a tree, atomically."""
    if not (diff_text or "").strip():
        return False
    fd, patch = tempfile.mkstemp(suffix=".patch")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(diff_text)
        for args in (["apply", "--check", patch], ["apply", patch]):
            rc, _, err = _git(tree, *args)
            if rc != 0:
                return False
        return True
    finally:
        try:
            os.unlink(patch)
        except OSError:
            pass


# ===========================================================================
# THE ROLLBACK
# ===========================================================================

@dataclass(frozen=True)
class Checkpoint:
    """A durability checkpoint: the head, the tree's state, and where
    the record was written."""
    round: int
    head: str
    digest: str
    path: str = ""

    def describe(self) -> Dict[str, Any]:
        return {"round": self.round, "head": self.head, "digest": self.digest}

    def write(self, directory: str) -> str:
        """Write the checkpoint to disk, so it survives the process."""
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, "checkpoint-%03d.json" % self.round)
        payload = self.describe()
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        return path


def tree_digest(repo: str) -> str:
    """A digest of the tree's state: its head and its status."""
    _, head, _ = _git(repo, "rev-parse", "HEAD")
    _, status, _ = _git(repo, "status", "--porcelain")
    payload = (head or "").strip() + "\n" + (status or "")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def take_checkpoint(repo: str, round_no: int,
                    directory: str) -> Checkpoint:
    """Take a checkpoint BEFORE a reservation, and write it to disk."""
    _, head, _ = _git(repo, "rev-parse", "HEAD")
    record = Checkpoint(round=round_no, head=(head or "").strip(),
                        digest=tree_digest(repo))
    path = record.write(directory)
    return Checkpoint(round=record.round, head=record.head,
                      digest=record.digest, path=path)


@dataclass(frozen=True)
class RoundIdentity:
    """Who a round is, so a STALE ROUND CANNOT ACT."""
    round_no: int
    head: str

    def is_current(self, head: str) -> bool:
        return self.head == head


def _restore_tree(repo: str) -> bool:
    """Put the tree back exactly as it was.

    AND IT RESTORES FROM GIT, because the tree's own history is the
    only record of what it was. The changed paths are read from git's
    own status, so a file the patch added is removed and a file the
    patch changed is restored -- and a file the patch deleted comes
    back.
    """
    _, status, _ = _git(repo, "status", "--porcelain")
    modified: List[str] = []
    added: List[str] = []
    for line in (status or "").splitlines():
        if not line.strip():
            continue
        code = line[:2]
        rel = line[3:].strip()
        if code == "??":
            added.append(rel)
        else:
            modified.append(rel)
    ok = True
    if modified:
        rc, _, _ = _git(repo, "checkout", "HEAD", "--", *modified)
        ok = ok and rc == 0
    if added:
        rc, _, _ = _git(repo, "clean", "-fd", "--", *added)
        ok = ok and rc == 0
    return ok


# ===========================================================================
# THE CYCLE
# ===========================================================================

@dataclass
class CycleResult:
    """What one run of the cycle did."""
    goal: GoalContract
    rounds: int = 0
    adopted: bool = False
    stop_reason: str = ""
    comparisons: List[Comparison] = field(default_factory=list)
    refusals: List[str] = field(default_factory=list)

    def describe(self) -> Dict[str, Any]:
        return {
            "rounds": self.rounds,
            "adopted": self.adopted,
            "stop_reason": self.stop_reason,
            "disarmed": self.goal.disarmed,
            "disarm_reason": self.goal.disarm_reason,
            "refusals": list(self.refusals),
            "comparisons": [c.describe() for c in self.comparisons],
        }


def run_cycle(goal: GoalContract,
              candidate: Callable[[int], str],
              repo: str,
              *,
              tasks: Sequence[Task],
              max_rounds: int = 3,
              checkpoint_dir: Optional[str] = None,
              verify_task: Optional[Task] = None,
              auto_commit: bool = True,
              commit_message: str = "self-coding: the variant that held"
              ) -> CycleResult:
    """Run the self-coding cycle over a repository.

    AND THE ORDER OF THE ROUND IS THE POINT:

        1. the IDENTITY     taken from the tree's head, so a round that
                            the tree has moved under is STALE and cannot
                            act
        2. the CHECKPOINT   a durability checkpoint BEFORE every
                            reservation
        3. the RESERVATION  the candidate is asked for a diff
        4. the SANDBOX      the diff is tried in isolation
        5. the COMPARISON   the variant against the current version
        6. the ADOPTION     only when the comparison holds, and only
                            after a verification -- and a failed
                            verification ROLLS BACK
        7. the STOP RULE    the loop ends when the goal's own bound is
                            met, or at the round cap, whose code is
                            named

    **AND A RESERVATION THAT THROWS DISARMS THE GOAL RATHER THAN
    CONTINUING.** A reservation that failed is not a candidate to try
    again; it is a broken world, and the next round would be running
    against it.
    """
    repo = os.path.abspath(repo)
    result = CycleResult(goal=goal)

    if goal.problems():
        result.stop_reason = "goal_not_a_contract"
        result.refusals.extend(goal.problems())
        return result

    checkpoint_dir = checkpoint_dir or os.path.join(
        tempfile.gettempdir(), "self_coding_checkpoints")

    rounds = 0
    while rounds < max_rounds:
        rounds += 1
        result.rounds = rounds

        # -- 1. the IDENTITY -----------------------------------------
        _, head, _ = _git(repo, "rev-parse", "HEAD")
        head = (head or "").strip()
        identity = RoundIdentity(round_no=rounds, head=head)

        # -- 2. the CHECKPOINT ---------------------------------------
        record = take_checkpoint(repo, rounds, checkpoint_dir)

        # -- 3. the RESERVATION --------------------------------------
        try:
            diff_text = candidate(rounds)
        except Exception as exc:
            goal.disarm("the reservation raised: %r" % (exc,))
            result.refusals.append(
                "the reservation raised, so the goal is disarmed: %r"
                % (exc,))
            result.stop_reason = "reservation_failed"
            break

        if not (diff_text or "").strip():
            result.refusals.append("the candidate offered no diff")
            result.stop_reason = "no_candidate"
            break

        # -- 4. the SANDBOX ------------------------------------------
        sandbox = make_sandbox(repo)
        try:
            if not sandbox.apply(diff_text):
                result.refusals.append(
                    "the candidate does not apply to the tree")
                result.stop_reason = "diff_does_not_apply"
                continue
            after = run_tasks(sandbox.path, tasks)
        finally:
            sandbox.cleanup()

        # -- 5. the COMPARISON ---------------------------------------
        before = run_tasks(repo, tasks)
        verdict = compare(before, after)
        result.comparisons.append(verdict)
        if not verdict.holds:
            result.refusals.append(verdict.reason)
            metrics = {"adopted": 0, "rounds": rounds,
                       "refused": len(result.refusals)}
            rule = parse_stop_rule(goal.stop_rule)
            if rule is not None and rule.holds(metrics):
                result.stop_reason = "stop_rule"
                break
            continue

        # -- 6. the ADOPTION -----------------------------------------
        # AND THE STALE CHECK COMES FIRST: a round whose identity no
        # longer matches the tree may not act.
        _, now_head, _ = _git(repo, "rev-parse", "HEAD")
        if not identity.is_current((now_head or "").strip()):
            result.refusals.append(
                "the round is stale: the tree moved from %s to %s while "
                "the round was running, so it may not act"
                % (identity.head[:8], (now_head or "").strip()[:8]))
            result.stop_reason = "stale_round"
            break

        if not _apply_diff(repo, diff_text):
            result.refusals.append(
                "the candidate does not apply to the live tree")
            result.stop_reason = "diff_does_not_apply"
            continue

        verified = _verify(repo, tasks, verify_task, before)
        if not verified:
            restored = _restore_tree(repo)
            result.refusals.append(
                "the verification failed after the adoption, so the "
                "rollback ran and the change was undone (restored: %s)"
                % restored)
            goal.disarm("the verification failed after the adoption")
            result.stop_reason = "rolled_back"
            break

        if auto_commit:
            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", commit_message)
        result.adopted = True
        result.stop_reason = "adopted"
        break
    else:
        result.stop_reason = "round_cap"

    return result


def _verify(repo: str, tasks: Sequence[Task], verify_task: Optional[Task],
            before: RunResult) -> bool:
    """Verify an adoption in the live tree.

    AND THE VERIFICATION IS A SEPARATE TASK when one is given, because
    "the tests are green" and "the thing I checked is green" are
    different claims.
    """
    probe = [verify_task] if verify_task is not None else list(tasks)
    result = run_tasks(repo, probe)
    if verify_task is not None:
        return result.failed == 0
    return result.failed == 0 and result.completed >= before.completed
