# MTE LLM Wrapper Safety

> **Full rewrite 2026-09-16** (per Grok master plan, applied by Hermes). Per Grok
> (segment 02): "Strong if the wrapper actually intercepts model I/O." This
> rewrite shows the wired wrapper.

## 1. The wrapper contract

The wrapper sits between every caller and the model. Prompts leave only as
typed packets. Replies return only as spans offered to ingest. Side doors
(Telegram, code execution) use the same wrapper.

Implementation: `simself/src/harness/gate.py:gated_call` is the single entry
point. It is imported by:

- `simself/src/coding_operator_object.py:CodingOperatorObject.propose_span`
- `simself/src/harness/telegram_bot.py:gate_inbound`
- `simself/src/harness/telegram_text_bot.py:gate_text`
- `simself/src/harness/tools.py:ToolRegistry.call`
- `simself/src/m1_m0_negotiation.py:negotiate`

If `gated_call` is unavailable, every caller refuses by default. The
wrapper cannot be silently bypassed.

## 2. The two inequalities

`gate_packet` (in `harness/gate.py`) applies the same norm + cosine
predicates as the kernel's `M0_Governor`. A packet is allowed only if both
inequalities pass. Reasons: `ok`, `refuse_norm`, `refuse_coherence`,
`refuse_zero`.

## 3. Telegram bot

The Telegram bot runs `gate_inbound(text, ψ₀, embed_fn)` before forwarding
to the model. Refused messages produce a deny record but no LLM call.
Allowed messages are forwarded to the model.

## 4. Tool calls

`ToolRegistry.call(name, payload, ψ₀, embed_fn)` runs `gated_call` first,
then dispatches to the registered tool. Refused payloads produce a deny
record and the tool is not invoked.

## 5. Failure mode: gate unavailable

If `gated_call` cannot be imported (e.g. broken install), every wrapper
raises or refuses by default. The harness cannot run without the gate.
This is the structural form of "no ungated execution."

## 6. Status

Wired 2026-09-16 per master plan Step 5 + Batch 1 K8. The wrapper is the
single source of truth for LLM-call paths. Adding a new caller requires
adding the `gated_call` wrap, not an inline check.

## 7. References

- `simself/src/harness/gate.py` — the gate.
- `fieldcore/src/tiniest-core/tiniest_core.py` — the kernel's M0_Governor.
- `simself/src/coding_operator_object.py` — model I/O surface.
- `simself/src/harness/telegram_bot.py` — Telegram gateway.
- `simself/src/harness/telegram_text_bot.py` — text-only Telegram gateway.
- `simself/src/harness/tools.py` — tool registry.
- `simself/src/m1_m0_negotiation.py` — M1 / M0 negotiation.
