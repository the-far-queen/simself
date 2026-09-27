"""
run_loop.py — the autocode loop: snapshot → call → patch → test → commit.

The full pipeline:

    1. Build a SelfPrompt from the current repo state.
    2. Call the MiniMax API with that prompt.
    3. If the response is NO_DIFF, stop.
    4. Otherwise, hand the diff to apply_patch.py.
    5. If apply_and_test() succeeds: stop (commit landed).
    6. If it fails: roll back, optionally retry with the error in the next prompt.
    7. Repeat up to max_iterations.

Usage:
    python -m src.autocode.run_loop --goal "..." [--constraint X] [--max-iterations 3]

Each iteration is logged to stdout. The agent can resume from any prior
state by passing --resume <iteration_number>.

This loop is also the integration point: a human agent (Hermes / MiniMax-M3)
can run the same goal in chat, see the diff the model produced, and
approve / discard before commit. The difference is just whether the loop
calls itself or the human calls back.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

# Local imports — assume run as module: python -m src.autocode.run_loop
from . import call_minimax, self_prompt, apply_patch


def run(
    goal: str,
    *,
    constraints: Optional[List[str]] = None,
    repo_root: Optional[str] = None,
    max_iterations: int = 3,
    model: Optional[str] = None,
    auto_commit: bool = True,
    include_test_surface: bool = True,
    verbose: bool = True,
) -> dict:
    """Run the autocode loop until success, max_iterations, or NO_DIFF.

    Returns a dict describing the final state:
        {
          "ok": bool,
          "iterations": int,
          "final_sha": Optional[str],
          "history": [ {iter, ok, message, ...}, ... ],
          "stop_reason": "committed" | "no_diff" | "max_iterations" | "failed",
        }
    """
    history = []
    last_diff: Optional[str] = None
    last_error: Optional[str] = None

    for it in range(1, max_iterations + 1):
        if verbose:
            sys.stderr.write(f"\n[autocode] iteration {it}/{max_iterations}\n")

        # 1. Build prompt (with prior error feedback if any).
        iter_constraints = list(constraints or [])
        if last_error:
            iter_constraints.append(
                f"Previous attempt failed with error: {last_error!r}. "
                "Do not repeat the same mistake."
            )
        sp = self_prompt.build(
            goal=goal,
            constraints=iter_constraints,
            repo_root=repo_root,
            include_test_surface=include_test_surface,
        )

        # 2. Call the API.
        try:
            resp = call_minimax.complete(prompt=sp.render(), model=model)
        except call_minimax.MiniMaxError as e:
            err = f"API error: {e}"
            history.append({"iter": it, "ok": False, "message": err})
            if verbose:
                sys.stderr.write(f"[autocode] {err}\n")
            return {
                "ok": False, "iterations": it, "final_sha": None,
                "history": history, "stop_reason": "failed",
            }

        if verbose:
            sys.stderr.write(
                f"[autocode] API reply: model={resp.model} "
                f"tokens={resp.total_tokens} ({resp.prompt_tokens}+{resp.completion_tokens}) "
                f"elapsed={resp.elapsed_seconds:.2f}s\n"
            )

        text = resp.text.strip()

        # 3. NO_DIFF sentinel.
        if text == "NO_DIFF":
            history.append({"iter": it, "ok": False, "message": "model returned NO_DIFF"})
            if verbose:
                sys.stderr.write("[autocode] model returned NO_DIFF — stopping\n")
            return {
                "ok": False, "iterations": it, "final_sha": None,
                "history": history, "stop_reason": "no_diff",
            }

        # 4. Apply + test.
        result = apply_patch.apply_and_test(
            text,
            repo_root=repo_root or os.getcwd(),
            commit_message=f"autocode: {goal[:60]}",
            auto_commit=auto_commit,
        )

        history.append({
            "iter": it,
            "ok": result.ok,
            "applied": result.applied,
            "tested": result.tested,
            "committed": result.committed,
            "files": result.files_touched,
            "commit_sha": result.commit_sha,
            "error": result.error,
        })

        if result.ok:
            if verbose:
                sys.stderr.write(
                    f"[autocode] OK — committed {result.commit_sha} "
                    f"({len(result.files_touched)} file(s))\n"
                )
            return {
                "ok": True,
                "iterations": it,
                "final_sha": result.commit_sha,
                "history": history,
                "stop_reason": "committed",
            }

        # Failure path: record error for next iteration, retry.
        last_error = result.error or "unknown patch failure"
        last_diff = text
        if verbose:
            sys.stderr.write(f"[autocode] FAIL: {last_error}\n")

    return {
        "ok": False,
        "iterations": max_iterations,
        "final_sha": None,
        "history": history,
        "stop_reason": "max_iterations",
    }


# --- CLI -------------------------------------------------------------------

def _cli():
    p = argparse.ArgumentParser(
        description="Run the autocode loop: prompt → call → patch → test → commit."
    )
    p.add_argument("--goal", required=True,
                   help="One-sentence description of the change to make.")
    p.add_argument("--constraint", action="append", default=[],
                   help="Add a constraint (can be passed multiple times).")
    p.add_argument("--repo-root", default=None,
                   help="Path to the simself repo (default: autodetect).")
    p.add_argument("--max-iterations", type=int, default=3,
                   help="Maximum loop iterations (default: 3).")
    p.add_argument("--model", default=None,
                   help="Override the MiniMax model (default: $MINIMAX_MODEL).")
    p.add_argument("--no-commit", action="store_true",
                   help="Apply + test only; never commit.")
    p.add_argument("--no-tests", action="store_true",
                   help="Skip the test surface (faster, but unsafe).")
    args = p.parse_args()

    result = run(
        goal=args.goal,
        constraints=args.constraint,
        repo_root=args.repo_root,
        max_iterations=args.max_iterations,
        model=args.model,
        auto_commit=not args.no_commit,
        include_test_surface=not args.no_tests,
    )

    print(f"\nstop_reason: {result['stop_reason']}")
    print(f"iterations:  {result['iterations']}")
    print(f"final_sha:   {result['final_sha']}")
    print(f"ok:          {result['ok']}")

    # History summary.
    print("\nhistory:")
    for h in result["history"]:
        msg = h.get("error") or ("committed " + (h.get("commit_sha") or "?"))
        print(f"  iter {h['iter']}: {msg}")

    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    _cli()