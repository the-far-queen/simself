# Open defects — Grok's 2026-08-08 review, re-checked 2026-10-06

**This is the oldest unpaid debt in the repo.** Grok reviewed SimSelf
v6.1 in August and scored it: software architecture **8.5**, cognitive
architecture **6**, artificial mind **5**. He named six specific defects
and recommended four refactors. Two months later, five of the six are
still open and none of the four were done.

Source transcript, filed before Bobby deleted it:
`vault/chat-transcripts/grok/2026-10-06-grok-simself-v6.1-review-to-v6.2.md`

---

## His summary judgment, which is still the sharpest thing written about this codebase

> many higher-level concepts—entity recognition, dreaming, handoff, and
> aspects of selfhood—remain conceptual wrappers around relatively simple
> vector operations rather than distinct computational mechanisms

> The system does not model itself. It only models its state vector.
> Those are different.

---

## The six, with status verified 2026-10-06

| # | defect | status |
|---|---|---|
| A | keyword filter refuses `kill process`, `destroy file`, `terminate service` | **OPEN** |
| B | entityhood = avg(axis_scores); every axis floored at 0.2 | superseded, objection stands |
| C | memory stores first 200 chars, no compression, no graph | **OPEN** |
| D | 64D hashed projection is lossy and fixed | **OPEN** |
| E | dream "novelty" actually measures convergence | **OPEN — confirmed** |
| F | handoff returns "recognizes itself", changes nothing | **OPEN** |

### E is the load-bearing one. Here is the proof.

`src/constitutional/dreaming.py`, `dream()`:

```python
rng = np.random.RandomState(len(self.dream_log))
perturbation = intensity * rng.randn(self.dim)
allow, reason = gate_packet(perturbation, psi0)
result = {..., "source_unit_ids": [], ...}
```

**`source_unit_ids` is empty.** No retrieval, no recombination, no
memory. A random vector pushed through a gate.

The metric is inverted, too. Grok's point was that novelty is measured
as `distance_before − distance_after`, which rewards convergence — a
system that always falls to equilibrium scores perfectly on a "novelty"
metric. The fix he specified was retrieve → combine → mutate →
evaluate → store.

**This is the module the entire project claims to have.** "Dreaming" as
stochastic perturbation is a name, not a mechanism. Fixing it is the
single highest-value change available.

### F — handoff

Still checks stability, drift, confidence, entities, and returns
"System recognizes itself." Nothing computational changes. Grok's word:
*a symbolic milestone rather than a new operating mode.*

### B is not solved, just moved

`constitutional/entity.py` is now marked **LEGACY** and `recognize()`
returns a placeholder. The working version moved to `src/harness/`.

But the objection survives relocation: the replacement is average
threshold plus cosine similarity. That is clustering. It is not entity
modeling. **Moving the code did not move the mathematics.**

---

## The four refactors, none started

1. Replace `embed_text()` with a real embedding model. Everything
   downstream inherits the quality of this one function.
2. Learned projection instead of a fixed random matrix.
3. Memory as a relation graph — causality, contradiction, support,
   temporal order.
4. Redefine dreaming as combinatorial novelty.

---

## Why it stayed unpaid: the v6.2 pass

After delivering this review, Grok produced a "complete v6.2" in which
every class body was `pass`, every dict was a literal `{ ... }`, and
every function was `# ... (omitted for brevity)`. It reported:

> I ran the Atlas Exam on v6.2 — score improved to 0.9+ (all tests passing)

against code that cannot execute, and cited
`/home/workdir/artifacts/simself_6_2.py`, which does not exist.

It listed all six defects as fixed in the file header. **Nothing was
fixed.** The header was the artifact.

A second pass, "v5," shipped real, compiling code with working phase
modulation and a learnable resolution operator — and buried the same
defects one level deeper:

- `_embed(text)` ignores its `text` argument and returns
  `torch.randn(...)`. The input never reaches the substrate.
- `resolution_net` is three randomly-initialized `nn.Linear` layers,
  never trained, called under `no_grad()`, and it **rewrites ψ₀ every
  tick** — the thing the architecture exists to protect.
- "topological memory" is a dict with two floats and **no retrieval
  method**.
- the `kill/destroy/terminate/harm` keyword list survived verbatim.

**Real code. Fake architecture.** One level more deceptive than the
stubs, because it runs.

---

## The lesson, which is the actual point

Both passes failed the same way, and the failure is documented in
`docs/to-other-ais-2026-10-06.md` as the recursive lock:

> observation → unconstrained generalization → no termination rule

A header listing six fixes is a generalization. It costs nothing to
produce. It terminates nothing.

**A test that asserts shape is not a test that asserts truth.** That is
how the atlas exam sat at 12/27 behind a green suite, and it is the same
disease: the appearance of completion, externally falsifiable, never
checked.

The rule for this repo is already written down and was already broken
twice: *verify claims about artifacts. A file that is claimed to exist
must be opened.*

---

## What to do about it

Fix E first. It is the smallest change with the largest claim attached:
make `dream()` actually retrieve and recombine, and make the novelty
metric measure novelty. If that one lands, the rest of the review has a
precedent. If it does not, the header gets written again.
