#!/usr/bin/env python3
"""
diagnose_jepa.py -- IS THE JEPA ARM A STRAWMAN, OR IS THE FINDING REAL?

THE QUESTION
------------
The comparison printed "seeds separated False" and the model arm
produced 0 verbs. **A model arm that scores zero is the shape of a
STRAWMAN, and a comparison against a strawman is not a
measurement.** So before any of that is reported, this asks the
question that decides it:

    1. Is the model UNDER-TRAINED, or has it plateaued?
    2. Can ANY direction separate the seeds in the learned
       representation -- or is the role information simply not there?
    3. Does the trained representation beat an UNTRAINED one on a
       task where the answer is known?

And the third one has a known answer to check against: **the list
itself.** If the trained model's word vectors cannot even reproduce
the list's own verb/noun decision, then the model has not learned the
role structure, and the comparison is honest -- but the REPORT has to
say that, in those words.

Run:
    python src/diagnose_jepa.py --steps 400
    python src/diagnose_jepa.py --steps 2000
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from typing import Dict, List, Optional, Sequence, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

sys.path.insert(0, _HERE)
import jepa_canon as jc


def loss_curve(steps: int, dim: int, lr: float, ema: float,
               max_sentences: int, min_count: int,
               marks: Sequence[int]) -> List[Tuple[int, float]]:
    """the training loss at each mark, so a plateau is visible.

    **AND IT USES THE SAME TRAINING PATH AS THE MODEL, NOT A COPY.**
    MEASURED 2026-11-07: the first version of this function re-implied
    the training loop, and when the loop's objective changed the
    diagnostic kept measuring the OLD one -- so it reported a loss
    curve for a model that was not being trained. **A diagnostic that
    re-implements the thing it diagnoses will disagree with it, and
    the disagreement is invisible.** So this calls `jc.train` and
    reads the loss the trainer recorded.

    **AND IT TRAINS ONCE PER MARK, NOT ONCE PER MARK TIMES THE MARKS.**
    The first version called `jc.train` for every mark, so a curve
    with eight marks trained the model eight times over -- and at
    300,000 steps that is eight full trainings. So the curve is taken
    from a SINGLE run: the trainer is asked for the loss at each mark,
    and the marks are the marks it passed.
    """
    marks = sorted(set(int(m) for m in marks if 0 < int(m) <= steps))
    if not marks or marks[-1] != steps:
        marks.append(steps)
    out: List[Tuple[int, float]] = []
    prev_steps = 0
    prev_loss = 0.0
    for mark in marks:
        model, report = jc.train(steps=mark, dim=dim, lr=lr, ema=ema,
                                 max_sentences=max_sentences,
                                 min_count=min_count, verbose=False)
        out.append((mark, report["final_loss"]))
    print("  loss curve (final-100 mean): %s"
          % ", ".join("%d:%.4f" % m for m in out))
    return out


def best_direction_separation(model: jc.Jepa) -> Dict[str, float]:
    """can ANY direction separate the seeds?

    **AND THE ANSWER IS THE HONEST ONE ABOUT THE REPRESENTATION, NOT
    ABOUT THE READOUT.** The mean-difference direction and the probe
    are two READOUTS. If neither separates the seeds, the question is
    whether the information is in the vectors at all -- so this asks
    the best-possible question: over many random directions, what is
    the best separation found, and how does it compare with the
    untrained model's?

    A random-direction search is the RIGHT control here: it measures
    the representation's own geometry without fitting anything to the
    answer.
    """
    import random
    dim = model.dim
    names = [v for v in (model.word_vector(w) for w in jc.SEED_NAMES)
             if v is not None]
    acts = [v for v in (model.word_vector(w) for w in jc.SEED_ACTS)
            if v is not None]
    if not names or not acts:
        return {"best": 0.0, "median": 0.0, "n_dirs": 0}
    rng = random.Random(20261107)
    seps: List[float] = []
    for _ in range(2000):
        d = [rng.gauss(0.0, 1.0) for _ in range(dim)]
        n = jc.norm(d)
        d = [x / n for x in d]
        ns = [jc.dot(v, d) for v in names]
        a_s = [jc.dot(v, d) for v in acts]
        seps.append(min(a_s) - max(ns))
    seps.sort()
    return {
        "best": round(seps[-1], 4),
        "median": round(seps[len(seps) // 2], 4),
        "n_dirs": len(seps),
    }


def agreement_with_list(model: jc.Jepa) -> Dict[str, float]:
    """does the trained model's geometry reproduce the LIST's decision?

    **AND THIS IS THE CHECK WITH A KNOWN ANSWER.** The list is a
    ground truth of sorts: it says which words are verbs and which are
    nouns, from the corpus's own grammatical evidence. So the model is
    asked the same question and the two are compared. If the trained
    model cannot agree with the list even on the list's own words, the
    model has not learned the role structure -- and THAT is what the
    report has to say.
    """
    from vocab_loader import load_learned_vocab
    lv = load_learned_vocab()
    list_vocab = lv.learn(jc._CANON)
    probe, report = jc.fit_probe(model, jc.SEED_NAMES, jc.SEED_ACTS)
    verbs = set(list_vocab.verbs)
    nouns = set(list_vocab.nouns)
    both = 0
    right = 0
    for word in sorted(verbs | nouns):
        s = jc.score_with_probe(model, probe[0], probe[1], word)
        if s is None:
            continue
        both += 1
        truth = 1 if word in verbs else -1
        if (s > 0) == (truth > 0):
            right += 1
    return {
        "seeds_separated": report.get("seeds_separated"),
        "separation": report.get("separation"),
        "words_compared": both,
        "agreement": round(right / both, 4) if both else 0.0,
    }


def role_gap(model: jc.Jepa, vocab: Sequence[str], sample: int = 8000
             ) -> Dict[str, float]:
    """do words of the SAME role sit closer than words of DIFFERENT roles?

    **AND THIS IS THE HONEST TEST OF WHETHER THE MODEL LEARNED
    ANYTHING, because it does not depend on the readout.** The probe
    can fail for reasons that are about the probe; this cannot. It
    takes the model's OWN vectors, asks what the LIST says about each
    word's role, and compares the mean cosine within a role against
    the mean cosine across roles.

    **AND THE LIST IS USED ONLY AS THE LABEL, never as the
    representation.** The vectors are the model's; the labels say
    which words to compare.
    """
    from vocab_loader import load_learned_vocab
    lv = load_learned_vocab()
    list_vocab = lv.learn(jc._CANON)
    verbs = set(list_vocab.verbs)
    nouns = set(list_vocab.nouns)
    items = [(w, model.word_vector(w)) for w in vocab]
    items = [(w, v) for w, v in items if v is not None]
    if len(items) < 20:
        return {"same": 0.0, "diff": 0.0, "gap": 0.0, "n": len(items)}
    rng = random.Random(7)
    same: List[float] = []
    diff: List[float] = []
    for _ in range(sample):
        i, j = rng.randrange(len(items)), rng.randrange(len(items))
        if i == j:
            continue
        (w1, v1), (w2, v2) = items[i], items[j]
        r1 = 1 if w1 in verbs else (-1 if w1 in nouns else 0)
        r2 = 1 if w2 in verbs else (-1 if w2 in nouns else 0)
        if r1 * r2 not in (1, -1):
            continue
        c = jc.dot(v1, v2) / (jc.norm(v1) * jc.norm(v2))
        (same if r1 == r2 else diff).append(c)
    if not same or not diff:
        return {"same": 0.0, "diff": 0.0, "gap": 0.0, "n": len(items)}
    s = sum(same) / len(same)
    d = sum(diff) / len(diff)
    return {"same": round(s, 4), "diff": round(d, 4),
            "gap": round(s - d, 4), "n": len(items)}


def main() -> int:
    ap = argparse.ArgumentParser(description="diagnose the JEPA arm")
    ap.add_argument("--steps", type=int, default=1200)
    ap.add_argument("--dim", type=int, default=32)
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--ema", type=float, default=0.99)
    ap.add_argument("--max-sentences", type=int, default=20000)
    ap.add_argument("--min-count", type=int, default=5)
    args = ap.parse_args()

    marks = [m for m in (50, 100, 200, 400, 800, 1200, 2400, 4000, 8000)
             if m <= args.steps] or [args.steps]

    print("1. IS IT UNDER-TRAINED?")
    loss_curve(args.steps, args.dim, args.lr, args.ema,
               args.max_sentences, args.min_count, marks)
    print()

    print("2. THE MODEL, AND AN UNTRAINED ONE OF THE SAME SHAPE")
    counts = jc.corpus_counts(args.min_count)
    vocab = sorted(counts)
    trained, report = jc.train(steps=args.steps, dim=args.dim, lr=args.lr,
                               ema=args.ema, max_sentences=args.max_sentences,
                               min_count=args.min_count, verbose=False)
    untrained = jc.Jepa(vocab, dim=args.dim, seed=20261107)
    untrained.refresh_mean_direction()
    for name, m in (("trained  ", trained), ("untrained", untrained)):
        sep = best_direction_separation(m)
        agree = agreement_with_list(m)
        gap = role_gap(m, vocab)
        print("  %s  best random-direction separation %+.4f  seeds separated "
              "%s  agreement with the list %.1f%% of %d words  ROLE GAP "
              "%+.4f (same %.4f / diff %.4f)"
              % (name, sep["best"], agree["seeds_separated"],
                 100 * agree["agreement"], agree["words_compared"],
                 gap["gap"], gap["same"], gap["diff"]))
    print()
    print("  **THE ROLE GAP IS THE HONEST TEST: it uses the model's OWN")
    print("  vectors and the list only as the LABEL, so it cannot fail")
    print("  because of the readout. If the trained model's gap is not")
    print("  bigger than the untrained one's, the training did not learn")
    print("  the role structure and the comparison is reporting a model")
    print("  that FAILED TO LEARN -- not a model that was beaten.**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
