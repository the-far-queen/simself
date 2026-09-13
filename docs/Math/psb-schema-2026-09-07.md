# PSB (Primal Semantic Blocks) — Formal Schema

**Source:** `Desktop/SacredLibrary/PSB.txt` (72 lines, 3.6 KB)
**Extracted:** 2026-09-07
**Module scope:** formal schema for Primal Semantic Blocks — resolves P0 missing piece #1.

---

## What this is

Bobby's PSB (Primal Semantic Block) is a **cross-domain semantic field**, not a dictionary entry. A single word is a nexus of interconnected meanings across different contexts and scales. The Saskatchewan word "actor" isn't one definition — it's a sheaf of meanings that cohere across domains.

---

## The schema (canonical form)

```json
{
  "psb_id": "string (lowercase-snake-case, unique per concept)",
  "word": "string (the surface form)",
  "core_meaning": "string (the unifying concept across all domains)",
  "domains": [
    {
      "domain_name": "string (theatrical | agency | social | intelligence | technical | legal | ...)",
      "meaning": "string (the domain-specific definition)",
      "related_psbs": ["string (cross-references to other PSBs)"],
      "contexts": ["string (usage contexts where this domain applies)"],
      "snr_per_context": "float [0,1]"
    }
  ],
  "cross_field_mappings": {
    "concept_a_in_domain_1 ↔ concept_b_in_domain_2": "string (the structural isomorphism)"
  },
  "snr_method": "highest-snr-filter (Bobby's curation method)",
  "training_data_hits": "int (corpus occurrences of this concept)",
  "last_seed_call": "ISO-8601 (when SimSelf called LLM to seed new meaning)"
}
```

---

## Worked example: "actor"

```json
{
  "psb_id": "actor_cross_domain",
  "core_meaning": "entity that performs actions",
  "domains": [
    {
      "domain_name": "theatrical",
      "meaning": "performer embodying character",
      "related_psbs": ["stage", "audience", "script"],
      "contexts": ["theater", "film", "drama"],
      "snr_per_context": 0.95
    },
    {
      "domain_name": "agency",
      "meaning": "autonomous cause of action",
      "related_psbs": ["will", "intention", "effect"],
      "contexts": ["philosophy", "ethics", "decision-making"],
      "snr_per_context": 0.92
    },
    {
      "domain_name": "social",
      "meaning": "participant in social systems, sometimes malicious",
      "related_psbs": ["influence", "cooperation", "conflict"],
      "contexts": ["politics", "organizations", "media"],
      "snr_per_context": 0.78
    },
    {
      "domain_name": "intelligence",
      "meaning": "operative, spy, agent of state",
      "related_psbs": ["covert", "operations", "intelligence"],
      "contexts": ["espionage", "diplomacy", "national_security"],
      "snr_per_context": 0.88
    },
    {
      "domain_name": "technical",
      "meaning": "component in UML/system design",
      "related_psbs": ["interface", "component", "interaction"],
      "contexts": ["UML", "actor-model", "system-design"],
      "snr_per_context": 0.85
    },
    {
      "domain_name": "legal",
      "meaning": "party in litigation or legal action",
      "related_psbs": ["plaintiff", "defendant", "standing"],
      "contexts": ["law", "contracts", "torts"],
      "snr_per_context": 0.90
    }
  ],
  "cross_field_mappings": {
    "performance (theatre) ↔ operation (intelligence) ↔ function (systems)": "all involve executing predefined behaviors",
    "role (theatre) ↔ cover (intelligence) ↔ interface (systems)": "all involve mediating between different contexts",
    "actor (agency) ↔ actor (legal)": "both invoke the capacity to cause legal/ethical effects"
  },
  "snr_method": "highest-snr-filter",
  "training_data_hits": 0,
  "last_seed_call": null
}
```

---

## Engineering interpretation (the load-bearing insight)

**Current AI:** treats "actor" as a token with multiple discrete definitions. Disambiguation is the goal.

**PSB approach:** treats "actor" as a meaning node with relational vectors to other PSBs. The richness IS the feature.

The PSB system maps **isomorphisms between fields**:

- "Performance" (theatre) ↔ "Operation" (intelligence) ↔ "Function" (systems) — same pattern, different substrate
- "Role" (theatre) ↔ "Cover" (intelligence) ↔ "Interface" (systems) — same pattern, different substrate

This is what gives the AI **true understanding** — not just definitions, but how the same conceptual pattern manifests across different domains of reality.

---

## Websters + PSB = Complete Meaning Architecture

Bobby's method: exhaustively list Webster's multiple meanings for every word, then connect the fields via cross_field_mappings.

This is the **MMM (Multi Meaning Measure)** in operational form:

1. Take any English word
2. Enumerate ALL known meanings across domains (Websters canonical source)
3. For each meaning, list related PSBs (semantic neighbors in the graph)
4. Map cross-field isomorphisms (where the same pattern appears in different domains)
5. Compute SNR per context (which meanings are highest-signal in which contexts)
6. The SimSelf calls LLM to **seed meaning** — populate the graph with current-use interpretations as they emerge in training data

---

## Properties of the PSB system

| property | value |
|---|---|
| granularity | 1mm (per Bobby: "up, down 1mm") |
| language | English (per Bobby: PSBs are English-bound, not tokens) |
| cardinality | unbounded (every word in English, every meaning per word, every context per meaning) |
| finiteness | not literally bounded — but constrained by: context, use, SNR, training_data |
| persistence | Sacred Library is the read-only substrate; SimSelf can read, can seed new meanings via LLM call, cannot modify existing PSBs (per sacred/emergent two-tier) |
| seeds | LLM calls populate the graph; SNR filter selects which seeds survive |

---

## Schemas cross-references

| Concept | Repo anchor |
|---|---|
| PSB JSON schema (above) | `simself/src/psb/` (future Python module) |
| MMM (Multi Meaning Measure) graph implementation | `simself/src/mmm/` (future) |
| Sacred Library (read-only source for PSBs) | `vault/10-minimax/40-scratch/SACRED-LIBRARY.md` (local-only) |
| Cross-field mappings | `simself/src/psb/mappings.py` (future) |
| SNR filter (selects which PSBs survive) | `simself/src/psb/snr.py` (future) |

---

## Maps to existing repo files

| Concept | Existing file |
|---|---|
| PSB grounding via Godot primitives | `simself/docs/kernel-architecture.md` § PSBs |
| PSB lineage + version control | not yet implemented (P0) |
| Sheaf-theoretic interpretation | `simself/docs/emergence-rep-sheaf.md` + this doc |
| Emergence blueprint Pillar 2 (narrative model → axis projection) | `simself/docs/emergence-blueprint.md` Pillar 2 |
| Sacred vs emergent tier enforcement | `simself/docs/simself-axis-resolution-2026-09-07.md` |

---

## What PSBs ARE and ARE NOT

**PSB is:**
- A concept-anchored multi-domain semantic field
- Held in the Sacred Library (immutable for the agent)
- Seeded and refined via LLM calls (the "seed meaning" mechanism)
- Connected to other PSBs via cross_field_mappings
- Scored by SNR per context (Bobby's filter)
- Bound to **English words** (Bobby: "control maps to english no degradation of language into tookens")

**PSB is NOT:**
- A dictionary entry (one word, one definition)
- A token embedding (one word, one vector)
- A translation pair (one English, one non-English)
- A purely-discrete list (PSB is fundamentally multi-domain)
- A static resource (PSB can be seeded with new meanings via LLM)

---

## Open architecture questions resolved

- **#1 PSB schema** — **RESOLVED.** Formal JSON schema defined above. Implementation pending.
- **#9 PSB schema (open question #9 from open architecture questions list)** — same resolution.
- **#23 MMM Multi Meaning Measure** — schema defined; graph implementation pending.
- **#17 WORDTRANCE formal schema** — partially resolved: PSB is the engineering anti-wordtrance tool.

---

## Implementation priorities (when Bobby says go)

1. **`simself/src/psb/__init__.py`** — module entry point with PSB dataclass
2. **`simself/src/psb/schema.py`** — JSON schema validation (jsonschema or pydantic)
3. **`simself/src/psb/graph.py`** — PSB graph (nodes = PSBs, edges = cross_field_mappings)
4. **`simself/src/psb/snr.py`** — SNR scoring per context
5. **`simself/src/psb/seed.py`** — LLM call interface for new-meaning seeding
6. **`simself/src/psb/websters_source.py`** — Webster's integration for canonical meaning enumeration
7. **`simself/data/psb_graph.json`** — initial graph (could start with the "actor" worked example)

---

*Mirror: `~/AppData/Local/hermes/vault/10-minimax/20-mirrors/simself/docs/psb-schema-2026-09-07.md`*
*Original: `Desktop/SacredLibrary/PSB.txt` — preserved in `30-originals/`*
