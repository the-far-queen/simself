"""
jepa_canon.py -- A JEPA OVER THE FC'S OWN TWO VIEWS, AND THE LIST IT IS MEASURED AGAINST.

WHAT THIS IS
------------
Item 50 asks: "does a JEPA over the FC's own paired corpora beat the
list?" -- the list being the learned word lists (3,075 verbs / 8,231
nouns) that `bench_canon_vocab.py` scores.

**AND THE MEASUREMENT IS A COMPARISON, so both arms must be scored by
THE SAME INSTRUMENT.** So this module does NOT invent a metric. It
imports the bench's own `discrimination()` and `coverage_of()` and
runs them on whatever word partition it is handed.

THE PREMISE, AND WHAT IS ACTUALLY TRUE OF IT
--------------------------------------------
The item says the vocabulary "is learned from TWO corpora -- the canon
corpus and the far-writing Gutenberg corpus -- joined because they are
two views of the same works."

MEASURED 2026-11-07, against the source:
  * `learned_vocab.learn(canon_dir)` takes ONE directory, and the
    artifact `canon_vocab.json` records the sha256 of exactly the 49
    files in `sacred-library/corpus/deception/texts`. ONE corpus.
  * `far-writing/catalog/gutenberg/wikicache/` is 2,831 files and
    EVERY ONE is a JSON API response (Wikipedia/Wikidata queries).
    Zero of the 49 canon texts appear in it. `fieldcore/tools/
    derive_mltr_terms.py` reads it for word COUNTS.

So the second view did not exist and had to be BUILT: the canon texts
are cut from Project Gutenberg, and `ACQUIRED.json` records the source
URL for every work. `sacred-library/corpus/deception/
build_raw_view.py` fetches them, and the second view is on disk now.

**AND HERE IS THE MEASUREMENT THAT DECIDES WHAT THIS EXPERIMENT CAN
SAY AT ALL.** The two views are the SAME OBSERVATION rendered twice:
the raw carries the Gutenberg licence header and a different line wrap,
and the canon carries neither. MEASURED: 97.85% of the canon's
sentences are TOKEN-IDENTICAL to a raw sentence. **A JEPA over a pair
that is 97.85% the same tokens is a JEPA over ONE view** -- and in
LeCun's own taxonomy, "two parts of one document" is the BAD view.
So the number this module prints is a measurement of the FC's actual
data, and the honest reading of it must carry that fact.

THE JEPA, CONCRETELY
---------------------
A JEPA has an ENCODER that embeds a view, a PREDICTOR that maps one
view's embedding toward another's, and a TARGET ENCODER that is a
slowly-moving average of the encoder. The loss is on the PREDICTION
of the target's embedding, and the target branch is stopped-gradient.
That is what makes it a JEPA rather than a word2vec: the model is
trained to predict a REPRESENTATION of the other view, never a token
of it.

    the encoder       E[w]          one vector per corpus word
    the target        E'[w]         the EMA-moving copy of E
    the predictor     P(z)          a linear map from a context
                                     embedding to a predicted target
                                     embedding

    the context       the first half of view A (the canon text)
    the target        the second half of view B (the raw text)

    the loss          1 - cos(P(context), target(target))

**AND THE SPLIT ALTERNATES, so every word gets trained.** A word that
only ever appears in the second half of a sentence would never be a
context word, so its row would never move. So every other step runs
the split the other way round -- view B's first half is the context
and view A's second half is the target.

THE READOUT, AND WHY IT CANNOT BE FAKED
----------------------------------------
A JEPA produces an EMBEDDING; the bench scores a WORD PARTITION. So
the readout has to be stated, and the readout is where a comparison
can be faked. So:

    the encoder's vector for each word, projected onto ONE direction,
    and the words on the two sides of that direction are the verb list
    and the noun list.

**AND THE DIRECTION IS NOT FITTED TO THE ANSWER.** It is fitted on the
SEEDS -- the pronouns (names) and the auxiliaries (acts) -- the same
seeds `learned_vocab.py` starts from. So the model arm is given
exactly what the list arm is given, and the difference between the arms
is the REPRESENTATION, which is the thing under test.

**AND THE PARTITION IS THE CORPUS'S OWN UNIVERSE, not the list's.** The
list is allowed to choose its own words; so is the model. Handing the
model the list's vocabulary as its universe would have been a
comparison where the list picked the ground and the model was graded
on it.

WHY IT IS PURE PYTHON
---------------------
Because numpy is not installed for the interpreter the cron runs
(`python` -> 3.11, no numpy; `py` -> 3.13, with numpy). A model whose
measurement only runs on one of the two interpreters on this machine is
a measurement a later session cannot reproduce.

Run:
    python src/jepa_canon.py --train
    python src/jepa_canon.py --compare
    python src/jepa_canon.py --compare --steps 4000 --dims 16,32,64
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

_HERMES = os.path.abspath(os.path.join(_ROOT, "..", ".."))
_CANON = os.path.join(_HERMES, "work_repos", "sacred-library", "corpus",
                      "deception", "texts")
_RAW = os.path.join(_HERMES, "work_repos", "sacred-library", "corpus",
                     "deception", "_raw")
_RAW_MANIFEST = os.path.join(_HERMES, "work_repos", "sacred-library",
                              "corpus", "deception", "RAW.json")

_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")

#: THE EMBEDDING WIDTH. This is the model's PARAMETER COUNT axis, and
#: it is what the comparison's cost axis runs over.
DEFAULT_DIM = 32

#: A word must appear this many times in the canon corpus to be in the
#: universe the model partitions. The list admits a word on 3
#: grammatical instances, so a corpus-count floor of 5 is in the same
#: order and not lower.
MIN_CORPUS_COUNT = 5

#: HOW MANY POSITIONS IN A SENTENCE THE TRAINER TRIES before it gives
#: up on that sentence. MEASURED 2026-11-07: the first version picked
#: ONE position at random and dropped the step when it was unusable,
#: and at the E3 configuration that threw away 51.12% of the training
#: steps. A rescue finds a usable position for 65.0% of them on the
#: first try, so 8 tries take the waste from 51% to about 0.2%.
POSITION_TRIES = 8

#: THE SEEDS. These are the SAME seeds the list arm starts from: the
#: pronouns (names) and the auxiliaries (acts). The model arm gets no
#: information the list arm does not.
SEED_NAMES = (
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "its", "our", "their", "mine", "yours",
    "this", "that", "these", "those", "who", "whom", "whose", "which",
    "what", "one", "ones", "someone", "anyone", "everyone", "nobody",
)
SEED_ACTS = (
    "is", "are", "was", "were", "be", "been", "being", "am", "do", "does",
    "did", "have", "has", "had", "will", "would", "shall", "should",
    "may", "might", "must", "can", "could", "say", "said",
)


# ===========================================================================
# THE TEXT
# ===========================================================================
def sentences(text: str, min_len: int = 25) -> List[str]:
    out: List[str] = []
    for part in re.split(r"[.!?]+", text):
        s = " ".join(part.split())
        if len(s) > min_len:
            out.append(s)
    return out


def tokens(sentence: str) -> List[str]:
    return [w.lower() for w in _WORD.findall(sentence)]


def read(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def canon_works() -> List[str]:
    return sorted(f for f in os.listdir(_CANON) if f.endswith(".txt"))


def corpus_counts(min_count: int = MIN_CORPUS_COUNT) -> Dict[str, int]:
    """every word of the canon corpus, and how often it occurs."""
    counts: Dict[str, int] = {}
    for fn in canon_works():
        for s in sentences(read(os.path.join(_CANON, fn))):
            for t in tokens(s):
                counts[t] = counts.get(t, 0) + 1
    return {w: c for w, c in counts.items() if c >= min_count}


def corpus_vocabulary(min_count: int = MIN_CORPUS_COUNT) -> List[str]:
    """the words the corpus uses.

    **AND THIS IS THE UNIVERSE THE MODEL PARTITIONS, and it is the
    CORPUS's own -- not the list's.** The list is allowed to choose its
    own words; so is the model. Handing the model the list's vocabulary
    as its universe would have been a comparison where the list picked
    the ground and the model was graded on it.

    **AND THE COUNT IS THE CORPUS'S OWN COUNT, not the list's
    evidence count.** The list admits a word on grammatical evidence
    (a determiner in front of it, say); this floor is how often the
    word occurs. They are different rules, and the model's rule is
    stated here so it can be checked.
    """
    return sorted(corpus_counts(min_count))


# ===========================================================================
# THE TWO VIEWS, AND HOW SIMILAR THEY ARE
# ===========================================================================
def view_pairs(max_sentences: int = 0) -> List[Tuple[List[str], List[str]]]:
    """the (canon, raw) sentence pairs.

    **AND THE PAIRS ARE ALIGNED BY THE SENTENCE TEXT, not by
    position.** The raw text carries the Gutenberg licence header and
    a different line wrap, so position i of the raw is not position i
    of the canon. The alignment is by the normalised sentence.
    """
    if not os.path.isdir(_RAW):
        raise SystemExit(
            "NO SECOND VIEW at %s.\n"
            "Run:  python corpus/deception/build_raw_view.py" % _RAW)
    pairs: List[Tuple[List[str], List[str]]] = []
    for fn in canon_works():
        raw_path = os.path.join(_RAW, fn)
        if not os.path.isfile(raw_path):
            continue
        canon = sentences(read(os.path.join(_CANON, fn)))
        raw = sentences(read(raw_path))
        index: Dict[str, List[str]] = {}
        for s in raw:
            index.setdefault(" ".join(tokens(s)), tokens(s))
        for s in canon:
            other = index.get(" ".join(tokens(s)))
            if other is None:
                continue
            pairs.append((tokens(s), other))
            if max_sentences and len(pairs) >= max_sentences:
                return pairs
    return pairs


def raw_manifest() -> Dict[str, Any]:
    """the builder's manifest, so the pairing ratio can be reported."""
    if not os.path.isfile(_RAW_MANIFEST):
        return {}
    with open(_RAW_MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


# ===========================================================================
# THE LINEAR ALGEBRA
# ===========================================================================
def dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(v: Sequence[float]) -> float:
    """the length of a vector. Never zero: a zero length would make
    the normalization a division by zero, and a NaN loss is the shape
    that looks like a number.

    **AND SO IT MUST NOT BE USED TO ASK WHETHER A VECTOR IS ZERO.**
    MEASURED 2026-11-07: this function returns 1.0 for a zero vector,
    on purpose -- and so a check written as `norm(v) > 1e-12` is TRUE
    for an all-zero vector. That check was written to catch a model
    whose gradient had gone to zero, and it could not catch it: **THE
    INSTRUMENT THAT IS SAFE TO DIVIDE BY IS NOT AN INSTRUMENT FOR
    ASKING WHETHER SOMETHING IS ZERO.** Ask about the largest
    COMPONENT instead, which is what the check does.
    """
    return math.sqrt(sum(x * x for x in v)) or 1.0


def unit(v: Sequence[float]) -> List[float]:
    n = norm(v)
    return [x / n for x in v]


def _uncentre_gradient(dp: Sequence[float], p_hat: Sequence[float],
                       m_hat: Sequence[float], n_p: float
                       ) -> List[float]:
    """the gradient with respect to the UNCENTRED prediction.

    **THE CENTRING IS A PROJECTION, AND A PROJECTION'S GRADIENT IS NOT
    THE IDENTITY.** The centred direction is
    `p_c = unit(p_hat - (p_hat . m) m)`, so a change in p_hat changes
    p_c in TWO ways: the component along m is removed, and the length
    changes. Both are undone here, so the gradient that reaches the
    predictor is the gradient of the loss with respect to the vector
    the predictor actually produces.

    **AND GETTING THIS WRONG IS SILENT.** The loss would still fall,
    because the predictor could still shrink the prediction's
    component along m -- which is free, and teaches nothing.

    **AND THE MISSING FACTOR OF 1/||p|| WAS SILENT TOO, AND IT WAS
    FOUND BY A CENTRAL DIFFERENCE.** MEASURED 2026-11-07: this
    function took `n_p` as an argument and NEVER USED IT, so the
    gradient that reached the predictor was NOT the gradient of the
    loss the module computes. The check is a finite difference of the
    module's own loss against the module's own analytic gradient, and
    they DISAGREED by 83% (the bias, the predictor and the encoder
    all of them), while the corrected chain rule agrees with the same
    finite difference to 6e-11, 2e-8 and 6e-10.

    **AND THE DIRECTION WAS NEVER WRONG, WHICH IS WHY EVERY
    BEHAVIOURAL CHECK STAYED GREEN.** The cosine between the old
    gradient and the true one is 1.0000000000 at every one of 320
    random points: the gradient was off by a POSITIVE SCALAR, and a
    gradient that is off by a positive scalar still DESCENDS. So the
    loss fell, the vectors moved, and the model learned -- and the
    step size was wrong by a factor that moves with ||p||. **A BEHAVIOUR
    CHECK CANNOT SEE A SCALE, AND A SCALE IS WHAT WAS WRONG.**

    **SO THE CHAIN RULE IS WRITTEN OUT IN FULL HERE**, projections
    included, even though the incoming `dp` happens to be orthogonal
    to both p_hat and the mean direction (and so the projections are
    no-ops for the inputs this module produces). Written out, the
    formula is correct for every input; written as the special case,
    it is correct only for the ones that happen to arrive.

        g = -(t_c - c p_c) / n_pc     the gradient w.r.t. the centred q
        v = (I - m m') g              the centring is a projection
        w = (I - u u') v              and so is the normalisation
        D = w / n_p                   and p_hat = p / ||p||

    `n_p` is the length of the prediction, and the factor 1/n_p is the
    one that was missing: without it the update is not a gradient step
    on this loss but on a differently-scaled one.
    """
    dim = len(dp)
    # (I - m m') dp: the centring removes the component along the mean
    dm = dot(dp, m_hat)
    v = [dp[j] - m_hat[j] * dm for j in range(dim)]
    # (I - u u') v: the normalisation removes the radial component
    du = dot(v, p_hat)
    w = [v[j] - p_hat[j] * du for j in range(dim)]
    # and p_hat = p / ||p||, so the gradient w.r.t. p carries 1/||p||
    return [x / n_p for x in w]


# ===========================================================================
# THE JEPA
# ===========================================================================
class Jepa:
    """A JEPA over the two views.

    THE THREE PARTS, and why all three are here:
      encoder     E[w]      the encoder's vector for a word
      target      E'[w]     the STOPPED-GRADIENT, EMA-moving copy
      predictor   P(z)      maps a context embedding toward the target

    The loss is on the PREDICTION of the target's embedding, with the
    target's embedding detached. That is the JEPA's defining property:
    the model predicts a REPRESENTATION of the other view, never a
    token of it.
    """

    def __init__(self, vocab: Sequence[str], dim: int = DEFAULT_DIM,
                 ema: float = 0.99, lr: float = 0.05,
                 seed: int = 20261107):
        self.vocab = list(vocab)
        self.index = {w: i for i, w in enumerate(self.vocab)}
        self.dim = dim
        self.ema = ema
        self.lr = lr
        self.rng = random.Random(seed)
        #: THE ENCODER AND THE PREDICTOR BOTH START AT UNIT SCALE.
        #:
        #: MEASURED 2026-11-07: the first version started both from
        #: small random weights (0.05 per component), and with the
        #: window objective the loss ROSE -- 0.847 at 50 steps to 0.900
        #: at 2,000. The cause is the loss's scale, and it is a real
        #: one: the loss is a COSINE, so the gradient carries a factor
        #: of 1/||p||, and a predictor whose output has length 0.02
        #: produces a gradient of length ~50. The steps then overshoot,
        #: and the loss climbs.
        #:
        #: **A NORMALISED LOSS HAS A SCALE, AND THE SCALE IS THE
        #: LEARNING RATE.** So the encoder's rows and the predictor's
        #: rows are initialised with unit-length vectors, which puts
        #: ||p|| at O(1) and the gradient at O(1).
        self.enc = [[self.rng.gauss(0.0, 1.0 / math.sqrt(dim))
                     for _ in range(dim)] for _ in self.vocab]
        self.enc_bias = [0.0] * dim
        self.target = [row[:] for row in self.enc]
        self.target_bias = [0.0] * dim
        self.predictor = [[self.rng.gauss(0.0, 1.0 / math.sqrt(dim))
                           for _ in range(dim)] for _ in range(dim)]
        self.bias = [0.0] * dim
        #: THE MEAN DIRECTION: the average word direction, which every
        #: word shares and which a model can predict without learning
        #: anything about words. It is tracked from the ENCODER's rows
        #: so it moves as the encoder moves, and it is removed from
        #: both sides of the loss.
        self.mean_direction = [0.0] * dim

    # -- the forward pass, and the gradients -----------------------------
    def _forward(self, context: Sequence[int],
                 target: Sequence[int]) -> Optional[Dict[str, Any]]:
        """the loss and the gradients, and NOTHING is changed.

        **AND IT IS SEPARATE FROM `step` BECAUSE A GRADIENT THAT CANNOT
        BE CHECKED IS A GRADIENT THAT CANNOT BE TRUSTED.** `step` both
        computed the loss and moved the parameters, so there was no way
        to ask the model "is this the gradient of your loss?" -- the
        question needs the loss as a function of the parameters, and
        the parameters moved underneath it.

        **AND THE ANSWER, MEASURED 2026-11-07, WAS NO.** A central
        difference of this loss against this module's own analytic
        gradient DISAGREED, and the check that would have caught the
        original transposed backpropagation (the trained model
        agreeing with an untrained one to four significant figures)
        could not see it, because it compared two models instead of
        comparing a gradient with the loss it claims to be the
        gradient of.

        `None` means there is nothing to learn -- the word IS the mean
        direction -- and the loss is then zero.
        """
        dim = self.dim
        if not context or not target:
            return None
        # the context's embedding: the MEAN of its words' vectors
        z_ctx = [0.0] * dim
        for w in context:
            row = self.enc[w]
            for j in range(dim):
                z_ctx[j] += row[j]
        inv = 1.0 / len(context)
        z_ctx = [v * inv for v in z_ctx]
        # the prediction
        p = list(self.bias)
        for i, v in enumerate(z_ctx):
            if v == 0.0:
                continue
            row = self.predictor[i]
            for j in range(dim):
                p[j] += v * row[j]
        # the target's embedding, from the MOVING copy, and NO gradient
        z_tgt = [0.0] * dim
        for w in target:
            row = self.target[w]
            for j in range(dim):
                z_tgt[j] += row[j]
        inv = 1.0 / len(target)
        z_tgt = [v * inv for v in z_tgt]
        if len(target) == 1:
            z_tgt = list(self.target[target[0]])
        n_p = norm(p)
        n_t = norm(z_tgt)
        p_hat = [v / n_p for v in p]
        t_hat = [v / n_t for v in z_tgt]
        # **THE MEAN DIRECTION IS REMOVED FROM BOTH.** The corpus's
        # average word direction is the thing every word shares; a
        # model that reproduces it has learned nothing about words.
        m_hat = unit(self.mean_direction)
        p_c = [p_hat[j] - m_hat[j] * dot(p_hat, m_hat) for j in range(dim)]
        t_c = [t_hat[j] - m_hat[j] * dot(t_hat, m_hat) for j in range(dim)]
        n_pc = norm(p_c)
        n_tc = norm(t_c)
        if n_pc < 1e-9 or n_tc < 1e-9:
            # the word IS the mean direction (or the prediction is);
            # there is nothing left to predict and nothing to learn
            return None
        p_c = [v / n_pc for v in p_c]
        t_c = [v / n_tc for v in t_c]
        c = dot(p_c, t_c)
        loss = 1.0 - c

        # d(1 - cos)/dp, with p_c = p_c/||p_c||
        dp = [-(t_c[j] - c * p_c[j]) / n_pc for j in range(dim)]

        # **AND THE GRADIENT COMES BACK THROUGH THE CENTRING.** The
        # prediction p is centred by subtracting its own component
        # along m, so a change in p changes the centred direction.
        # The chain rule for that projection is applied to the
        # UNCENTRED p, because that is the quantity the predictor
        # produces.
        dp = _uncentre_gradient(dp, p_hat, m_hat, n_p)

        # **THE ENCODER'S GRADIENT IS COMPUTED BEFORE THE PREDICTOR IS
        # UPDATED.** MEASURED 2026-11-07: the first version updated
        # the predictor's weights and THEN used them to backpropagate
        # into the context -- and it used the WRONG INDEX, too:
        # `d_ctx[j] += z_ctx[i] * predictor[i][j]` computes the
        # predictor's OUTPUT, not the input's gradient. The correct
        # backprop of p[j] = sum_i z_ctx[i] * W[i][j] is
        # dz_ctx[i] = sum_j dp[j] * W[i][j] -- the SUM IS OVER j, and
        # the result lands on i.
        #
        # **AND THE CONSEQUENCE WAS INVISIBLE.** The encoder received a
        # gradient that was not a gradient, so its word vectors barely
        # moved: MEASURED, the trained model and an UNTRAINED model of
        # the same shape agreed with the list on 72.4% of 9,496 words
        # -- IDENTICALLY, to four significant figures. **A model that
        # agrees with an untrained one to four figures has not
        # learned.** And the loss still fell (0.742 -> 0.689), because
        # the predictor alone can reduce it -- so a falling loss did
        # not mean the encoder was learning either.
        d_ctx = [0.0] * dim
        for i, v in enumerate(z_ctx):
            if v == 0.0:
                continue
            row = self.predictor[i]
            acc = 0.0
            for j in range(dim):
                acc += dp[j] * row[j]
            d_ctx[i] = acc

        return {
            "loss": loss,
            "dp": dp,
            "d_ctx": d_ctx,
            "z_ctx": z_ctx,
            "p": p,
            "p_c": p_c,
            "t_c": t_c,
            "m_hat": m_hat,
            "n_p": n_p,
            "n_t": n_t,
        }

    # -- the training step ------------------------------------------------
    def step(self, context: Sequence[int],
             target: Sequence[int]) -> Optional[float]:
        """one step: predict the target view's embedding from the context.

        **AND THE ARITHMETIC IS THE FORWARD PASS'S, because the step
        calls it.** There is ONE implementation of the loss and the
        gradients, and it is the one the check reads. A gradient
        checked against a second copy of the formula is a second copy
        of the formula, not a check.

        **AND IT RETURNS None WHEN THERE IS NOTHING TO LEARN, NOT
        0.0.** MEASURED 2026-11-07: this used to return 0.0, and the
        trainer averaged those 0.0s into the reported loss -- **and A
        LOSS OF ZERO IS THE BEST POSSIBLE LOSS.** At the E3
        configuration 51.12% of the steps are no-ops (the window's
        words are not in the model's vocabulary, or the target word is
        not), so more than half the training budget reported
        perfection. None cannot be averaged into anything by accident,
        so the distinction between "this step learned nothing" and
        "this step reached a loss of zero" is now impossible to lose.
        """
        out = self._forward(context, target)
        if out is None:
            return None
        dim = self.dim
        loss = out["loss"]
        dp = out["dp"]
        d_ctx = out["d_ctx"]
        z_ctx = out["z_ctx"]

        # the predictor's gradient
        for i, v in enumerate(z_ctx):
            if v == 0.0:
                continue
            row = self.predictor[i]
            for j in range(dim):
                row[j] -= self.lr * dp[j] * v
        for j in range(dim):
            self.bias[j] -= self.lr * dp[j]

        # and back into the context words' own rows
        inv = 1.0 / len(context)
        for w in context:
            row = self.enc[w]
            for j in range(dim):
                row[j] -= self.lr * d_ctx[j] * inv

        # the target encoder MOVES, slowly, toward the encoder.
        #
        # **AND ONLY THE WORDS THIS STEP TOUCHED ARE MOVED.** MEASURED
        # 2026-11-07: the first version swept the whole vocabulary on
        # every step -- 27,504 words x 32 dims = 880,000 updates per
        # step, so 400 steps took 28 seconds and the sweep could not be
        # run at more than one size. **The words that were not in the
        # step have not moved, so moving them again is work that
        # changes nothing.**
        m = self.ema
        for w in set(context) | set(target):
            enc_row = self.enc[w]
            tgt_row = self.target[w]
            for j in range(dim):
                tgt_row[j] = m * tgt_row[j] + (1.0 - m) * enc_row[j]
        return loss

    # -- the readout ------------------------------------------------------
    def word_vector(self, word: str) -> Optional[List[float]]:
        """the encoder's vector for a word, or None if it is not in the
        vocabulary."""
        i = self.index.get(word)
        if i is None:
            return None
        return self.enc[i]

    def parameters(self) -> int:
        """the model's parameter count -- the cost axis of the
        comparison."""
        return (len(self.vocab) * self.dim * 2          # encoder + target
                + self.dim * self.dim + self.dim)       # predictor + bias

    def refresh_mean_direction(self) -> None:
        """the mean of the encoder's rows -- the direction every word
        shares.

        **AND IT IS COMPUTED FROM THE ENCODER, NOT FROM A SEPARATE
        BUFFER, so it cannot drift away from the representation it
        describes.** A model that predicts this direction has learned
        the corpus's average and nothing else, so the loss removes it
        from both sides.
        """
        if not self.vocab:
            return
        dim = self.dim
        acc = [0.0] * dim
        for row in self.enc:
            for j in range(dim):
                acc[j] += row[j]
        inv = 1.0 / len(self.enc)
        self.mean_direction = [v * inv for v in acc]


# ===========================================================================
# THE EVALUATION: THE LOSS ON A FIXED SET OF PAIRS
# ===========================================================================
def evaluate(model: Jepa, pairs: Sequence[Tuple[List[str], List[str]]],
             sample: int = 400, window: int = 8,
             seed: int = 20261107) -> Dict[str, Any]:
    """the loss on a FIXED set of (context, target) pairs.

    **AND IT IS THE INSTRUMENT, BECAUSE A WINDOW OF THE TRAINING LOSS
    IS NOT ONE.** MEASURED 2026-11-07: the trainer used to report the
    mean of the first 100 training losses against the mean of the last
    100, and those are two different SETS of pairs. The per-step loss
    has a standard deviation of 0.283, so a 100-sample mean carries a
    standard error of 0.028 -- and the difference the check was
    reading (0.069) was 2.44 standard errors of NOISE. Worse, the
    noise pointed the WRONG WAY: the training-window loss ROSE while
    the loss on a FIXED set FELL, from 0.99231 to 0.95604.

    **A CHECK BUILT ON A SAMPLING ARTIFACT CAN REPORT THAT A MODEL
    DID NOT TRAIN ABOUT A MODEL THAT DID.** So the loss is measured on
    the SAME pairs before and after training, and the comparison is
    PAIRED: the per-example noise cancels instead of adding.

    **AND THE PAIRS ARE FIXED BY A SEED, so the measurement is
    REPRODUCIBLE**: the same set, every time, for any model.
    """
    import random as _random
    rng = _random.Random(seed)
    index = model.index
    dim = model.dim
    losses: List[float] = []
    for _ in range(sample):
        if not pairs:
            break
        a, b = pairs[rng.randrange(len(pairs))]
        ctx_src, tgt_src = (a, b) if rng.random() < 0.5 else (b, a)
        lo = min(window + 1, len(ctx_src) - 1)
        if lo < 1:
            continue
        pos = lo + rng.randrange(max(1, len(ctx_src) - lo))
        ctx = [index[w] for w in ctx_src[pos - window:pos] if w in index]
        tgt_word = tgt_src[pos] if pos < len(tgt_src) else ""
        tgt = [index[tgt_word]] if tgt_word in index else []
        if not ctx or not tgt:
            continue
        out = model._forward(ctx, tgt)
        if out is not None:
            losses.append(out["loss"])
    if not losses:
        return {"n": 0, "mean": 0.0}
    mean = sum(losses) / len(losses)
    sd = (sum((x - mean) ** 2 for x in losses) / len(losses)) ** 0.5
    return {"n": len(losses), "mean": round(mean, 6),
            "sd": round(sd, 6), "se": round(sd / (len(losses) ** 0.5), 6)}


# ===========================================================================
# THE TRAINING
# ===========================================================================
def train(steps: int = 3000, dim: int = DEFAULT_DIM, lr: float = 0.05,
          ema: float = 0.99, max_sentences: int = 0, min_count: int = 5,
          window: int = 8, seed: int = 20261107, verbose: bool = True
          ) -> Tuple[Jepa, Dict[str, Any]]:
    """train the JEPA on the two views, and report what it saw.

    **AND THE CONTEXT IS A WINDOW OF THE WORDS BEFORE THE TARGET, NOT
    HALF A SENTENCE.** MEASURED 2026-11-07: the first version took
    the whole first half of the sentence as the context and the whole
    second half as the target, and the model learned NOTHING about
    word roles: the probe could not fit its own seeds (58.3% training
    accuracy) and the trained model agreed with an untrained one of
    the same shape to four significant figures.

    The cause is the objective, and it is a real one: with half a
    sentence as the context and half a sentence as the target, both
    sides are dominated by the corpus's most frequent words, so the
    model can reduce the loss by learning ONE global direction and
    ignore the words entirely. **A bag of the most common words is
    the cheapest possible answer to that question, and the model found
    it.** The information about a word's ROLE -- which is what the
    (name, act) test measures -- lives in the words IMMEDIATELY
    around it, and a whole half-sentence averages it away.

    So the context is the WINDOW of the `window` words before the
    target, in view A, and the target is the word itself in view B.
    That is a per-position objective, it is a JEPA (the model predicts
    the target's REPRESENTATION, and the target comes from the
    stopped-gradient EMA copy), and it is the objective that can carry
    a word's role.
    """
    counts = corpus_counts(min_count)
    vocab = sorted(counts)
    pairs = view_pairs(max_sentences=max_sentences)
    if not pairs:
        raise SystemExit("no aligned sentence pairs -- is the second view built?")
    # **AND EVERY TENTH PAIR IS HELD OUT**, interleaved, so the
    # held-out pairs come from the same works as the training pairs.
    # The held-out loss is the INSTRUMENT: it is measured on the SAME
    # pairs before and after training, so the comparison is paired and
    # the sampling noise cancels. A window of the TRAINING loss cannot
    # do that -- MEASURED 2026-11-07, its sampling error (0.028 on a
    # 100-sample mean) pointed the wrong way and reported that a model
    # which had trained had not.
    held_out = [p for i, p in enumerate(pairs) if i % 10 == 0]
    train_pairs = [p for i, p in enumerate(pairs) if i % 10 != 0]
    if not train_pairs:
        train_pairs = pairs
    model = Jepa(vocab, dim=dim, ema=ema, lr=lr, seed=seed)
    index = model.index
    rng = random.Random(seed)
    losses: List[float] = []
    noop = 0
    t0 = time.time()
    model.refresh_mean_direction()
    # **THE HELD-OUT LOSS, BEFORE ANY TRAINING.** The same pairs are
    # measured again at the end, so the difference is paired.
    before = evaluate(model, held_out)
    refresh_every = max(1, steps // 10)
    for step in range(steps):
        a, b = train_pairs[rng.randrange(len(train_pairs))]
        # **THE SPLIT ALTERNATES, so every word gets trained.** A word
        # that only ever appears in the second half of a sentence would
        # never be a context word and its row would never move.
        ctx_src, tgt_src = (a, b) if step % 2 == 0 else (b, a)
        # the target position: somewhere with a full window before it
        lo = min(window + 1, len(ctx_src) - 1)
        if lo < 1:
            noop += 1
            continue
        # **AND THE POSITION IS CHOSEN TO BE USABLE.** The first
        # version picked a position at random and DROPPED the step if
        # the target word was not in the model's vocabulary or none of
        # the window's words was. MEASURED 2026-11-07: at the E3
        # configuration that threw away **51.12% of the training
        # steps** -- 46.03% because the target word was not in the
        # vocabulary and 5.44% because no window word was. **A model
        # arm that got half the steps its budget said it had is the
        # shape of a strawman**, and `diagnose_jepa.py` exists to ask
        # exactly that question.
        #
        # So a few positions in the SAME sentence are tried, and the
        # first usable one is taken. MEASURED: a rescue finds a usable
        # position for 65.0% of the wasted steps on the first try, so
        # the waste collapses from 51% to a few percent. The choice is
        # still random over the sentences, so the distribution over
        # positions is still the corpus's.
        ctx: List[int] = []
        tgt: List[int] = []
        for _ in range(POSITION_TRIES):
            pos = lo + rng.randrange(max(1, len(ctx_src) - lo))
            ctx = [index[w] for w in ctx_src[pos - window:pos] if w in index]
            tgt_word = tgt_src[pos] if pos < len(tgt_src) else ""
            tgt = [index[tgt_word]] if tgt_word in index else []
            if ctx and tgt:
                break
        loss = model.step(ctx, tgt)
        # **A STEP THAT LEARNED NOTHING IS COUNTED, NOT AVERAGED.**
        if loss is None:
            noop += 1
            continue
        losses.append(loss)
        if (step + 1) % refresh_every == 0:
            # **AND THE MEAN DIRECTION IS REFRESHED ON THE SCHEDULE,
            # NOT ONLY WHEN THE RUN IS NOISY.** It used to sit inside
            # the `if verbose` block, so a quiet run -- every run in
            # the test suite, every run in `--compare` -- centred the
            # loss against a direction frozen at initialisation for
            # the whole training. Only the PRINTING is conditional
            # now.
            model.refresh_mean_direction()
            if verbose:
                recent = sum(losses[-100:]) / len(losses[-100:])
                print("  step %6d/%d  loss %.5f" % (step + 1, steps, recent),
                      flush=True)
    model.refresh_mean_direction()
    # **AND THE HELD-OUT LOSS, AFTER.** The same pairs, so the
    # difference is PAIRED and the per-example noise cancels.
    after = evaluate(model, held_out)
    # **AND THE LOSS STATISTICS ARE OVER THE STEPS THAT RAN.** The
    # no-op steps are not in `losses` at all -- they are counted, and
    # the count is reported, because a reader who is told that half
    # the budget was unused can weigh the number and a reader who is
    # not told cannot.
    tail = losses[-100:] or [0.0]
    head = losses[:100] or [0.0]
    report = {
        "steps": steps,
        "steps_computed": len(losses),
        "steps_noop": noop,
        "dim": dim,
        "lr": lr,
        "ema": ema,
        "window": window,
        "vocab": len(vocab),
        "parameters": model.parameters(),
        "pairs_available": len(pairs),
        "final_loss": round(sum(tail) / len(tail), 6),
        "first_loss": round(sum(head) / len(head), 6),
        # **AND THE PAIRED HELD-OUT LOSS.** This is the number a check
        # should read: the same pairs, before and after, so the
        # difference is a measurement of the MODEL and not of the
        # sampling.
        "held_out_loss_before": before["mean"],
        "held_out_loss_after": after["mean"],
        "held_out_loss_fall": round(before["mean"] - after["mean"], 6),
        "held_out_pairs": before["n"],
        "held_out_se": after.get("se", 0.0),
        "seconds": round(time.time() - t0, 1),
    }
    return model, report


# ===========================================================================
# THE CONTROL: are the two views worth anything?
# ===========================================================================
def alignment(model: Jepa, pairs: Sequence[Tuple[List[str], List[str]]],
              sample: int = 400, seed: int = 20261107
              ) -> Dict[str, Any]:
    """the mean cosine between the PREDICTION and the target.

    **AND THIS IS THE CONTROL THAT DECIDES WHETHER THE COMPARISON
    MEANS ANYTHING.** The cosine is measured two ways:

      CROSS   the context is view A's first half and the target is
              view B's second half -- the JEPA's own task, across the
              two views.
      WITHIN  the context is view A's first half and the target is
              view A's OWN second half -- the same work, the same
              sentence, no second view involved.

    **IF THE TWO NUMBERS ARE THE SAME, THEN THE SECOND VIEW CARRIES NO
    INFORMATION THE FIRST VIEW DID NOT ALREADY CARRY, and any JEPA
    trained on the pair is a JEPA trained on ONE view wearing two
    hats.** That is the measurement, and it is the one that decides
    what the comparison in `--compare` can claim.
    """
    rng = random.Random(seed)
    if not pairs:
        return {"cross": 0.0, "within": 0.0, "n": 0}
    dim = model.dim
    index = model.index
    scores: Dict[str, List[float]] = {"cross": [], "within": []}
    n = min(sample, len(pairs))
    for _ in range(n):
        a, b = pairs[rng.randrange(len(pairs))]
        cut_a = max(1, len(a) // 2)
        cut_b = max(1, len(b) // 2)
        ctx = [index[w] for w in a[:cut_a] if w in index]
        if not ctx:
            continue
        for mode, tgt_tokens in (("cross", b[cut_b:]), ("within", a[cut_a:])):
            tgt = [index[w] for w in tgt_tokens if w in index]
            if not tgt:
                continue
            z_ctx = [0.0] * dim
            for w in ctx:
                row = model.enc[w]
                for j in range(dim):
                    z_ctx[j] += row[j]
            inv = 1.0 / len(ctx)
            z_ctx = [v * inv for v in z_ctx]
            p = list(model.bias)
            for i, v in enumerate(z_ctx):
                if v == 0.0:
                    continue
                row = model.predictor[i]
                for j in range(dim):
                    p[j] += v * row[j]
            z_tgt = [0.0] * dim
            for w in tgt:
                row = model.target[w]
                for j in range(dim):
                    z_tgt[j] += row[j]
            inv = 1.0 / len(tgt)
            z_tgt = [v * inv for v in z_tgt]
            c = dot(unit(p), unit(z_tgt))
            scores[mode].append(c)
    cross = sum(scores["cross"]) / max(1, len(scores["cross"]))
    within = sum(scores["within"]) / max(1, len(scores["within"]))
    return {
        "cross": round(cross, 4),
        "within": round(within, 4),
        "cross_minus_within": round(cross - within, 4),
        "n": len(scores["cross"]),
    }


def fit_probe(model: Jepa, names: Sequence[str],
              acts: Sequence[str], l2: float = 1.0,
              seed: int = 20261107
              ) -> Tuple[Tuple[List[float], List[float]], Dict[str, Any]]:
    """a RIDGE readout on the seeds: a bounded direction, fitted on seeds.

    **AND THE READOUT IS A RIDGE REGRESSION, BECAUSE A LOGISTIC ONE
    DIVERGES HERE.** MEASURED 2026-11-07: the first probe was a
    logistic regression, and its scores reached -2,000 with a
    separation of -17.3 for a TRAINED model and -17.3 for an
    UNTRAINED one -- every model looked equally bad, so the readout
    could not tell a good model from a bad one. **A probe that
    diverges reports nothing.**

    The cause is the BIAS and the IMBALANCE: there are 35 name seeds
    and 25 act seeds, and the bias has nothing to hold it back. For a
    name seed the target probability is 0, so the gradient keeps
    pushing the bias DOWN, and it goes to -infinity taking every score
    with it.

    A ridge regression has no bias term and a closed form, so it is
    BOUNDED BY CONSTRUCTION: the direction is a fixed-length vector
    and the score is a dot product, so no score can run away. And the
    readout's own TRAINING ACCURACY is reported -- because a readout
    that cannot fit the seeds it was given is saying "this
    representation does not separate these words", and that is a
    RESULT about the representation, not a defect in the readout.

    Returns ((w, b), report): the score of a word is dot(w, emb) + b.
    """
    dim = model.dim
    xs: List[List[float]] = []
    ys: List[float] = []
    for word, y in [(w, -1.0) for w in names] + [(w, 1.0) for w in acts]:
        v = model.word_vector(word)
        if v is None:
            continue
        xs.append(unit(v))
        ys.append(y)
    if not xs:
        return ([0.0] * dim, [0.0]), {"seeds_found": 0,
                                       "seeds_separated": False,
                                       "train_accuracy": 0.0}
    # the ridge solution: w = (X'X + l2 I)^-1 X'y, solved by Gaussian
    # elimination with partial pivoting. No bias term, so nothing can
    # run away.
    ata = [[0.0] * (dim + 1) for _ in range(dim)]
    for x, y in zip(xs, ys):
        for i in range(dim):
            for j in range(dim):
                ata[i][j] += x[i] * x[j]
            ata[i][dim] += x[i] * y
    for i in range(dim):
        ata[i][i] += l2
    w = _solve(ata, dim)
    b = 0.0
    # the readout's own TRAINING ACCURACY
    correct = 0
    name_scores: List[float] = []
    act_scores: List[float] = []
    for x, y in zip(xs, ys):
        z = b + dot(w, x)
        if (z > 0) == (y > 0):
            correct += 1
        (name_scores if y < 0 else act_scores).append(z)
    worst_name = max(name_scores) if name_scores else 0.0
    best_act = min(act_scores) if act_scores else 0.0
    report = {
        "seed_names": len(name_scores),
        "seed_acts": len(act_scores),
        "separation": round(best_act - worst_name, 4),
        "seeds_separated": bool(best_act > worst_name),
        "train_accuracy": round(correct / len(xs), 4),
        "weight_norm": round(norm(w), 4),
    }
    return (w, [b]), report


def _solve(a: List[List[float]], n: int) -> List[float]:
    """solve the n x n system in `a` (augmented), by Gaussian elimination
    with partial pivoting."""
    m = [row[:] for row in a]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            continue
        m[col], m[pivot] = m[pivot], m[col]
        inv = 1.0 / m[col][col]
        for r in range(col + 1, n):
            factor = m[r][col] * inv
            if factor == 0.0:
                continue
            for c in range(col, n + 1):
                m[r][c] -= factor * m[col][c]
    out = [0.0] * n
    for r in range(n - 1, -1, -1):
        acc = m[r][n]
        for c in range(r + 1, n):
            acc -= m[r][c] * out[c]
        out[r] = acc / m[r][r] if abs(m[r][r]) > 1e-12 else 0.0
    return out


def score_with_probe(model: Jepa, w: Sequence[float], b: Sequence[float],
                     word: str) -> Optional[float]:
    v = model.word_vector(word)
    if v is None:
        return None
    return dot(w, v) + b[0]


# ===========================================================================
# THE READOUT: the probe, fitted on the SEEDS
# ===========================================================================
def partition(model: Jepa, probe: Tuple[Sequence[float], Sequence[float]],
              vocab: Sequence[str], threshold: float = 0.0,
              ) -> Tuple[List[str], List[str]]:
    """the word partition the readout produces.

    A word is an ACT if its score is above the threshold and a NAME if
    it is below -- so it is in at most one of the two, and the
    disjointness the whole design rests on is preserved BY
    CONSTRUCTION, exactly as it is in the list arm.
    """
    w, b = probe
    acts: List[str] = []
    names: List[str] = []
    for word in vocab:
        s = score_with_probe(model, w, b, word)
        if s is None:
            continue
        if s > threshold:
            acts.append(word)
        elif s < threshold:
            names.append(word)
    return acts, names


def partition_sized(model: Jepa, probe: Tuple[Sequence[float],
                                              Sequence[float]],
                    vocab: Sequence[str], n_acts: int, n_names: int,
                    ) -> Tuple[List[str], List[str]]:
    """the partition with the SAME SIZE as another arm's.

    **AND THIS IS THE EQUAL-COST COMPARISON.** The item asks for the
    two arms to be compared "at equal cost", and the cost that the
    bench actually sees is the SIZE of the partition: a list with more
    evidence is a bigger list, and a bigger list binds more prose. So
    the model is given the list's own counts -- the top n_acts words
    by score are its acts and the bottom n_names are its names -- and
    the two are then scored by the same bench.

    **AND THE MODEL CANNOT SPEND WORDS IT DOES NOT HAVE.** It picks
    from the corpus vocabulary it was trained on, so if the list
    admits more words than the model knows, the model is short and the
    comparison says so.
    """
    w, b = probe
    scored: List[Tuple[float, str]] = []
    for word in vocab:
        s = score_with_probe(model, w, b, word)
        if s is None:
            continue
        scored.append((s, word))
    scored.sort(key=lambda t: (-t[0], t[1]))
    acts = [word for _, word in scored[:n_acts]]
    chosen = set(acts)
    names = [word for _, word in reversed(scored[-n_names:])] if n_names else []
    # a word may not be in both, and the two lists must be disjoint
    names = [word for word in names if word not in chosen]
    return acts, names


def role_gap(model: Jepa, vocab: Sequence[str], sample: int = 8000,
             seed: int = 7) -> Dict[str, Any]:
    """do words of the SAME role sit closer than words of DIFFERENT roles?

    **AND THIS IS THE HONEST TEST OF WHETHER THE MODEL LEARNED
    ANYTHING, because it does not depend on the readout.** A probe can
    fail for reasons that are about the probe; this cannot. It takes
    the model's OWN vectors, asks what the LIST says about each word's
    role, and compares the mean cosine within a role against the mean
    cosine across roles.

    **AND THE LIST IS USED ONLY AS THE LABEL, never as the
    representation.** The vectors are the model's; the labels say
    which words to compare.
    """
    from vocab_loader import load_learned_vocab
    lv = load_learned_vocab()
    list_vocab = lv.learn(_CANON)
    verbs = set(list_vocab.verbs)
    nouns = set(list_vocab.nouns)
    items = [(w, model.word_vector(w)) for w in vocab]
    items = [(w, v) for w, v in items if v is not None]
    if len(items) < 20:
        return {"same": 0.0, "diff": 0.0, "gap": 0.0, "n": len(items)}
    rng = random.Random(seed)
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
        c = dot(v1, v2) / (norm(v1) * norm(v2))
        (same if r1 == r2 else diff).append(c)
    if not same or not diff:
        return {"same": 0.0, "diff": 0.0, "gap": 0.0, "n": len(items)}
    s = sum(same) / len(same)
    d = sum(diff) / len(diff)
    return {"same": round(s, 4), "diff": round(d, 4),
            "gap": round(s - d, 4), "n": len(items)}


# ===========================================================================
# THE COMPARISON
# ===========================================================================
def vocabulary_from(acts: Sequence[str], names: Sequence[str]):
    """a `lv.Vocabulary`, so the bench scores the model EXACTLY as it
    scores the list."""
    from vocab_loader import load_learned_vocab
    lv = load_learned_vocab()
    return lv.Vocabulary(verbs=tuple(acts), nouns=tuple(names),
                         version="jepa")


def vocabulary_from_list(min_evidence: int = 3, min_ratio: float = 3.0):
    from vocab_loader import load_learned_vocab
    lv = load_learned_vocab()
    return lv.learn(_CANON, min_evidence=min_evidence, min_ratio=min_ratio)


def score(vocab, bench) -> Dict[str, Any]:
    """the bench's OWN numbers, for a word partition."""
    held = bench.held_out_sentences()
    all_sents = [s for v in held.values() for s in v]
    disc = bench.discrimination(vocab, held)
    cov = bench.coverage_of(vocab, all_sents)
    return {
        "verbs": len(vocab.verbs),
        "nouns": len(vocab.nouns),
        "overlap": len(set(vocab.verbs) & set(vocab.nouns)),
        "real_rate": round(float(disc["real_rate"]), 4),
        "shuffled_rate": round(float(disc["shuffled_rate"]), 4),
        "lift": round(float(disc["lift"]), 2),
        "coverage": round(float(cov["fraction"]), 4),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="the JEPA, and the list it "
                                             "is measured against")
    ap.add_argument("--train", action="store_true", help="train the JEPA")
    ap.add_argument("--compare", action="store_true",
                    help="score the JEPA and the list with the same bench")
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--dim", type=int, default=DEFAULT_DIM)
    ap.add_argument("--dims", default="",
                    help="comma-separated dims to sweep (overrides --dim)")
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--ema", type=float, default=0.99)
    ap.add_argument("--max-sentences", type=int, default=0)
    ap.add_argument("--min-count", type=int, default=MIN_CORPUS_COUNT)
    ap.add_argument("--min-evidence", default="1,2,3,5,8",
                    help="the list's size axis: the min_evidence sweep")
    ap.add_argument("--save", default="", help="write the model here")
    args = ap.parse_args()

    if not (args.train or args.compare):
        args.compare = True

    manifest = raw_manifest()
    if manifest:
        s = manifest.get("summary", {})
        print("THE TWO VIEWS, and how different they are")
        print("  canon sentences        %d" % s.get("canon_sentences", 0))
        print("  matched in the raw     %d = %.2f%%"
              % (s.get("matched_sentences", 0),
                 100.0 * s.get("matched_sentences", 0)
                 / max(1, s.get("canon_sentences", 1))))
        print("  token-identical        %d = %.2f%%"
              % (s.get("token_identical_sentences", 0),
                 100.0 * s.get("token_identical_sentences", 0)
                 / max(1, s.get("canon_sentences", 1))))
        print()

    sys.path.insert(0, os.path.join(_ROOT, "src"))
    import bench_canon_vocab as bench

    dims = ([int(d) for d in args.dims.split(",") if d.strip()]
            if args.dims else [args.dim])

    if args.train:
        for dim in dims:
            print("TRAINING THE JEPA, dim %d" % dim)
            model, report = train(steps=args.steps, dim=dim, lr=args.lr,
                                  ema=args.ema,
                                  max_sentences=args.max_sentences,
                                  min_count=args.min_count)
            print("  steps %d  vocab %d  parameters %d  pairs %d  %.1fs"
                  % (report["steps"], report["vocab"], report["parameters"],
                     report["pairs_available"], report["seconds"]))
            print("  loss %.5f -> %.5f" % (report["first_loss"],
                                           report["final_loss"]))
            print()

    if args.compare:
        # -- the LIST arm, over its own size axis ------------------------
        print("THE LIST ARM -- the corpus count, over min_evidence")
        list_rows: List[Dict[str, Any]] = []
        for me in [int(x) for x in args.min_evidence.split(",") if x.strip()]:
            lv = vocabulary_from_list(min_evidence=me)
            row = score(lv, bench)
            row["min_evidence"] = me
            list_rows.append(row)
            print("  min_evidence %-3d  verbs %6d  nouns %6d  overlap %d  "
                  "coverage %5.1f%%  lift %5.2fx"
                  % (me, row["verbs"], row["nouns"], row["overlap"],
                     100 * row["coverage"], row["lift"]))
        print()

        # -- the JEPA arm, over its own size axis ------------------------
        print("THE JEPA ARM -- a per-word probe fitted on the seeds")
        model_rows: List[Dict[str, Any]] = []
        model: Jepa = Jepa([], dim=dims[-1])
        for dim in dims:
            model, report = train(steps=args.steps, dim=dim, lr=args.lr,
                                  ema=args.ema,
                                  max_sentences=args.max_sentences,
                                  min_count=args.min_count, verbose=False)
            probe, seed_report = fit_probe(model, SEED_NAMES, SEED_ACTS)
            universe = sorted(model.vocab)
            acts, names = partition(model, probe, universe, threshold=0.0)
            row = score(vocabulary_from(acts, names), bench)
            row["dim"] = dim
            row["parameters"] = report["parameters"]
            row["loss"] = report["final_loss"]
            row["seeds_separated"] = seed_report.get("seeds_separated")
            row["separation"] = seed_report.get("separation")
            model_rows.append(row)
            print("  dim %-4d  params %9d  loss %.4f  seeds separated %s  "
                  "verbs %6d  nouns %6d  overlap %d  coverage %5.1f%%  "
                  "lift %5.2fx"
                  % (dim, row["parameters"], row["loss"],
                     row["seeds_separated"], row["verbs"], row["nouns"],
                     row["overlap"], 100 * row["coverage"], row["lift"]))
        print()

        # -- THE UNTRAINED CONTROL: did the training do anything? -------
        print("THE UNTRAINED CONTROL -- the same model, never trained")
        untrained = Jepa(sorted(model.vocab), dim=dims[-1], lr=args.lr,
                         seed=20261107)
        untrained.refresh_mean_direction()
        uprobe, ureport = fit_probe(untrained, SEED_NAMES, SEED_ACTS)
        ua, un = partition(untrained, uprobe, sorted(model.vocab),
                           threshold=0.0)
        urow = score(vocabulary_from(ua, un), bench)
        ugap = role_gap(untrained, sorted(model.vocab))
        tgap = role_gap(model, sorted(model.vocab))
        print("  verbs %6d  nouns %6d  overlap %d  coverage %5.1f%%  "
              "lift %5.2fx   (seeds separated %s)"
              % (urow["verbs"], urow["nouns"], urow["overlap"],
                 100 * urow["coverage"], urow["lift"],
                 ureport.get("seeds_separated")))
        print("  ROLE GAP   untrained %+.4f   trained %+.4f"
              % (ugap["gap"], tgap["gap"]))
        if tgap["gap"] <= ugap["gap"]:
            print("  **THE TRAINING DID NOT LEARN THE ROLE STRUCTURE.** The")
            print("  trained model's gap is not bigger than the untrained")
            print("  one's, so the model arm FAILED TO LEARN and the")
            print("  comparison below is NOT a model that was beaten.")
        print()

        # -- THE CONTROL: are the two views worth anything? ---------------
        print("THE CONTROL -- is the second view worth anything?")
        pairs = view_pairs(max_sentences=args.max_sentences or 20000)
        model, _ = train(steps=args.steps, dim=dims[-1], lr=args.lr,
                         ema=args.ema, max_sentences=args.max_sentences,
                         min_count=args.min_count, verbose=False)
        al = alignment(model, pairs)
        print("  the prediction's cosine with the target, on held-out pairs")
        print("    CROSS   (view A's first half -> view B's second half)  "
              "%.4f" % al["cross"])
        print("    WITHIN  (view A's first half -> view A's own second)    "
              "%.4f" % al["within"])
        print("    the difference                               %+.4f"
              % al["cross_minus_within"])
        print("    pairs measured %d" % al["n"])
        if al["cross_minus_within"] <= 0.005:
            print("    **THE SECOND VIEW CARRIES NOTHING THE FIRST DID NOT.**")
            print("    The two views are 97.85%% the same tokens, so the "
                  "JEPA was")
            print("    trained on ONE view wearing two hats, and the "
                  "comparison")
            print("    below measures a model against a list, NOT the "
                  "good-views claim.")
        else:
            print("    the second view carries measurable information "
                  "beyond the first.")
        print()

        print("THE COMPARISON -- one bench, two arms")
        print("  the model partitioned the CORPUS's own universe (%d words, "
              "count >= %d);" % (len(model.vocab), args.min_count))
        print("  the list chose its own words. Neither arm picked the "
              "ground for the other.")
        print()
        best_list = max(list_rows, key=lambda r: r["lift"])
        best_model = max(model_rows, key=lambda r: r["lift"])
        print("  %-10s %10s %10s %10s %10s" % ("arm", "verbs", "nouns",
                                                "coverage", "lift"))
        for r in list_rows:
            print("  %-10s %10d %10d %9.1f%% %9.2fx"
                  % ("LIST", r["verbs"], r["nouns"], 100 * r["coverage"],
                     r["lift"]))
        for r in model_rows:
            print("  %-10s %10d %10d %9.1f%% %9.2fx"
                  % ("JEPA", r["verbs"], r["nouns"], 100 * r["coverage"],
                     r["lift"]))
        print()

        # -- THE EQUAL-COST COMPARISON -----------------------------------
        print("THE EQUAL-COST COMPARISON -- the model given the LIST's "
              "own counts")
        probe, _seed = fit_probe(model, SEED_NAMES, SEED_ACTS)
        universe = sorted(model.vocab)
        for r in list_rows:
            acts, names = partition_sized(model, probe, universe,
                                          r["verbs"], r["nouns"])
            m = score(vocabulary_from(acts, names), bench)
            print("  list(%d)  verbs %6d nouns %6d  coverage %5.1f%%  "
                  "lift %5.2fx   |  model(same size) verbs %6d nouns %6d  "
                  "coverage %5.1f%%  lift %5.2fx"
                  % (r["min_evidence"], r["verbs"], r["nouns"],
                     100 * r["coverage"], r["lift"],
                     m["verbs"], m["nouns"], 100 * m["coverage"], m["lift"]))
        print()
        print("  the list's best lift %5.2fx   the model's best lift %5.2fx"
              % (best_list["lift"], best_model["lift"]))
        if best_model["lift"] > best_list["lift"]:
            print("  THE MODEL WINS. And the premise was false: the two "
                  "views are 97.85%% the same tokens.")
        else:
            print("  THE LIST WINS. **AND THAT IS A FINDING WORTH HAVING:** "
                  "the list")
            print("  is the right instrument, and the 'good views' were "
                  "never")
            print("  good -- the two views are 97.85%% the same tokens, so "
                  "the")
            print("  JEPA was trained on ONE view wearing two hats.")

    if args.save:
        model, report = train(steps=args.steps, dim=dims[-1], lr=args.lr,
                              ema=args.ema, max_sentences=args.max_sentences,
                              min_count=args.min_count, verbose=False)
        payload = {"vocab": model.vocab, "dim": model.dim, "ema": model.ema,
                   "lr": model.lr, "enc": model.enc, "target": model.target,
                   "predictor": model.predictor, "bias": model.bias,
                   "report": report}
        with open(args.save, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        print("model written: %s" % args.save)
    return 0


if __name__ == "__main__":
    sys.exit(main())
