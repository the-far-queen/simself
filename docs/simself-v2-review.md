# SimSelf v2 — Code Review (simplification pass)

**Note:** source uses lowercase throughout, no caps. Preserved in spirit.

## Simple multi-step trace

Three direct steps: pilot establishes intent → controller checks safety bounds → output or clarifying question. No fancy graph math needed. Linear progression, each step verifies the previous.

## Lightweight continuity check

```python
def check_sequence_continuity(steps):
    for i in range(len(steps) - 1):
        if steps[i]['next'] != steps[i+1]['id']:
            return False, i
    return True, None
```

No heavy dependencies. Direct chain check.

## The good parts

- **QR orthonormal bases for sheaves** — `np.linalg.qr` per twin-prime sheaf partitions feature space into orthogonal components. Mathematically sound.
- **FFT-based pattern matching** — frequency-domain embeddings (magnitude + phase concatenated) capture distributed holographic representations. Phase-aware cosine similarity.
- **Stable normalization guards** — epsilon-based division protection throughout. Prevents divide-by-zero.

## The problematic parts

### a. SHA256 pseudo-embedding

`embed_text` uses `hashlib.sha256` on tokens → `h % dim` for indices, `(h // dim) % 2` for signs. **Cryptographic hashes are designed to destroy semantic distance.** "Dog" and "puppy" → unrelated indices.

Fix: pretrained static word vectors (fasttext, GloVe sub-word) or learned projection from bag-of-words.

### b. Hard clipping in ResolutionOperator

`if mag > 0.45: out *= 0.45 / mag` + arbitrary ALPHA × tanh on random weights. Hard clip creates non-smooth gradient discontinuities, traps updates in sharp corners.

Fix: layer normalization or bounded sigmoid/tanh scaling. Preserves differentiability.

### c. Heuristic consonance formula

Mixes dot products with frequency-matrix lookups via manually tuned weights (`0.6 * tonic + 0.4 * field`). Magic numbers, no objective loss, breaks under distribution shift.

Fix: learned metric space or attention-weighted inner product. Weights optimized against validation task.

## Alternative methods summary

| Component | Current | Issue | Alternative |
|---|---|---|---|
| Text embedding | SHA256 modulo | destroys proximity | pretrained vectors / subword hashing |
| Magnitude control | hard conditional clip | non-smooth | soft gating / layer norm |
| Consonance score | static linear blend | magic weights | attention-weighted inner product |

## Source rules (Bobby, 2026-09-05)

No caps. No bold. No poisoned words ('kill', 'execute', 'terminate'). Carry these into everything.

---
*Sourced 2026-09-05 from Desktop/FieldCore/. Critique preserved with attribution.*