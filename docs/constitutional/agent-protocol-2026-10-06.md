# CLAUDE.md / Agent protocol — simself

**source:** verbatim adoption of poteto/noodle/CLAUDE.md (MIT)
**date:** 2026-10-06
**reason:** lauren tan's protocol rules are the canonical 2026 agent-protocol rules; simself adopts them unchanged.

---

## Brain

The `vault/10-minimax/` directory is persistent memory across sessions.

- **Read first.** Read vault files relevant to your task before acting.
- **Write** after mistakes, corrections, or notable codebase learnings.
- **Structure:** One topic per file. Directories with index entries — no inlined content.
- **Maintain:** Delete outdated notes. Clean completed/abandoned plans.

## Workflow

- **User ordering:** Follow bullet/numbered list order. Don't reorder silently.
- **Isolation:** Multiple sessions run concurrently — use `git worktree` and atomic commits.

## Building

- **Build:** verify with `python -m pytest` after edits.
- **Check:** all F1..F5 / M1..M5 / G1..G5 / R1..R5 / W1..W5 gate tests must pass.

## Coding

- **Error messages:** Describe failure state ("session not found"), not expectations ("session must exist").
- **Cross-platform** (macOS/Windows/Linux): No bash 4+ features. Prefer POSIX shell or Python.
- **No backward compatibility** by default. No `omitempty` shims, no legacy fallbacks, no dual-path support. Only add compat when explicitly requested.
