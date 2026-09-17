"""
mltr_compile.py — decompose an English span into (PSB, role) triples.

Per Bobby 2026-09-17: "tokenization is an error and intelligence is
extant in intact lexicon." This is the first prototype — a small
rule-based decomposer that maps surface tokens to PSBs.

Usage:
    python mltr_compile.py "I made a thing yesterday."
    python mltr_compile.py --json "She is making it for him."

Output (text mode):
    token=made  psb=make  role=verb  domain=creation  mmm=0.5  snr=0.95
    token=a     psb=(none) role=article
    token=thing psb=(none) role=noun
    ...

Output (json mode): structured dict per token.

This is a prototype. Real MLTR will need:
- argument-structure extraction (agent, patient, instrument, ...)
- aspect composition (start, stop, keep, finish + verb)
- negation and modality
- cross-PSB composition rules (give X to Y, transfer X from A to B)

The schema is in psb.py + simself/docs/psb-schema-2026-09-17.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from psb import load_catalog, lookup  # noqa: E402


# Tiny stop-word table for the article/preposition/conjunction slots
# that the current PSB schema doesn't yet cover.
_NON_PSB_ROLES = {
    "the": "article", "a": "article", "an": "article",
    "i": "pronoun", "you": "pronoun", "he": "pronoun", "she": "pronoun",
    "it": "pronoun", "we": "pronoun", "they": "pronoun",
    "me": "pronoun", "him": "pronoun", "her": "pronoun",
    "us": "pronoun", "them": "pronoun",
    "my": "pronoun", "your": "pronoun", "his": "pronoun", "its": "pronoun",
    "our": "pronoun", "their": "pronoun",
    "for": "preposition", "to": "preposition", "from": "preposition",
    "with": "preposition", "by": "preposition", "at": "preposition",
    "on": "preposition", "in": "preposition", "of": "preposition",
    "into": "preposition", "onto": "preposition", "over": "preposition",
    "under": "preposition", "about": "preposition",
    "and": "conjunction", "or": "conjunction", "but": "conjunction",
    "if": "conjunction", "then": "conjunction", "because": "conjunction",
    "while": "conjunction", "when": "conjunction",
    "although": "conjunction", "though": "conjunction",
    "yesterday": "time", "today": "time", "tomorrow": "time",
    "now": "time", "soon": "time", "later": "time",
    "always": "time", "never": "time", "often": "time", "sometimes": "time",
    "very": "degree", "really": "degree", "quite": "degree",
    "somewhat": "degree", "slightly": "degree",
    "not": "negation", "no": "negation",
    "can": "modality", "could": "modality", "may": "modality",
    "might": "modality", "must": "modality", "shall": "modality",
    "should": "modality", "will": "modality", "would": "modality",
}


def _classify_token(tok: str, catalog):
    """Return (psb_or_none, role, domain_or_none, mmm_or_none, snr_or_none)."""
    t = tok.lower().strip()
    # Strip common punctuation for lookup
    t_clean = re.sub(r"[^a-z0-9'-]", "", t)
    if not t_clean:
        return None, "punct", None, None, None

    psb = lookup(t_clean, catalog)
    if psb is not None:
        return psb, "verb", psb.domain, psb.mmm, psb.snr

    if t_clean in _NON_PSB_ROLES:
        return None, _NON_PSB_ROLES[t_clean], None, None, None

    # Heuristic: words ending in -ing/-ed that are NOT just "thing"-
    # shaped nouns (length > 5 chars, not in {thing, sing, ring, ...})
    if re.match(r"^[a-z]+ing$", t_clean) and len(t_clean) > 5 and t_clean not in {
        "thing", "string", "ring", "sing", "king", "bring", "sting",
        "swing", "fling", "cling", "wring", "zing",
    }:
        return None, "verb-out-of-schema", None, None, None
    if re.match(r"^[a-z]+ed$", t_clean) and len(t_clean) > 4 and t_clean not in {
        "red", "bed", "fed", "led", "wed", "shed", "sled",
    }:
        return None, "verb-out-of-schema", None, None, None

    return None, "noun-or-unknown", None, None, None


def compile_span(span: str) -> list:
    """Return a list of dicts, one per token, with PSB + role info."""
    catalog = load_catalog()
    # Split on whitespace, keep punctuation attached to preceding token
    raw = span.split()
    out = []
    for tok in raw:
        psb, role, domain, mmm, snr = _classify_token(tok, catalog)
        out.append({
            "token": tok,
            "psb": psb.psb if psb else None,
            "role": role,
            "domain": domain,
            "mmm": mmm,
            "snr": snr,
        })
    return out


def main(argv):
    p = argparse.ArgumentParser(description="Compile a span to MLTR (PSB) triples.")
    p.add_argument("span", help="The English span to compile.")
    p.add_argument("--json", action="store_true", help="Output as JSON.")
    args = p.parse_args(argv)

    triples = compile_span(args.span)

    if args.json:
        print(json.dumps(triples, indent=2))
    else:
        for t in triples:
            if t["psb"]:
                print(f"token={t['token']:20s}  psb={t['psb']:10s}  "
                      f"domain={t['domain']:14s}  mmm={t['mmm']}  snr={t['snr']}")
            else:
                print(f"token={t['token']:20s}  role={t['role']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
