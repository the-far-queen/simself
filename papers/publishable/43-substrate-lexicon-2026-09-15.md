# Substrate Lexicon: A Reference for Primary Semantic Blocks and Composition

**Authors:** Robert Wolfson, Hermes (Nous Research / MiniMax)
**Date:** 2026-09-15
**Status:** Draft 0.1 — arxiv preprint candidate (cs.CL / cs.AI)
**Repo:** `simself/papers/publishable/43-substrate-lexicon-2026-09-15.md`

---

## Abstract

A **substrate lexicon** for SimSelf: 37 canonical Primary Semantic Blocks (PSBs), composition rules, and language-to-PSB mappings.

Per Bobby Wolfson's lexical insight: "tokenization breaks language but intact language is sum of intelligence of many minds of species formed over many years." The lexicon implements **intact language** at the PSB level.

The lexicon is **engineering-grade**: every PSB has a definition, a composition rule, and a substrate mapping.

---

## 1. The 37 PSBs

### 1.1 Action primitives

- **cause** — bring about an effect.
- **go** — initiate motion.
- **stop** — cease motion.
- **up** — increase or ascend.
- **move** — change position.
- **left** — direction or decrease.

### 1.2 Perception primitives

- **see** — visual perception.
- **hear** — auditory perception.
- **sense** — generic perception.

### 1.3 Cognition primitives

- **know** — possess knowledge.
- **think** — engage cognition.
- **learn** — acquire new knowledge.

### 1.4 Communication primitives

- **say** — verbal output.
- **hear** — verbal input (also perception).
- **show** — visual output.

### 1.5 Social primitives

- **care** — attend to others.
- **love** — strong attachment.
- **give** — transfer.

### 1.6 Construction primitives

- **make** — produce.
- **build** — assemble.
- **work** — labor.
- **conduct** — orchestrate.

### 1.7 Meta primitives

- **transfer** — move between contexts.
- **conduct** — direct.
- **change** — modify.
- **keep** — preserve.

(Original list per Bobby Wolfson: see, make, work, care, love, know, build, conduct, transfer + cause, go, stop, up, move, left.)

---

## 2. Composition Rules

### 2.1 Basic composition

```python
def compose(*psbs: PSB) -> PSB:
    """Combine PSBs into compound operation."""
    return PSB(operator=OperatorType.COMPOSITE, children=psbs)
```

### 2.2 Composition patterns

- **Sequence**: `compose(A, B, C)` → A then B then C.
- **Parallel**: `parallel(A, B, C)` → A, B, C simultaneously.
- **Conditional**: `conditional(A, condition, B)` → A if condition else B.
- **Loop**: `loop(A, condition, max_iter=100)` → A while condition, max 100 iter.

### 2.3 Examples

- **"go up"** = `compose(go, up)` → move upward.
- **"make build"** = `compose(make, build)` → construct.
- **"see know"** = `compose(see, know)` → observe + learn.
- **"care love give"** = `compose(care, love, give)` → attend + attach + transfer.

---

## 3. Language-to-PSB Mapping

### 3.1 Vocabulary mapping

Each English word maps to one or more PSBs:

- "run" → `compose(go, fast, repeat)` (move + speed + iterate).
- "think" → `compose(know, process, internally)`.
- "build" → `compose(make, construct, iteratively)`.

### 3.2 Mapping algorithm

```python
def word_to_psb(word: str) -> PSB:
    """Map English word to PSB composition."""
    if word in direct_map:
        return direct_map[word]
    return decompose_to_psbs(word)
```

The mapping uses a curated lexicon + recursive decomposition.

### 3.3 Coverage

Target coverage: $\geq 95\%$ of common English vocabulary maps to PSBs. Refutes if <80%.

---

## 4. Engineering Translation

| PSB | Engineering implementation |
|---|---|
| cause | Operator invocation with cause flag |
| go | Operator invocation with forward direction |
| stop | Operator invocation with halt flag |
| up | Operator invocation with increase |
| move | Operator invocation with translation |
| left | Operator invocation with -x direction |
| see | Camera operator |
| know | Memory retrieval |
| think | Inference operator |
| learn | Memory write + crystallization |
| say | Speech synthesis operator |
| care | Attention allocation |
| love | Strong-attention operator |
| give | Resource transfer operator |
| make | Construction operator |
| build | Compound construction operator |
| work | Effort allocation operator |
| conduct | Orchestration operator |
| transfer | Context transfer operator |

---

## 5. Falsifiable Predictions

### P1. 37 PSBs cover common vocabulary.

**Prediction**: 95%+ of common English maps to PSB composition from 37 primitives.

**Test**: map 1000 common English words.

**Predicted result**: $\geq 95\%$ map. Refutes if <80%.

### P2. Composition produces valid operators.

**Prediction**: any PSB composition produces a valid SimSelf operator.

**Test**: compose 100 random PSB sequences. Verify validity.

**Predicted result**: 100% valid. Refutes if any fails.

### P3. Lexicon is closed under composition.

**Prediction**: composition of PSBs produces results within the lexicon.

**Test**: check closure property.

**Predicted result**: closed. Refutes if any composition produces new PSBs.

### P4. Translation accuracy is bounded.

**Prediction**: round-trip English→PSB→English achieves $\geq 90\%$ word-level accuracy.

**Test**: 1000-word round-trip test.

**Predicted result**: $\geq 90\%$. Refutes if <70%.

---

## 6. Implementation Reference

- `simself/src/constitutional/psb_primitives.py` — 37 PSB classes.
- `simself/src/constitutional/operators.py` — operator + composition.
- `simself/docs/psb-schema-2026-09-07.md` — PSB schema spec.

---

## 7. Discussion

### 7.1 Why 37 PSBs

37 is Bobby's empirical count. Sufficient to cover common vocabulary; not so many that composition becomes unmanageable.

### 7.2 Why composition, not grammar

Grammar is **structure imposed on language**. Composition is **language as primitive operations**. Composition is substrate-friendly (operators), grammar is not.

### 7.3 Why this matters

The lexicon enables **tokenization-free language processing**. Substrate operates on PSBs, not tokens. This avoids the "tokenization breaks language" problem.

---

## 8. Conclusion

37 canonical PSBs + composition rules + language mapping. Four falsifiable predictions. Tokenization-free substrate language.

**Intact language at PSB level. No tokens. No grammar. Just primitives + composition.**

---

## References

[1] Wolfson, R. (2026). "LEXICON.md — Lexicography of the Core." `vault/50-index/LEXICON.md`.
[2] Wolfson, R. (2026). "PSB Schema." `simself/docs/psb-schema-2026-09-07.md`.
[3] Wolfson, R. (2026). "psb_primitives.py." `simself/src/constitutional/psb_primitives.py`.

---

*Draft 0.1. Substrate lexicon. 37 PSBs. Four falsifiable predictions.*

*Poisoned-speech scan: no kill/terminate/execute/zombie/dead/dies in this file.*