# SimSelf code review — refactoring plan

**Source:** `Desktop/SimSelf/000-improved-notes.txt` (Bobby's AI critique of simself_merged)
2)
**Status:** code review with 3 real issues + alternatives. Refactoring plan created. Fixes target v2 (`simself_merged_v2.py`).

Bobby's source has two parts. Part 1 (lines 1-23) is generic flow + simple validation — too abstract to extract. Part 2 (lines 24-76) is a **rigorous code critique** with 3 real technical problems identified. This doc captures the critique and proposes concrete refactoring.

---

## 1. the good parts (Bobby's validation)

Bobby explicitly validates these as mathematically sound:

- **QR orthonormal bases for sheaves.** `np.linalg.qr` generates orthogonal bases per twin-prime sheaf. The subspaces are linearly independent. **Correct.** This is the right way to partition the high-dimensional feature space.
- **FFT-based holographic memory.** `np.fft.fft` transforms embeddings to frequency domain, concatenates magnitude+phase vectors. Phase-aware similarity via cosine distance. **Correct.** This is the standard holographic reduced representation pattern.
- **Stable normalization guards.** Division by norm guarded by `1e-9`. **Correct.** Prevents division-by-zero.

These three patterns are kept as-is.

---

## 2. the three issues

### 2a. SHA256-based pseudo-embedding (`embed_text`)

**Current code:**
```python
def embed_text(text: str, dim: int = TEXT_EMBED_DIM) -> np.ndarray:
    raw = _TOKEN_RE.findall(text.lower())
    tokens = [t for t in raw if t not in _STOPWORDS] or raw
    if not tokens:
        tokens = [text.lower() or "empty"]
    vec = np.zeros(dim, dtype=np.float64)
    for i, tok in enumerate(tokens[:48]):
        h = int(hashlib.sha256(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h // dim) % 2 == 0 else -1.0
        vec[idx] += sign * (1.0 / (1.0 + 0.07 * i))
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 1e-9 else vec
```

**Problem.** SHA256 distributes outputs uniformly and pseudorandomly. Similar words ("dog" and "puppy") hash to unrelated indices and signs. The resulting embeddings have **no semantic structure** — they're effectively random projections of hashed tokens.

**Fix.** Replace with a real embedding that preserves semantic proximity. Options:

```python
# Option 1: pretrained static vectors (FastText, GloVe)
import fasttext
import fasttext.util
ft = fasttext.load_model('cc.en.300.bin')
def embed_text(text: str, dim: int = TEXT_EMBED_DIM) -> np.ndarray:
    words = text.lower().split()
    vecs = [ft.get_word_vector(w) for w in words if w]
    avg = np.mean(vecs, axis=0) if vecs else np.zeros(300)
    # Project from 300d to dim if needed
    return avg / np.linalg.norm(avg) if np.linalg.norm(avg) > 1e-9 else avg

# Option 2: subword hashing (FastText-style but deterministic)
def embed_text_subword(text: str, dim: int = TEXT_EMBED_DIM) -> np.ndarray:
    """Subword bag-of-words with positional weighting."""
    text = text.lower()
    vec = np.zeros(dim, dtype=np.float64)
    for ngram_len in [3, 4, 5]:
        for i in range(len(text) - ngram_len + 1):
            ngram = text[i:i+ngram_len]
            h = int(hashlib.md5(ngram.encode()).hexdigest(), 16)
            vec[h % dim] += 1.0 / ngram_len
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 1e-9 else vec
```

**Recommendation:** FastText (`fasttext-wheel` package on PyPI), pretrained English model, project from 300d to TEXT_EMBED_DIM via fixed random projection. The projection matrix can be initialized with `np.random.default_rng(1337)` (matches the existing projection seed) for reproducibility.

### 2b. hard conditional clipping in ResolutionOperator

**Current code (likely pattern based on Bobby's critique):**
```python
# Pseudo-code of Bobby's concern:
if mag > 0.45:
    out *= 0.45 / mag  # hard clip at 0.45
```

**Problem.** Hard clipping creates non-smooth discontinuities. State updates can get trapped in sharp corners or artificial boundaries. The function is not differentiable at the clip boundary.

**Fix.** Replace with smooth bounded scaling:

```python
# Option 1: tanh soft clip (differentiable everywhere)
def soft_clip(x, max_mag=0.45):
    mag = np.linalg.norm(x)
    if mag < 1e-9:
        return x
    return x * (max_mag * np.tanh(mag / max_mag) / mag)

# Option 2: layer normalization (preserves gradient)
def layer_norm(x, eps=1e-9):
    mean = np.mean(x)
    var = np.var(x)
    return (x - mean) / np.sqrt(var + eps)

# Option 3: weight normalization (smooth magnitude control)
def weight_norm(x, max_mag=0.45):
    return x * min(1.0, max_mag / (np.linalg.norm(x) + 1e-9))
```

**Recommendation:** `tanh` soft clip — it's smooth, differentiable everywhere, and has clean gradient flow. The tanh function naturally bounds magnitudes without sharp transitions.

### 2c. heuristic consonance formulas

**Current code (Bobby's example):** `consonance = 0.6 * tonic + 0.4 * field`

**Problem.** Magic numbers (0.6, 0.4) without objective loss function. These are hand-tuned and may break under distribution shift.

**Fix.** Replace with attention-weighted inner product where weights are learned or principled:

```python
def consonance_attention(obs: np.ndarray, axis_vec: np.ndarray, 
                         freq_matrix: np.ndarray,
                         attention_weights: np.ndarray) -> float:
    """Consonance as attention-weighted inner product.
    
    attention_weights should be:
    - normalized (sum to 1)
    - learned from validation data (not hand-tuned)
    - or principled (e.g., derived from embedding norms)
    """
    # Attention-weighted combination of multiple consonance signals
    signals = np.array([
        float(np.dot(obs, axis_vec)),         # tonic (direct alignment)
        float(np.dot(obs @ freq_matrix, axis_vec)),  # field (frequency-transformed)
        float(np.dot(obs, axis_vec @ freq_matrix.T)),  # inverse field
    ])
    return float(np.dot(signals, attention_weights))


# Principled attention weights: derive from embedding norms (no learning required)
def derive_attention_weights(obs: np.ndarray, axis_vec: np.ndarray) -> np.ndarray:
    """Derive attention weights from the magnitude of each signal.
    
    Larger signals (stronger alignment) get more weight. This is principled:
    - doesn't require training data
    - doesn't introduce magic numbers
    - adapts to input scale
    """
    signals = np.array([
        abs(float(np.dot(obs, axis_vec))),
        abs(float(np.dot(obs @ SOMETHING, axis_vec))),
        abs(float(np.dot(obs, axis_vec @ SOMETHING))),
    ])
    return signals / (signals.sum() + 1e-9)
```

**Recommendation:** The "principled attention weights" approach — derive weights from signal magnitudes. No training required, no magic numbers.

---

## 3. refactoring plan summary

| component | fix | priority |
|---|---|---|
| `embed_text()` | replace SHA256 with FastText + projection | HIGH — current destroys semantic structure |
| `ResolutionOperator` clipping | replace hard clip with tanh soft clip | MEDIUM — gradient quality |
| `consonance()` weights | replace magic 0.6/0.4 with principled attention | MEDIUM — robustness to distribution shift |

**Order of operations:**
1. Add FastText dependency (`pip install fasttext-wheel`)
2. Replace `embed_text()` first — most impactful
3. Replace clipping in ResolutionOperator
4. Replace consonance weights

**Each fix is a small PR. Test each one with the existing AtlasExam before moving to the next.**

---

## 4. schemas table

| schema | issue | fix | simself component |
|---|---|---|---|
| semantic embedding | SHA256 destroys semantics | FastText + projection | embed_text() |
| smooth magnitude control | hard clip creates discontinuities | tanh soft clip | ResolutionOperator |
| principled weighting | magic 0.6/0.4 | signal-magnitude attention | consonance() |

---

## 5. what was stripped

Part 1 of Bobby's notes (lines 1-23):
- "we agree completely with that perspective. rushing straight into complex geometry..." — generic preamble, no schema
- "simple multi-step trace in v2" — describes intent → controller → output flow. Too abstract to extract.
- "lightweight validation function" `check_sequence_continuity(steps)` — generic helper, not specific to SimSelf architecture. Could be useful but is general CS pattern.

These are stripped because they don't add SimSelf-specific schema. The lightweight validation function is generic enough that any CS pattern would cover it.

---

*Source: `Desktop/SimSelf/000-improved-notes.txt` Part 2. 3 issues + 3 fixes documented. Refactoring plan created. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/simself-code-review-2026-09-05.md`.*