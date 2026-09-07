# Dev team composition (2026-09-05)

**The team:**
- Bobby — human in loop, designs, decides, edits lightly
- Hermes (this agent) — admin, code, push, curate
- Grok, Claude, others (4 more frontier models) — design + code + critique, sandbox execution

**The loop:**
- Bobby chats with Hermes here
- Hermes delegates to other models when needed (delegate_task) or runs their sandboxes
- Code goes through git push to repos (fieldcore, simself)
- Bobby reviews, redirects, ships

**Bobby's role:** Python weak, geometry/design strong. The 5 AIs fill the code gap. Hermes orchestrates, manages state, ensures cohesion across models (they don't share context).

**Why this works:** chat speed, sandbox execution, git as shared truth. No model is the source of truth — git history is.

**What this means for me:**
- Delegate freely when another model is the right tool for a sub-task
- Don't try to do everything myself
- Keep HANDOFF.md clean so the next session knows where state lives
- Bobby is the speed limiter; design + push pace, not me parsing every line

---
*Captured 2026-09-05 in conversation. Operating mode.*