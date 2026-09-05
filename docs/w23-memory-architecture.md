# w23 — three-layer memory architecture

**Source:** `Desktop/FieldCore/w23-long-term-memory.md` (Bobby, 2026-08-08; possibly from another AI's writeup)
**Status:** memory architecture pattern, applied to SimSelf's long-term memory substrate

Bobby's note describes a recursive memory architecture pattern for AI assistants with three layers (Resources, Items, Categories) and four key mechanisms (active memorization, tiered retrieval, hybrid search, decay/maintenance). This document makes the schemas rigorous and defines construction classes for the SimSelf memory substrate.

---

## 1. three-layer hierarchy

**Resources.** Immutable source-of-truth records. Append-only. Each resource has: id, timestamp, source (file path / URL / transcript), raw content. Once written, never modified. Examples: full Bobby chat transcripts, ingested Desktop/FieldCore files, code commits.

**Items.** Atomic facts extracted from resources. Each item has: id, source_resource_id, timestamp, content (the fact), embedding (vector), tags, category_refs (which categories this item belongs to). Items are append-only — new facts create new items, old facts are not deleted (they may be superseded).

**Categories.** Coherent narratives woven from items. Each category has: id, name, summary_markdown (the current narrative), previous_summaries (archived when rewritten), item_refs (which items back this category). Categories are the only layer that gets rewritten as understanding consolidates.

**Why three layers.** The asymmetry in mutability matters: Resources = ground truth (never change), Items = append-only history (grow only), Categories = current understanding (rewritten). This separation prevents the classic failure mode where rewriting history loses provenance. The Categories layer can be updated, but the old version is always archived with a pointer.

**Mathematical interpretation.** Each layer is a function from the previous layer:
- Resources: set of immutable records
- Items: function `extract_items: Resource → list[Item]` (idempotent: same resource produces same items)
- Categories: function `consolidate: list[Item] → Category` (non-idempotent: same items may consolidate differently as the consolidation algorithm improves)

---

## 2. active memorization

**Pattern.** When a new Item arrives that contradicts an existing Category summary, the Category is rewritten. The old summary is archived with timestamp. The new summary integrates the contradicting item.

**Conflict detection.** Two items contradict if their embeddings are similar (semantic neighborhood) but their content is incompatible (fact-level check). Standard approach: vector similarity > threshold + content-level contradiction classifier. For SimSelf, the contradiction classifier can be the constitutional filter applied to the item pair.

**Resolution rule.** Newest item wins (chronological precedence). Old item is archived but not deleted. The Category summary that referenced the old item is rewritten to reference the new one.

**Why newest-wins.** For SimSelf, the current constitutional ground Ψ₀ is the most recent correct state. Older states are preserved for retrieval (in case the current state is corrupted or the older state was the right one). The append-only property of Items preserves the full history.

---

## 3. tiered retrieval

**Pattern.** Queries hit the Categories layer first (small, fast). If the retrieved summaries answer the query, stop. Otherwise drill down to Items (medium). If still insufficient, drill down to Resources (large).

**Cost model.** Categories: O(categories) per query, ~100-1000 entries. Items: O(items × embedding_dim) for vector search, ~10K-100K entries. Resources: O(resources × raw_content_size), potentially GB-scale.

**When to stop at each layer:**
- Category match score > 0.9 + summary directly answers → return summary
- Item match score > 0.7 + items have sufficient context → return items + brief synthesis
- Otherwise → retrieve full resources

**For SimSelf.** This is the pattern for grounding reasoning in accumulated experience: most facts are available at the Category level (cheap), specific cases drill down to Items (medium), full provenance requires Resources (expensive).

---

## 4. hybrid search (vector + graph)

**Pattern.** Two parallel indexes over Items:
- **Vector index.** Embedding-based semantic similarity (cosine similarity in embedding space). Standard vector database (FAISS, Qdrant, etc.).
- **Graph index.** Subject-predicate-object relationship triples. Standard graph database (Neo4j, etc.).

**Query flow.** Query → both indexes in parallel → merge results by relevance score → return top-k items with both similarity (semantic) and graph-distance (relational) scores.

**Why hybrid.** Pure vector search misses exact relational structure ("item A was extracted from resource B which contradicts item C"). Pure graph search misses semantic similarity ("item A and item D are about the same concept"). Hybrid captures both.

**For SimSelf.** Vector search = semantic recall ("what do I know about prime sheaves?"). Graph search = structural recall ("which items came from Bobby's voice vs. which from external sources?"). Both needed for grounded reasoning.

---

## 5. memory decay & maintenance

**Schedule.**
- **Nightly:** consolidation. Extract new items from day's resources. Update categories that need updating.
- **Weekly:** summarization. Rewrite categories whose item count has grown significantly (>10% new items since last rewrite).
- **Monthly:** re-indexing. Rebuild vector index from scratch (drift correction). Rebuild graph index (broken-link detection). Archive items older than 1 year unless they're still referenced by a category.

**Why decay.** Without decay, the item store grows unboundedly, vector search degrades, and categories become stale. Decay keeps the working set bounded while preserving the full history in Resources.

**For SimSelf.** This is the sleep-mode architecture: nightly consolidation = "REM sleep" (extract new facts), weekly summarization = "slow-wave sleep" (consolidate understanding), monthly re-indexing = "memory reconsolidation" (rebuild indexes).

---

## 6. sheaf-stalk alignment

**Pattern.** Each sheaf in FieldCore's sheaf architecture (the 4 sheaves: (2,3), (5,7), (11,13), (17,19)) gets its own Category set in SimSelf's memory.

**Cross-sheaf items.** Some items span multiple sheaves (e.g., a math fact might span (2,3) and (5,7)). These items belong to multiple categories — one per sheaf they touch.

**Sheaf consistency check.** When a new item arrives, it's tagged with the sheaves it affects. Each affected Category is checked for consistency with the new item. Inconsistencies trigger Category rewrites.

**For SimSelf.** This is the sheaf-based consistency Bobby mentions in his note. The memory substrate enforces sheaf isolation by storing items in sheaf-specific partitions, with cross-references for items that touch multiple sheaves.

---

## 7. construction classes

```python
class ThreeLayerMemory:
    """SimSelf long-term memory: three-layer hierarchy."""
    
    def __init__(self):
        self.resources = ResourceStore()    # immutable, append-only
        self.items = ItemStore()            # atomic facts, embeddings
        self.categories = CategoryStore()   # evolving narratives
    
    def ingest(self, raw_content, source):
        """Write path: Resource → Items → Category update."""
        resource = self.resources.append(raw_content, source)
        new_items = self.extract_items(resource)
        self.items.append_many(new_items)
        for item in new_items:
            self.update_categories(item)  # active memorization
    
    def retrieve(self, query, k=10):
        """Read path: Category → Item → Resource (tiered)."""
        # Try categories first
        cat_results = self.categories.search(query, k=k)
        if self.is_sufficient(cat_results, query):
            return cat_results
        # Drill to items
        item_results = self.items.hybrid_search(query, k=k)
        if self.is_sufficient(item_results, query):
            return item_results
        # Last resort: resources
        return self.resources.search(query, k=k)
    
    def update_categories(self, new_item):
        """Active memorization: rewrite categories that contradict."""
        for cat in self.categories.affected_by(new_item):
            if self.contradicts(cat, new_item):
                self.categories.archive(cat)        # save old version
                self.categories.rewrite(cat, new_item)  # new version
            else:
                self.categories.append_item_ref(cat, new_item)
    
    def extract_items(self, resource):
        """Extract atomic facts from a resource. Idempotent."""
        # Implementation-specific: LLM call, regex, structured parser, etc.
        pass
    
    def is_sufficient(self, results, query):
        """Has the query been answered at this tier?"""
        # Confidence threshold + relevance check
        pass
    
    def contradicts(self, category, item):
        """Two facts contradict if semantically similar but content-incompatible."""
        pass


class ResourceStore:
    """Immutable, append-only resource storage."""
    
    def __init__(self):
        self._resources = []  # append-only list
    
    def append(self, content, source):
        resource = {
            'id': len(self._resources),
            'timestamp': now(),
            'source': source,
            'content': content
        }
        self._resources.append(resource)
        return resource
    
    def get(self, resource_id):
        return self._resources[resource_id]
    
    def search(self, query, k=10):
        # Full-text search over raw content
        pass


class ItemStore:
    """Atomic facts with embeddings and graph relationships."""
    
    def __init__(self):
        self._items = []
        self._vector_index = None  # FAISS or similar
        self._graph_index = None   # NetworkX or similar
    
    def append(self, item):
        item['id'] = len(self._items)
        self._items.append(item)
        self._vector_index.add(item['embedding'])
        self._graph_index.add_triple(item['subject'], item['predicate'], item['object'])
    
    def hybrid_search(self, query, k=10):
        vec_results = self._vector_index.search(query, k=k)
        graph_results = self._graph_index.search(query, k=k)
        return self.merge_results(vec_results, graph_results)


class CategoryStore:
    """Evolving markdown summaries, rewritten as understanding consolidates."""
    
    def __init__(self):
        self._categories = {}
        self._archive = []  # old versions of rewritten categories
    
    def create(self, name, initial_summary):
        cat_id = hash(name)
        self._categories[cat_id] = {
            'name': name,
            'summary': initial_summary,
            'item_refs': [],
            'created_at': now(),
            'last_rewrite': now()
        }
    
    def archive(self, cat_id):
        """Move current category to archive (preserved for retrieval)."""
        old = self._categories[cat_id].copy()
        old['archived_at'] = now()
        self._archive.append(old)
    
    def rewrite(self, cat_id, new_item):
        """Rewrite category with new item integrated."""
        old = self._categories[cat_id]
        new_summary = self.consolidate(old, new_item)
        self.archive(cat_id)
        self._categories[cat_id] = {
            'name': old['name'],
            'summary': new_summary,
            'item_refs': old['item_refs'] + [new_item['id']],
            'created_at': old['created_at'],
            'last_rewrite': now()
        }


class MemoryMaintenance:
    """Scheduled decay and re-indexing."""
    
    def nightly_consolidation(self):
        """Extract items from today's new resources."""
        new_resources = self.resources.today()
        for r in new_resources:
            self.ingest(r['content'], r['source'])
    
    def weekly_summarization(self):
        """Rewrite categories with significant new item counts."""
        for cat in self.categories.all():
            if cat['item_count_since_last_rewrite'] > 0.1 * cat['total_item_count']:
                self.categories.rewrite(cat, None)  # reconsolidate from items
    
    def monthly_reindex(self):
        """Rebuild vector and graph indexes from scratch."""
        self.items.rebuild_indexes()
        self.categories.purge_orphans()  # remove items with no category ref
```

---

## 8. schemas table

| schema | layer | mutability | simself component |
|---|---|---|---|
| Resource | 1 | immutable, append-only | chat transcripts, ingested files |
| Item | 2 | append-only | atomic facts with tags |
| Category | 3 | rewritable (with archive) | current understanding narratives |
| Active memorization | write path | category rewrite on contradiction | governor-regulated memory writes |
| Tiered retrieval | read path | cat → item → resource | cost-optimized grounding |
| Hybrid search | item layer | vector + graph parallel | semantic + structural recall |
| Memory decay | maintenance | time-based | sleep-mode architecture |
| Sheaf alignment | partitioning | per-sheaf categories | sheaf-isolated memory |

---

## 9. what was stripped

Bobby's note has a sentence "Ready to integrate this with the sheaf-governor kernel, or map categories onto stalks?" which is a prompt for further design discussion. This document resolves it: categories map to sheaf stalks (one Category set per sheaf), with cross-sheaf items living in multiple Categories. No open question remains.

Bobby's note also has "Condensed as a single reference block for new-chat context:" followed by an empty section — no actual reference block. Not used.

---

*Source: `Desktop/FieldCore/w23-long-term-memory.md`. Extracted and expanded to construction-ready pseudocode. Mirrored to `~/AppData/Local/hermes/vault/10-minimax/w23-memory-architecture-2026-09-05.md`.*