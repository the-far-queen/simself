"""
bench_canon_vocab.py -- MEASURE the learned vocabulary before it is trusted.

WHAT THIS BENCH IS
------------------
The handoff's next step is *"feed the learned word lists back into
PRIMITIVES"*. The first attempt at that is wrong in a way only a
measurement shows, so this bench is written BEFORE the wiring, and it
answers four questions with numbers:

  1. ARE THE LISTS DISJOINT? A word in both lists is in both form
     sets, so `SlotPattern.matches()` accepts it for either slot and
     the pattern has lost its power. MEASURED on the unfiltered
     bootstrap: 17,034 of 20,597 verbs are also names -- 72% of the
     union. That list would have pushed coverage to 100% and the
     number would have been a lie.

  2. DOES THE (name, act) TEST DISCRIMINATE? A random pair of English
     words is bound by the pattern at some rate. A real (name, act)
     pair is bound at another rate. **If they are the same rate, the
     pattern is decorative.** This is the measurement that decides
     whether the vocabulary is usable, and it is the one the size of
     the list cannot tell you.

  3. DOES COVERAGE RISE WITHOUT THE NUMBER BECOMING VACUOUS? The
     coverage of the primitives on literary prose was 4.6%-28.5% with
     the canon at 21.0%. A vocabulary that lifts coverage to 90% by
     binding everything has not fixed the engine -- it has made the
     engine lie. So the coverage is reported ALONGSIDE the
     discrimination, and the check is on the pair.

  4. IS THE EVIDENCE THRESHOLD A PLATEAU OR A KNIFE EDGE? A result
     that only works at one setting of one parameter is not a result
     (CENTRAL-RULES rule 6). So the threshold is SWEPT.

THE HELD-OUT SET, AND WHY IT IS NOT THE FITTING SET
---------------------------------------------------
The vocabulary is learned from the canon. If the vocabulary is then
measured on the canon, the number is fitted -- it measures how well the
learner and the canon agree. So the PRIME metric is measured on text
the learner never saw: Bobby's own books (`~/Desktop/books`), which
are NOT in the canon.

`--blind` prints the held-out numbers alone, with no canon number
beside them, so the two cannot be confused.

Run:
    python src/bench_canon_vocab.py            # learn, measure, write
    python src/bench_canon_vocab.py --check    # verify only
    python src/bench_canon_vocab.py --sweep    # the threshold sweep
    python src/bench_canon_vocab.py --blind    # held-out numbers only
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from typing import Dict, List, Optional, Sequence, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.dirname(_HERE)
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from constitutional import learned_vocab as lv

_HERMES = os.path.abspath(os.path.join(_SRC, "..", ".."))
_CANON = os.path.join(_HERMES, "work_repos", "sacred-library", "corpus",
                      "deception", "texts")
_BOOKS = os.path.join(os.path.expanduser("~"), "Desktop", "books")

_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")


# ===========================================================================
# THE TEXT
# ===========================================================================

def sentences_from(path: str, limit: Optional[int] = None) -> List[str]:
    """the sentences of a file, long enough to be a sentence."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return []
    if path.endswith(".php"):
        text = re.sub(r"<script.*?</script>", " ", text, flags=re.S)
        text = re.sub(r"<style.*?</style>", " ", text, flags=re.S)
        text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
    out = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 25]
    return out[:limit] if limit else out


def canon_sentences(limit_per_file: int = 40,
                    max_files: int = 12) -> List[str]:
    out: List[str] = []
    if not os.path.isdir(_CANON):
        return out
    for fn in sorted(os.listdir(_CANON)):
        if not fn.endswith(".txt"):
            continue
        out.extend(sentences_from(os.path.join(_CANON, fn), limit_per_file))
        if len(out) >= limit_per_file * max_files:
            break
    return out


def held_out_sentences() -> Dict[str, List[str]]:
    """Bobby's own books -- NOT in the canon, so this is a held-out set."""
    targets = {
        "star_rider": "star-rider.txt",
        "college_girl": "College-Girl.php",
        "gabrielle_ship": "0-Gabrielle1.txt",
        "little_monk": "The-Little-Monk.txt",
    }
    out: Dict[str, List[str]] = {}
    for name, fn in targets.items():
        path = os.path.join(_BOOKS, fn)
        sents = sentences_from(path, 400)
        if sents:
            out[name] = sents
    return out


# ===========================================================================
# THE MEASUREMENTS
# ===========================================================================

def discrimination(vocab: lv.Vocabulary, held_out: Dict[str, List[str]],
                   seed: int = 20261031) -> Dict[str, object]:
    """how often does the (name, act) test bind, on REAL adjacency versus
    RANDOM adjacency?

    **AND THE FIRST VERSION OF THIS CONTROL WAS CONFOUNDED.**
    MEASURED 2026-10-31: it drew the control pairs from the vocabulary
    itself, so it measured the LIST COMPOSITION (64.7% nouns x 35.3%
    verbs = 0.228, which is exactly the 0.2238 it reported) rather than
    the text. A real-text rate of 0.051 against a control of 0.224 read
    as "the pattern has no power" -- and the real cause was that the
    control sampled the wrong population. **The instrument was wrong,
    and the negative reading was wrong.**

    **SO THE CONTROL NOW COMES FROM THE TEXT**, in two independent ways
    that must agree (CENTRAL-RULES rule 5, two derivations):

      SHUFFLED  each sentence's words are shuffled, and the rate of
                (name, act) adjacency is measured on the shuffle. Same
                words, same sentence lengths, random order.

      ANALYTIC  the rate implied by the text's own token composition,
                p(name) * p(act). Independent of the shuffle.

    The lift is real_rate / shuffled_rate. A lift near 1.0 means the
    pattern is matching POSITION rather than ROLE.
    """
    verbs = set(vocab.verbs)
    nouns = set(vocab.nouns)
    rng = random.Random(seed)

    real_total = 0
    real_bind = 0
    shuf_total = 0
    shuf_bind = 0
    tok_total = 0
    tok_noun = 0
    tok_verb = 0

    for name, sents in held_out.items():
        for s in sents:
            words = [w.lower() for w in _WORD.findall(s)]
            if len(words) < 2:
                continue
            for i in range(len(words) - 1):
                real_total += 1
                if words[i] in nouns and words[i + 1] in verbs:
                    real_bind += 1
            # the token composition of THIS text
            for w in words:
                tok_total += 1
                if w in nouns:
                    tok_noun += 1
                elif w in verbs:
                    tok_verb += 1
            # the SHUFFLED control -- the same words, random order
            shuffled = list(words)
            rng.shuffle(shuffled)
            for i in range(len(shuffled) - 1):
                shuf_total += 1
                if shuffled[i] in nouns and shuffled[i + 1] in verbs:
                    shuf_bind += 1

    real_rate = real_bind / real_total if real_total else 0.0
    shuf_rate = shuf_bind / shuf_total if shuf_total else 0.0
    p_noun = tok_noun / tok_total if tok_total else 0.0
    p_verb = tok_verb / tok_total if tok_total else 0.0
    analytic_rate = p_noun * p_verb
    return {
        "real_pairs": real_total,
        "real_bind": real_bind,
        "real_rate": real_rate,
        "shuffled_pairs": shuf_total,
        "shuffled_bind": shuf_bind,
        "shuffled_rate": shuf_rate,
        "analytic_rate": analytic_rate,
        "p_name": p_noun,
        "p_act": p_verb,
        "lift": (real_rate / shuf_rate) if shuf_rate else 0.0,
        #: the two derivations must agree, or one of them is wrong
        "derivations_agree": abs(shuf_rate - analytic_rate) < 0.02,
    }


def coverage_of(vocab: lv.Vocabulary, sentences: Sequence[str]) -> Dict[str, float]:
    """the fraction of sentences that contain a (name, act) window."""
    verbs = set(vocab.verbs)
    nouns = set(vocab.nouns)
    if not sentences:
        return {"total": 0, "covered": 0, "fraction": 0.0}
    covered = 0
    for s in sentences:
        words = [w.lower() for w in _WORD.findall(s)]
        hit = False
        for i in range(len(words) - 1):
            if words[i] in nouns and words[i + 1] in verbs:
                hit = True
                break
        if hit:
            covered += 1
    return {"total": len(sentences), "covered": covered,
            "fraction": covered / len(sentences)}


def sweep(min_evidence: Sequence[int],
          min_ratio: Sequence[float] = (1.0,)) -> List[Dict[str, object]]:
    """the threshold sweep -- plateau or knife edge?

    **AND THE SWEEP REPORTS THE COVERAGE AND THE LIFT TOGETHER.**
    A sweep that reports coverage alone would pick the point where
    coverage is highest, which is the point where the vocabulary is
    largest and the pattern selects nothing (MEASURED: LIFT 1.00x at
    50.4% coverage). The lift is the number that says whether the
    coverage means anything, so both are in the table.
    """
    out = []
    for me in min_evidence:
        for mr in min_ratio:
            v = lv.learn(_CANON, min_evidence=me, min_ratio=mr)
            ho = held_out_sentences()
            allsents = [s for v_ in ho.values() for s in v_]
            disc = discrimination(v, ho)
            cov = coverage_of(v, allsents)
            out.append({
                "min_evidence": me,
                "min_ratio": mr,
                "verbs": len(v.verbs),
                "nouns": len(v.nouns),
                "overlap": len(set(v.verbs) & set(v.nouns)),
                "held_out_coverage": cov["fraction"],
                "lift": float(disc["lift"]),      # type: ignore[arg-type]
                "real_rate": float(disc["real_rate"]),   # type: ignore
                "shuffled_rate": float(disc["shuffled_rate"]),  # type: ignore
            })
    return out


# ===========================================================================
# THE REPORT
# ===========================================================================

def main() -> int:
    ap = argparse.ArgumentParser(description="the canon vocabulary bench")
    ap.add_argument("--check", action="store_true",
                    help="verify the artifact, write nothing")
    ap.add_argument("--sweep", action="store_true",
                    help="sweep the evidence threshold")
    ap.add_argument("--blind", action="store_true",
                    help="print held-out numbers only")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.sweep:
        rows = sweep([1, 2, 3, 5, 8], [1.0, 2.0, 3.0, 5.0, 8.0, 12.0])
        print("=" * 86)
        print("THE THRESHOLD SWEEP -- plateau or knife edge?")
        print("=" * 86)
        print("  %-8s %-8s %8s %8s %8s %14s %10s %10s"
              % ("min_ev", "ratio", "verbs", "nouns", "overlap",
                 "held-out cov", "real rate", "lift"))
        for r in rows:
            cov_f = float(r["held_out_coverage"])   # type: ignore[arg-type]
            print("  %-8d %-8.1f %8d %8d %8d %13.1f%% %10.4f %9.2fx"
                  % (r["min_evidence"], r["min_ratio"], r["verbs"],
                     r["nouns"], r["overlap"],
                     100 * cov_f, r["real_rate"],
                     r["lift"]))
        print()
        print("  THE READING: coverage alone would pick the last row.")
        print("  The lift is what says whether the coverage MEANS anything.")
        return 0

    if args.check:
        v = lv.load_vocabulary()
        print("the artifact is present and its digest matches")
        print("  verbs %d  nouns %d  overlap %d  disjoint %s"
              % (len(v.verbs), len(v.nouns),
                 len(set(v.verbs) & set(v.nouns)), v.is_disjoint()))
        return 0

    # LEARN
    vocab = lv.learn(_CANON)
    ho = held_out_sentences()
    canon = canon_sentences()

    if args.blind:
        disc = discrimination(vocab, ho)
        allsents = [s for v_ in ho.values() for s in v_]
        cov = coverage_of(vocab, allsents)
        disc_real = float(disc["real_rate"])   # type: ignore[arg-type]
        disc_lift = float(disc["lift"])        # type: ignore[arg-type]
        print("=" * 78)
        print("HELD-OUT ONLY -- text the learner never saw")
        print("=" * 78)
        print("  sentences            %d" % cov["total"])
        print("  covered by a window  %d (%.1f%%)"
              % (cov["covered"], 100 * cov["fraction"]))
        print("  real-pair bind rate  %.4f" % disc_real)
        print("  shuffled control     %.4f"
              % float(disc["shuffled_rate"]))    # type: ignore[arg-type]
        print("  analytic control     %.4f"
              % float(disc["analytic_rate"]))    # type: ignore[arg-type]
        print("  LIFT                 %.2fx" % disc_lift)
        return 0

    print("=" * 78)
    print("THE LEARNED VOCABULARY")
    print("=" * 78)
    print("  verbs %d   nouns %d   OVERLAP %d   disjoint %s"
          % (len(vocab.verbs), len(vocab.nouns),
             len(set(vocab.verbs) & set(vocab.nouns)),
             vocab.is_disjoint()))
    print("  excluded: ambiguous %d  function %d  rare %d"
          % (vocab.excluded_ambiguous, vocab.excluded_function,
             vocab.excluded_rare))
    print("  verbs sample:", ", ".join(list(vocab.verbs)[:18]))
    print("  nouns sample:", ", ".join(list(vocab.nouns)[:18]))
    print()

    print("=" * 78)
    print("THE DISCRIMINATION -- real adjacency versus shuffled adjacency")
    print("=" * 78)
    disc = discrimination(vocab, ho)
    d_real = float(disc["real_rate"])       # type: ignore[arg-type]
    d_shuf = float(disc["shuffled_rate"])   # type: ignore[arg-type]
    d_ana = float(disc["analytic_rate"])    # type: ignore[arg-type]
    d_lift = float(disc["lift"])            # type: ignore[arg-type]
    print("  real (name, act) adjacency  %d of %d  = %.4f"
          % (disc["real_bind"], disc["real_pairs"], d_real))
    print("  SHUFFLED control             %d of %d  = %.4f"
          % (disc["shuffled_bind"], disc["shuffled_pairs"], d_shuf))
    print("  ANALYTIC control (p_n*p_a)                    = %.4f" % d_ana)
    print("  the two derivations agree: %s   (|diff| = %.4f)"
          % (disc["derivations_agree"],
             abs(d_shuf - d_ana)))
    print("  LIFT                                 %.2fx" % d_lift)
    print("  (lift near 1.0 = the pattern matches POSITION, not ROLE)")
    print()

    print("=" * 78)
    print("THE COVERAGE, on held-out text")
    print("=" * 78)
    for name, sents in ho.items():
        c = coverage_of(vocab, sents)
        print("  %-16s %4d sentences  %4d (%.1f%%)"
              % (name, c["total"], c["covered"], 100 * c["fraction"]))
    c = coverage_of(vocab, canon)
    print("  %-16s %4d sentences  %4d (%.1f%%)   <- the fitting set"
          % ("the canon", c["total"], c["covered"], 100 * c["fraction"]))
    print()

    if args.json:
        print(json.dumps({"discrimination": disc}, indent=2))

    path = lv.write_artifact(vocab)
    print("  artifact written: %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
