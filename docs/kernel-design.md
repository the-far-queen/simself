# Kernel architecture — design intent (2026-09-05)

**Bobby's core insight, captured:**

The kernel of the core is **not** the geometric / sheaf / harmonic framing. The geometry is irrelevant to whether the system works. What matters:

## Deterministic wrapper solves key issues simply

- **Refusal as 1-bit**: cheap, efficient, refusal is first-class reply. No need for elaborate gating — a single bit veto.
- **4-bit fails upward**: when a cheap refusal/checks pass, escalate to deeper stalks. Don't run expensive computation if cheap check already vetoed.
- **Only computes if needed**: tokenization is wasteful. Algebraic / structural representations when possible. Compute the answer to the deeper issue, don't pattern-match to garbage.

## Training data is polluted with noise

- Distillation: 5x distilled version of training data, garbage removed.
- SNR / MMM as filter metrics: higher speed, same efficacy, lower size cost.

## MoE on steroids: dedicated reasoner

- Most LLMs lack a dedicated reasoning module. Reasoning is emergent, not engineered.
- Build a dedicated reasoner pathway that runs when the regular path needs it.
- Not the same as chain-of-thought (which is just longer token output) — actual structural reasoning.

## Many more (Bobby listed more, TBD capture)

- This is the first batch. Expect follow-up design directives.

## Implications

- The kernel can be a thin Rust/Python shim that decides cheap refusal or expensive path
- No need for elaborate sheaf/gluing for the *cheap* refusal path
- The expensive path (full sheaf, governor, projection) runs only when needed
- Geometry is still useful at the deep level but the kernel entry/exit is just a refusal bit

## What this means for code already written**
- `fieldcore_unified.py` M0Governor already does restricted-term check + role check — that's the cheap path
- The 5 gate types (structural/semantic/invariant/authority/projection) in MTE — that's the deep path
- The architecture matches. Add: dedicated reasoner module + 5x distilled data path.

---
*Captured 2026-09-05 in conversation. Multiple design directives expected.*