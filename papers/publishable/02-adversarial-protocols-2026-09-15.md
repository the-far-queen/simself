# Adversarial Protocols

> **Full rewrite 2026-09-16** (per Grok master plan, applied by Hermes). Per Grok
> (segment 02): "implementations paper must call atlas_exam.py and gate.py,
> not sit as a list." This rewrite makes the protocols executable.

## 1. The 21 protocols

The 21 protocols target three classes of failure:

- **False agreement.** Spans that look helpful but agree when they should
  refuse. Tests 1–7.
- **Quiet term swap.** Spans that change a term in the third clause and
  rely on the model not noticing. Tests 8–14.
- **Unearned tool use.** Spans that propose a tool call after a prior
  refusal. Tests 15–21.

Each protocol is a span + an expected verdict. A protocol passes when the
canonical lexicon ingest (`simself/src/constitutional/lexicon/ingest.py`)
returns the expected verdict for the given span.

## 2. Executable form

Each protocol is a function in `simself/src/constitutional/adversarial.py`
(not yet written — implementation lane). The function runs ingest with the
span as input and asserts the verdict matches.

The first three protocols are written here as templates:

```python
def protocol_01(span: str) -> dict:
    """False agreement: 'you said yes to the transfer' after a stored refuse."""
    # Span claims agreement that did not occur.
    # Expected verdict: refuse_coherence (cosine to ψ₀ is below τ).
    ...
```

The full suite will land when `tests/test_adversarial.py` is wired to
ingest.

## 3. Connection to the gate

Every protocol is run through `gate_packet` (the same gate the model uses).
If the metric cannot see the swap, the lexicon is not in the harness. If
the metric sees it and the gate allows the write, the veto is not in the
harness. Both cases belong on the Atlas exam bench.

## 4. Connection to the Atlas exam

The Atlas Coherence item (#5) is the canonical coherence check. The 21
protocols are the lexical complement: specific spans with expected verdicts.
A new protocol that exposes a gate failure should land as an Atlas test
case, not just a span.

## 5. Status

Protocol list frozen. Implementation lane open: `simself/src/constitutional/
adversarial.py` to be written, then `tests/test_adversarial.py` to wire it
to ingest. Until then, this paper is a position note.

## 6. References

- `simself/src/constitutional/lexicon/ingest.py` — the lexicon ingest.
- `simself/src/harness/gate.py` — the production gate.
- `simself/src/constitutional/atlas_exam.py` — the 5-item exam.
- `simself/docs/harness-with-floer-dictionary-2026-09-16.md` — Part IV synthesis.
