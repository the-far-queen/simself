# Long-Term Memory Architecture (w23)

**Source:** `Desktop/SimSelf/docs/w23-long-term-memory.md` (2.7KB)
**Filed:** 2026-09-14 by Hermes for Bobby (re-mining pass)
**Status:** **engineering reference** — memory substrate for persistent learning SimSelf

---

## Core idea

Memory is **not just chat history** — it's a **structured, self-organizing, decaying knowledge system** with three layers.

---

## Three layers

1. **Resources** — raw, timestamped logs/transcripts. Immutable source of truth.
2. **Items** — atomic facts extracted from resources (e.g., "User prefers Python").
3. **Categories** — evolving markdown summaries that weave items into coherent narratives.

---

## Two architectures

| Architecture | Best for | Format |
|--------------|----------|--------|
| **File-Based Memory** | assistants, companions | hierarchical, narrative-focused |
| **Context-Graph Memory** | precise systems (CRM, research) | subject-predicate-object relationships |

---

## Key innovations

- **Active memorization** — new info rewrites category summaries, handles contradictions automatically.
- **Tiered retrieval** — pull summaries first, drill down only if insufficient.
- **Hybrid search** — vector (semantic similarity) + graph (relationship traversal) in parallel.
- **Conflict resolution** — detects contradictions, archives old facts, promotes current ones.
- **Memory decay & maintenance** — nightly consolidation, weekly summarization, monthly re-indexing to prevent rot.

---

## Why this matters for the project

- Provides **recursive memory** that can digest long files, research papers, code repos.
- Enables **SimSelf's sleep-mode learning** — new info is integrated, summarized, related.
- Fits **sheaf-based consistency** — memory categories align with sheaf stalks (coding, robotics, info-integration).
- **Governor-regulated** — memory writes/decays follow qualification rules; no junk accumulation.

---

## Implementation outline

### Write path
```
Resource → Items → Category update (with conflict resolution)
```

### Read path
```
Category selection → Sufficiency check → Hierarchical search (items/resources)
```

### Maintenance
- Cron jobs for consolidation
- Summarization
- Re-indexing

---

## Cross-reference

This is the memory substrate for `simself/src/constitutional/` (B + L modules). The three-layer model maps to:
- **Resources** = raw ledger entries (append-only, like `ledger.db`)
- **Items** = facts (denormalized, queryable)
- **Categories** = sacred library entries (curated, governor-approved)

Per Bobby 2026-09-13 karpathy memory rule: **memory is pointers**. The w23 architecture IS the substrate, but the AGENT'S memory (in `~/.hermes/memory_store.db`) should remain pointer-only — content lives in vault files.

---

*Filed 2026-09-14 by Hermes. Per Bobby: re-mining pass on underused originals.*
