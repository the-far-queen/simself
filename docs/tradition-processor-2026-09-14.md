# TraditionProcessor — Sacred Library Ingestion Engine

**Source:** `Desktop/SimSelf/research/tradition_processor.py` (4.0KB, 113 lines, md5 `26484080b06070993ffd0b440d81418d`)
**Filed:** 2026-09-14 by Hermes for Bobby (full ingest, bobby deleting)
**Status:** **canonical research module** — implements the same workflow as the manual sacred-library KG ingest (per `simself/docs/sacred-library/knowledge-graph-2026-09-14.json`)

---

## What this file is

A 4-method processor for ingesting structured tradition text files:

1. **`load_traditions()`** — regex-split text file by `\n\d+\.\s*|\n\n` markers, extract `name:description` pairs
2. **`augment_with_api(name)`** — Wikipedia API lookup for each tradition, get first paragraph
3. **`find_connections()`** — pairwise compare descriptions, link if >2 shared terms
4. **`recursive_integrate(depth=2)`** — recurse augmentation for un-augmented entries

**Engineering reading:** this is the **scripted version** of what I (Hermes) did manually for the sacred-library 50-texts ingest on this turn (2026-09-14). The same workflow, the same output format (json dict), just automated.

---

## The 4 methods

### `load_traditions()` — text splitter

```python
def load_traditions(self):
    with open(self.file_path, 'r') as f:
        raw_text = f.read()
    entries = re.split(r'\n\d+\.\s*|\n\n', raw_text.strip())
    for entry in entries:
        if not entry.strip(): continue
        parts = re.split(r'–|:', entry, maxsplit=1)
        if len(parts) >= 2:
            name = parts[0].strip()
            desc = parts[1].strip()
            self.core_knowledge[name] = {
                'description': desc,
                'sources': [],
                'connections': []
            }
    return self.core_knowledge
```

**Regex:** `r'\n\d+\.\s*|\n\n'` splits on `1. ` or `2. ` style numbered items, OR on double newlines.

**Issue:** the format is fragile. Sacred library 50-texts file uses `\n\n` (no numbering), so it parses via the `|\n\n` branch. A numbered list (like Bobby's earlier tradition notes) would parse via the `\n\d+\.` branch.

**Engineering improvement:** use a parser that detects format (numbered list vs blank-line-separated) and adapts. Or use a structured input format (JSON / YAML).

### `augment_with_api(name)` — Wikipedia lookup

```python
def augment_with_api(self, name):
    if name in self.api_cache:
        return self.api_cache[name]
    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&titles={name}&prop=extracts&exintro=True"
        response = requests.get(wiki_url, timeout=5)
        data = response.json()
        pages = data.get('query', {}).get('pages', {})
        if pages:
            page = next(iter(pages.values()))
            extract = page.get('extract', '')
            soup = BeautifulSoup(extract, 'html.parser')
            first_para = soup.find('p').get_text() if soup.find('p') else ""
        self.api_cache[name] = first_para
        return first_para
    except Exception as e:
        print(f"API lookup failed for {name}: {str(e)}")
        return ""
```

**Wikipedia API call.** Returns the first paragraph of the Wikipedia article for the given tradition name.

**Dependencies:** `requests` + `beautifulsoup4` (bs4) — **NOT installed locally.** Would fail at runtime. Need `pip install requests beautifulsoup4`.

**Engineering improvement:** use multiple sources (Wikipedia + Wikidata + OpenLibrary + sacred-texts.com). Single source = single point of failure. Bobby's SNR criterion (per `bobby-minimax-team-2026-09-14.md` §23) — multiple sources = higher confidence.

### `find_connections()` — pairwise term overlap

```python
def find_connections(self):
    names = list(self.core_knowledge.keys())
    for i, name1 in enumerate(names):
        for name2 in names[i+1:]:
            desc1 = self.core_knowledge[name1]['description'].lower()
            desc2 = self.core_knowledge[name2]['description'].lower()
            common_terms = set(desc1.split()) & set(desc2.split())
            if len(common_terms) > 2:
                self.core_knowledge[name1]['connections'].append({'tradition': name2, 'shared_terms': list(common_terms)})
                self.core_knowledge[name2]['connections'].append({'tradition': name1, 'shared_terms': list(common_terms)})
```

**Naive term overlap.** Two traditions are "connected" if they share >2 common words.

**Issue:** this is **NOT a good signal.** Common English words ("the", "is", "and") inflate counts. Bobby's SNR criterion: common terms in spiritual texts include "psyche", "divine", "consciousness", etc. — these are SIGNAL, not noise.

**Engineering improvement:** 
- filter stopwords (the/a/is/and/of/to/in/on/for)
- weight by term rarity (tf-idf)
- use semantic embeddings instead of term overlap (cosine similarity via MiniMax API)

### `recursive_integrate(depth=2)` — augmentation recursion

```python
def recursive_integrate(self, depth=2, current_depth=0):
    if current_depth >= depth:
        return
    new_additions = []
    for name in list(self.core_knowledge.keys()):
        if not self.core_knowledge[name].get('augmented'):
            api_data = self.augment_with_api(name)
            if api_data:
                self.core_knowledge[name]['sources'].append({'source': 'wikipedia', 'content': api_data})
                self.core_knowledge[name]['augmented'] = True
                new_additions.append(name)
    for name in new_additions:
        self.recursive_integrate(depth, current_depth + 1)
```

**Recursively augment each tradition** with API data, going `depth` levels deep.

**Issue:** the recursion does nothing different at each level (it just re-checks `augmented` flag). Real recursion would: at depth 1, find new connections based on augmented data; at depth 2, augment the newly-connected traditions. This is iterative, not recursive.

**Engineering improvement:** at each depth level, run `find_connections()` with the new data, then `load_traditions()` on the new connection's Wikipedia article.

---

## ⚠️ RUNTIME ISSUE: missing dependencies

**`requests` and `beautifulsoup4` are not installed locally.** The script will fail at import time:
```
ModuleNotFoundError: No module named 'requests'
```

**To fix:** `pip install requests beautifulsoup4`

**Or:** replace `requests` with `urllib.request` (stdlib), replace `BeautifulSoup` with regex parsing (or no HTML parsing — just raw extract).

---

## What this file IS NOT (gaps)

- ❌ **not** integrated with v6.2 unified (no SimSelf, no GraphMemory)
- ❌ **not** integrated with MTE wrapper (just raw text processing)
- ❌ **not** integrated with sacred library KG (the file would be the input pipeline, not the storage)
- ❌ **not** integrated with frequency layer (no resonance monitoring)
- ❌ **not** validated against Bobby's SNR criterion (uses raw term overlap, not signal-weighted)
- ❌ **not** robust to format variation (regex breaks on different layouts)
- ❌ **not** persistent across runs (no checkpointing)

---

## What needs work

| Component | What's missing | Effort |
|-----------|----------------|--------|
| `load_traditions` | format detection, JSON/YAML input | small |
| `augment_with_api` | multi-source, error retry, rate limiting | medium |
| `find_connections` | stopword filter, semantic similarity | medium |
| `recursive_integrate` | real recursion (connection-based depth) | medium |
| runtime | install `requests` + `beautifulsoup4` OR replace with stdlib | trivial |
| integration | wire to v6.2 unified GraphMemory as the storage | medium |

---

## Cross-reference: matches my manual sacred-library ingest

This turn (2026-09-14), I did manually:
1. parsed 50 sacred library entries from `Desktop/SacredLibrary/50 hidden spiritual texts.txt`
2. built JSON-LD KG with 50 nodes + 49 edges + 8 clusters
3. output to `simself/docs/sacred-library/knowledge-graph-2026-09-14.json`
4. used no external API (web search returned 50 URLs, didn't fetch full pages)

This TraditionProcessor would:
1. parse same 50 entries (regex split)
2. augment each with Wikipedia API (first paragraph)
3. find connections (term overlap)
4. save to JSON

**the output is similar in shape** — dict of `{name: {description, sources, connections}}`. The KG I built is more sophisticated (theme extraction, axiom alignment, cluster grouping). TraditionProcessor is the **automated version** that gets us 80% there.

---

## Where this file should land

**decision (per Bobby's refactor-clean autonomy):**
- save raw verbatim ✅ done (vault/30-originals/simself-tradition-processor-original-2026-09-14.md)
- canonical .py: `simself/src/research/tradition_processor.py` (already in `research/` dir from prior ingest)
- canonical doc: this file (simself/docs/tradition-processor-2026-09-14.md)
- future work: install deps OR replace with stdlib + wire to v6.2 GraphMemory

---

*Filed 2026-09-14 by Hermes for Bobby. Per Bobby: "save each raw file going forward i am deleting them... ingest fully no more skims."*

*This file IS the load-bearing research automation for the sacred library ingestion workflow. Currently missing `requests` + `beautifulsoup4` runtime deps. Would be the automation pipeline that produces `knowledge-graph-2026-09-14.json`.*
