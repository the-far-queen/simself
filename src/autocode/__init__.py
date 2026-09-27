"""
autocode/ — the self-coding surface of SimSelf.

The agent that wrote this repo also extends SimSelf by calling itself.
A MiniMax API model receives a structured prompt (see self_prompt.py)
and returns a unified-diff patch. The patch is parsed, applied
atomically, and verified by the test surface before commit.

Public API:
    from simself.src.autocode import run_loop, call_minimax, self_prompt

    # single API call
    response = call_minimax.complete(prompt="...")

    # build a self-prompt from current repo state
    sp = self_prompt.build(goal="...", constraints=[...], repo_root=".")
    response = call_minimax.complete(prompt=sp.render())

    # full loop: snapshot → call → patch → test → commit
    run_loop.run(goal="...", constraints=[...], max_iterations=3)
"""

__version__ = "0.1.0"
__all__ = ["call_minimax", "self_prompt", "apply_patch", "run_loop"]