---
name: simself-gate
description: >-
  Use when the user wants to gate a model call or asset commit through the M0 governor.
  Triggers: "gate", "veto", "1-bit veto", "commit_asset", "refuse", "permit".
---

# SimSelf Gate — the 1-bit veto

The gate is the load-bearing refusal mechanism. Without it, the kernel is just an LLM with bookkeeping. The gate says: this thing may proceed, or it may not. That's it.

## Two predicates

The same predicates exist in three forms:

1. **kernel**: `fieldcore/src/tiniest-core/tiniest_core.py:M0_Governor`
2. **production**: `src/harness/gate.py:gate_packet`
3. **lexicon**: `src/constitutional/lexicon/ingest.py`

All three return `(allow: bool, reason: str)`. **Reasons are load-bearing** — they travel with the refusal and are auditable.

## When to call

Call the gate when:
- An asset (image, text, code, voice) is about to be committed to a public repo
- A model call is about to happen (or about to skip happening)
- A lexicon unit is being ingested
- A constitution axis is being changed

Skip the gate when:
- Reading from ψ₀ (read-only)
- Running the atlas exam (it IS the gate)
- Operating inside the kernel (the kernel IS the gate)

## Surface

```python
from src.harness.gate import gate_packet, gated_call

# Direct
allow, reason = gate_packet(packet)         # tuple-style check

# Wrap a callable
result = gated_call(do_thing, packet)       # runs only if gate says yes
# → returns result OR raises GateRefused(reason)

# Through the constitutional layer
from src.constitutional.lexicon.ingest import ingest
decision = ingest(text)                     # admit / commit / refuse
```

## Reason codes

Common reasons (not exhaustive):

- `no_ground` — ψ₀ not installed
- `drift_exceeded` — ‖ψ - ψ₀‖ > threshold
- `mode_locked` — M0 won't allow M1 in current mode
- `commit_forbidden` — `commit_asset="forbid"` on the sheet
- `forbidden_motif:<term>` — asset text matched a banned term
- `banned_term:<term>` — lyric/voice check failed
- `no_source_id` — film/track/mechanic has no pd source
- `royalty_mode_invalid:<mode>` — non-pd source for music/games
- `ground_touch_not_forbidden` — still/3d/comic touched ground
- `a11y_contrast_too_low` — image sheet below WCAG min
- `gate_refused:<inner>` — nested gate refused, fail-upwards

## Refusal handling

Refusals are NOT errors. They are **first-class results**. Catch `GateRefused` and act on the reason — don't retry blindly.

```python
try:
    result = gated_call(some_op, packet)
except GateRefused as r:
    log(f"refused: {r.reason}")
    return Fallback(r.reason)
```

## See also

- `simself-identity` — the SimSelf class
- `simself-constitution` — the axes
- `fieldcore-tiny-core` — the kernel math