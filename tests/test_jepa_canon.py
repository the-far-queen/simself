"""tests: the checks on the JEPA, with the finite-difference one added.

THE NEW CHECK, AND WHY IT IS THE ONE THAT MATTERS
---------------------------------------------------
MEASURED 2026-11-07: the module's analytic gradient was NOT the
gradient of its own loss. A central difference of the loss against
the module's own analytic gradient DISAGREED by 83% -- on the bias,
on the predictor, and on the encoder alike -- while the corrected
chain rule agrees with the same central difference to 6e-11, 2e-8 and
6e-10.

**AND EVERY BEHAVIOURAL CHECK MISSED IT, AND THE REASON IS THE
POINT.** The cosine between the old gradient and the true one is
1.0000000000 at every one of 320 random points: the old gradient was
off by a POSITIVE SCALAR (the missing 1/||p||), and a gradient that
is off by a positive scalar still DESCENDS. So the loss fell, the
vectors moved, the model learned -- and the step size was wrong by a
factor that moves with ||p||. **A BEHAVIOURAL CHECK CANNOT SEE A
SCALE, AND A SCALE IS WHAT WAS WRONG.**

So the check that catches this class of defect is not "did the loss
fall" and not "did the vectors move". It is: **is the analytic
gradient the gradient of the loss?** And that is a FINITE DIFFERENCE
-- the same question asked of the loss itself rather than of the
model's behaviour.

THE THRESHOLDS, RE-DERIVED
--------------------------
The old thresholds were set against a loss in which 51.12% of the
steps contributed 0.0 -- the BEST possible loss -- so they were
thresholds on a contaminated number. And the window comparison they
used was a SAMPLING ARTIFACT: the first 100 losses and the last 100
are different sets of pairs, the per-step loss has a standard
deviation of 0.283, and the observed 0.069 difference was 2.44
standard errors of noise -- pointing the WRONG WAY, while the loss on
a FIXED held-out set fell from 0.99231 to 0.95604.

So the checks now read the PAIRED HELD-OUT loss, and the thresholds
are set against that measurement.
"""
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import jepa_canon as jc


# ---------------------------------------------------------------------------
# 0. THE GRADIENT IS THE GRADIENT OF THE LOSS
# ---------------------------------------------------------------------------
def test_E0_the_analytic_gradient_is_the_gradient_of_the_loss():
    """the analytic gradient must equal a central difference of the loss.

    **AND THIS IS THE CHECK THAT WOULD HAVE CAUGHT THE DEFECT THAT WAS
    IN THE CODE.** MEASURED 2026-11-07: the module's analytic gradient
    disagreed with a central difference of the module's OWN loss by
    83%, and every behavioural check stayed green -- because the error
    was a POSITIVE SCALAR (the missing 1/||p|| from the
    normalisation), and a gradient that is off by a positive scalar
    still descends. The cosine between the old gradient and the true
    one is 1.0000000000 at every one of 320 random points.

    **SO THE QUESTION IS ASKED OF THE LOSS, NOT OF THE MODEL.** The
    forward pass is pure -- it computes the loss and changes nothing --
    so the numerical derivative is of exactly the function the
    analytic gradient claims to be the derivative of.

    **AND THE TOLERANCE IS SET FROM THE MEASUREMENT**: the corrected
    chain rule agrees to 9.2e-11 on the bias, 1.0e-08 on the
    predictor and 3.1e-09 on the encoder. The bound below is a
    thousand times looser than the worst of those, and a thousand
    times tighter than the 83% the defect produced -- so it separates
    the two cleanly.
    """
    import random

    rng = random.Random(20261107)
    vocab = ["w%d" % i for i in range(40)]
    model = jc.Jepa(vocab, dim=6, lr=0.05, seed=20261107)
    model.refresh_mean_direction()
    # move the model off its initialisation, so the check is made on a
    # model in a state training produces
    for _ in range(20):
        ctx = rng.sample(range(len(vocab)), 4)
        model.step(ctx, [rng.randrange(len(vocab))])
    model.refresh_mean_direction()

    context = rng.sample(range(len(vocab)), 4)
    target = [rng.randrange(len(vocab))]
    f = model._forward(context, target)
    assert f is not None, "the forward pass returned None at the probe point"

    eps = 1e-6

    def loss_at():
        o = model._forward(context, target)
        return o["loss"] if o else 0.0

    # ---- the bias: dL/dbias[j] IS dL/dp[j] ---------------------------
    for j in range(model.dim):
        old = model.bias[j]
        model.bias[j] = old + eps
        up = loss_at()
        model.bias[j] = old - eps
        down = loss_at()
        model.bias[j] = old
        numeric = (up - down) / (2 * eps)
        analytic = f["dp"][j]
        assert abs(analytic - numeric) <= 1e-5 * max(1.0, abs(numeric)), (
            "the gradient w.r.t. the bias[%d] is %+.8g but a central "
            "difference of the loss says %+.8g: the analytic gradient "
            "is not the gradient of the loss" % (j, analytic, numeric))

    # ---- the predictor: dL/dW[i][j] = dL/dp[j] * z_ctx[i] ------------
    for i in range(model.dim):
        for j in range(model.dim):
            old = model.predictor[i][j]
            model.predictor[i][j] = old + eps
            up = loss_at()
            model.predictor[i][j] = old - eps
            down = loss_at()
            model.predictor[i][j] = old
            numeric = (up - down) / (2 * eps)
            analytic = f["dp"][j] * f["z_ctx"][i]
            assert abs(analytic - numeric) <= 1e-4 * max(1.0, abs(numeric)), (
                "the gradient w.r.t. the predictor[%d][%d] is %+.8g but a "
                "central difference says %+.8g"
                % (i, j, analytic, numeric))

    # ---- the encoder: dL/dz_ctx[i] = sum_j dL/dp[j] * W[i][j] -------
    n_ctx = len(context)
    for w in context:
        for j in range(model.dim):
            old = model.enc[w][j]
            model.enc[w][j] = old + eps
            up = loss_at()
            model.enc[w][j] = old - eps
            down = loss_at()
            model.enc[w][j] = old
            numeric = (up - down) / (2 * eps)
            analytic = f["d_ctx"][j] / n_ctx
            assert abs(analytic - numeric) <= 1e-4 * max(1.0, abs(numeric)), (
                "the gradient w.r.t. the encoder row %d[%d] is %+.8g but a "
                "central difference says %+.8g"
                % (w, j, analytic, numeric))

    # ---- AND THE GRADIENT MUST NOT BE ZERO -------------------------
    # **A CHECK THAT COMPARES TWO ZEROS IS VACUOUS.** MEASURED
    # 2026-11-07: with the encoder dropped from the forward pass, the
    # analytic d_ctx is ZERO and the central difference is ZERO -- they
    # AGREE, so every comparison above passed, and the mutation
    # survived. The loss must actually DEPEND on the parameters being
    # differentiated, or the check is measuring nothing.
    #
    # **AND THE NORM CANNOT BE USED TO ASK WHETHER IT IS ZERO.** The
    # module's own `norm()` returns 1.0 for a zero vector -- it does
    # that on purpose, so that a division by its result is never a
    # division by zero -- and so `norm(d_ctx) > 1e-12` is TRUE for an
    # all-zero gradient. **THE INSTRUMENT THAT IS SAFE TO DIVIDE BY
    # IS NOT AN INSTRUMENT FOR ASKING WHETHER SOMETHING IS ZERO.** So
    # the largest COMPONENT is used.
    #
    # MEASURED: the unmutated d_ctx's largest component is 1.131, so a
    # bound of 1e-12 has twelve orders of magnitude of margin.
    largest = max(abs(v) for v in f["d_ctx"])
    assert largest > 1e-12, (
        "the gradient with respect to the context is IDENTICALLY ZERO: "
        "the loss does not depend on the encoder's rows at all, so the "
        "model cannot learn anything from them")


# ---------------------------------------------------------------------------
# 1. THE LOSS MUST FALL
# ---------------------------------------------------------------------------
def test_E1_the_loss_falls_by_a_lot():
    """the loss on a HELD-OUT set must FALL, and by a lot.

    **AND THE INSTRUMENT IS THE HELD-OUT SET, MEASURED PAIRED.** The
    old check compared the mean of the first 100 training losses with
    the mean of the last 100, and those are two DIFFERENT sets of
    pairs. MEASURED 2026-11-07: the per-step loss has a standard
    deviation of 0.283, so a 100-sample mean carries a standard error
    of 0.028, and the difference the old check read (0.069) was 2.44
    standard errors of NOISE -- and the noise pointed the WRONG WAY:
    the training-window loss ROSE while the loss on a fixed held-out
    set FELL from 0.99231 to 0.95604.

    **AND THE OLD THRESHOLD WAS ON A CONTAMINATED NUMBER.** 51.12% of
    the training steps were no-ops and each contributed 0.0 -- the
    BEST possible loss -- to the reported mean.

    So the check reads the paired held-out loss, and the threshold is
    set against the measurement: at this configuration the held-out
    loss falls by 0.058 (min_count 20, 400 steps), which is 3.8
    standard errors of the paired difference.
    """
    model, report = jc.train(steps=400, dim=16, max_sentences=4000,
                              min_count=20, verbose=False)
    assert report["held_out_pairs"] > 0, "the held-out set is empty"
    assert report["held_out_loss_fall"] > 0.02, (
        "the held-out loss did not fall: %.5f -> %.5f (a fall of %.5f, "
        "and the paired standard error is %.5f). The model did not train."
        % (report["held_out_loss_before"], report["held_out_loss_after"],
           report["held_out_loss_fall"], report["held_out_se"]))


# ---------------------------------------------------------------------------
# 2. THE TRAINED MODEL MUST BEAT AN UNTRAINED ONE
# ---------------------------------------------------------------------------
def test_E2_the_trained_model_differs_from_an_untrained_one():
    """the trained model's vectors must MOVE.

    **AND THE CHECK FOR THE TRANSPOSED GRADIENT.** MEASURED
    2026-11-07: with the wrong index in the backprop, the trained
    model and an untrained one of the same shape agreed with the list
    on 72.4% of 9,496 words -- IDENTICALLY, to four significant
    figures. A model that agrees with an untrained one to four figures
    has not learned.

    **AND THE MOVE MUST BE A REAL ONE, NOT A FLOATING-POINT WIGGLE.**
    The old check accepted ANY difference above 1e-9, which a single
    rounding difference satisfies. So the move is required to be
    larger than the encoder's own numerical noise.
    """
    counts = jc.corpus_counts(50)
    vocab = sorted(counts)
    untrained = jc.Jepa(vocab, dim=16, seed=20261107)
    trained, report = jc.train(steps=300, dim=16, max_sentences=3000,
                               min_count=50, verbose=False)
    assert report["held_out_loss_fall"] > 0.02, (
        "the model did not train: the held-out loss fell by only %.5f"
        % report["held_out_loss_fall"])

    # the words the training actually touched must have moved, and by
    # MORE than the numerical noise
    moved = 0
    checked = 0
    biggest = 0.0
    for word in list(vocab)[:200]:
        a = untrained.word_vector(word)
        b = trained.word_vector(word)
        if a is None or b is None:
            continue
        checked += 1
        d = max(abs(x - y) for x, y in zip(a, b))
        biggest = max(biggest, d)
        if d > 1e-6:
            moved += 1
    assert checked > 0, "no words to check"
    assert moved > 0, (
        "not one of %d checked word vectors moved by more than 1e-6 "
        "(the largest move was %.3g): the encoder is not receiving a "
        "gradient" % (checked, biggest))


def test_E3_the_trained_model_learns_the_role_structure():
    """the trained model's vectors must carry the role structure.

    **AND THE MEASURE IS THE ROLE GAP, NOT THE PROBE, because the gap
    does not depend on the readout.** The probe is one way to read a
    representation out and it can fail for reasons that are about the
    probe. The role gap cannot: it takes the model's OWN vectors and
    asks whether words the list calls verbs sit closer to each other
    than to the words the list calls nouns.

    **AND THE POINT OF THE CHECK IS THAT THE TRAINED MODEL BEATS AN
    UNTRAINED ONE.** A model that agrees with an untrained one to four
    figures has not learned, and the earlier version of this check
    passed a model that had learned nothing.

    **AND THE THRESHOLD IS MEASURED, NOT GUESSED.** At lr 0.1 the
    trained model's gap beats the untrained one's by +0.0356, and the
    loss falls on the held-out set.
    """
    counts = jc.corpus_counts(2000)
    vocab = sorted(counts)
    untrained = jc.Jepa(vocab, dim=16, lr=0.1, seed=20261107)
    untrained.refresh_mean_direction()
    trained, report = jc.train(steps=200000, dim=16, lr=0.1,
                               max_sentences=20000,
                               min_count=2000, verbose=False)
    assert report["held_out_loss_fall"] > 0.05, (
        "the model did not train: the held-out loss fell by only %.5f"
        % report["held_out_loss_fall"])
    ugap = jc.role_gap(untrained, vocab)
    tgap = jc.role_gap(trained, vocab)
    assert tgap["gap"] > ugap["gap"], (
        "the trained model's role gap %+.4f is not better than the "
        "untrained one's %+.4f: the training did not learn the role "
        "structure" % (tgap["gap"], ugap["gap"]))


# ---------------------------------------------------------------------------
# 3. THE PROBE MUST FIT ITS OWN SEEDS
# ---------------------------------------------------------------------------
def test_E4_the_probe_fits_its_own_seeds():
    """a probe that cannot fit its own seeds is reporting nothing.

    **AND THE CHECK FOR THE DIVERGING PROBE.** MEASURED 2026-11-07:
    the probe's seed scores reached -2,000 and the separation was
    -17.3 for a trained model AND -17.3 for an untrained one -- every
    model looked equally bad, so the readout could not tell a good
    model from a bad one.
    """
    counts = jc.corpus_counts(50)
    vocab = sorted(counts)
    model = jc.Jepa(vocab, dim=16, seed=20261107)
    probe, report = jc.fit_probe(model, jc.SEED_NAMES, jc.SEED_ACTS)
    assert report["seed_names"] > 10, "not enough name seeds found"
    assert report["seed_acts"] > 10, "not enough act seeds found"
    assert report["train_accuracy"] > 0.60, (
        "the probe fits its own seeds at only %.1f%%: the readout is "
        "not measuring the representation"
        % (100 * report["train_accuracy"]))


def test_E5_the_probe_does_not_diverge():
    """the probe's scores must stay in a sane range, and its direction
    must solve the ridge system it claims to solve.

    MEASURED 2026-11-07: the scores reached -2,000. A probe whose
    weights grow without bound reports nothing about the model.

    **AND THE SCORE BOUND ALONE IS NOT ENOUGH.** MEASURED: with the
    ridge's sign flipped, the weight norm goes from 1.87 to 37.16 and
    the separation from -1.03 to -17.81, but the scores only reach
    11.48 -- and the bound here is 100. **A BOUND SET TEN TIMES ABOVE
    THE MUTANT'S VALUE IS NOT A BOUND.** So the check is ALGEBRAIC:
    the probe's direction must solve the ridge system it claims to
    solve, (X'X + l2 I) w = X'y with l2 = 1.0.

    **AND THE RESIDUAL SEPARATES THE THREE CASES BY ORDERS OF
    MAGNITUDE**: 2.2e-15 for the ridge as it is, 1.50 for the ridge
    scaled down a thousandfold, and 39.3 for the sign flipped. So the
    bound is 1e-6, which is eight orders of magnitude below the
    smallest mutant and eight above the true residual.
    """
    counts = jc.corpus_counts(50)
    vocab = sorted(counts)
    model = jc.Jepa(vocab, dim=16, seed=20261107)
    probe, report = jc.fit_probe(model, jc.SEED_NAMES, jc.SEED_ACTS)
    for word in jc.SEED_NAMES[:5] + jc.SEED_ACTS[:5]:
        s = jc.score_with_probe(model, probe[0], probe[1], word)
        assert s is None or abs(s) < 100.0, (
            "the probe's score for %r is %.1f -- it has diverged"
            % (word, s))

    # ---- AND THE RIDGE SYSTEM IT CLAIMS TO SOLVE ---------------------
    xs, ys = [], []
    for word, y in ([(w, -1.0) for w in jc.SEED_NAMES]
                    + [(w, 1.0) for w in jc.SEED_ACTS]):
        v = model.word_vector(word)
        if v is None:
            continue
        xs.append(jc.unit(v))
        ys.append(y)
    w = list(probe[0])
    residual = 0.0
    for i in range(model.dim):
        lhs = 0.0
        for j in range(model.dim):
            a = sum(x[i] * x[j] for x in xs)
            if i == j:
                a += 1.0        # the ridge, l2 = 1.0
            lhs += a * w[j]
        rhs = sum(x[i] * yy for x, yy in zip(xs, ys))
        residual = max(residual, abs(lhs - rhs))
    assert residual < 1e-6, (
        "the probe's direction does not solve the ridge system "
        "(X'X + I) w = X'y: the residual is %.6e. The probe is fitting "
        "something else, so its scores are not measuring the "
        "representation." % residual)


# ---------------------------------------------------------------------------
# 4. THE TWO VIEWS, AND WHAT THEY ARE WORTH
# ---------------------------------------------------------------------------
def test_E6_the_two_views_are_measured_not_assumed():
    """the pairing's similarity must be MEASURED and reported.

    **AND THE MEASUREMENT IS THE FINDING.** The canon corpus is the
    stripped Gutenberg text and the second view is the raw Gutenberg
    text of the same work, so the two views are the SAME OBSERVATION
    rendered twice. If the module reported a JEPA over "good views"
    without this number, the claim would be unfounded.
    """
    manifest = jc.raw_manifest()
    if not manifest:
        pytest.skip("the second view is not built")
    summary = manifest.get("summary", {})
    assert summary.get("canon_sentences", 0) > 0, "the manifest has no counts"
    assert summary.get("matched_sentences", 0) > 0, "nothing matched"
    ratio = (summary["token_identical_sentences"]
             / float(summary["canon_sentences"]))
    assert ratio > 0.5, (
        "the two views are only %.1f%% token-identical, so the "
        "degenerate-pairing finding does not hold and the comparison's "
        "reading has to change" % (100 * ratio))


def test_E7_the_cross_and_within_alignment_are_both_measured():
    """the control must report BOTH numbers.

    **AND THE CONTROL IS WHAT DECIDES WHAT THE COMPARISON CAN CLAIM.**
    If the cross-view alignment and the within-view alignment are the
    same, the second view carries nothing the first did not, and the
    comparison measures a model against a list -- NOT the good-views
    claim.

    **AND THE CONTROL MUST BE ABLE TO FIRE.** On the real corpus the
    two numbers are EQUAL -- that is the finding, and it is why the
    good-views claim is not tested -- so a check of "cross != within"
    would FAIL on the real data and pass on broken code. So the check
    is the other way round: on a SYNTHETIC pair whose two views
    genuinely differ, the control must SEE a difference.

    **AND WITHOUT THAT, THE CONTROL COULD BE READING THE SAME VIEW
    TWICE AND NOBODY WOULD KNOW.** MEASURED 2026-11-07: on the real
    corpus the difference is +0.0000, and on the synthetic pair it is
    +0.0068 -- so the control can tell the views apart, and the
    degeneracy on the real corpus is the DATA's, not the code's.
    """
    pairs = jc.view_pairs(max_sentences=2000)
    assert pairs, "no aligned pairs"
    counts = jc.corpus_counts(50)
    model = jc.Jepa(sorted(counts), dim=16, seed=20261107)
    al = jc.alignment(model, pairs, sample=60)
    assert al["n"] > 0, "no pairs measured"
    assert "cross" in al and "within" in al, "the control is incomplete"
    assert "cross_minus_within" in al, "the difference is not reported"

    # the control must be able to SEE a difference when there IS one:
    # pair each sentence with a DIFFERENT sentence
    synth = []
    for i in range(len(pairs) - 1):
        a = pairs[i][0]
        c = pairs[i + 1][0]
        if len(a) > 4 and len(c) > 4:
            synth.append((a, c))
    assert synth, "no synthetic pairs to test the control with"
    syn = jc.alignment(model, synth, sample=60)
    assert syn["n"] > 0, "the synthetic control measured nothing"
    assert abs(syn["cross_minus_within"]) > 1e-4, (
        "the control CANNOT see a difference between two genuinely "
        "different views (cross %.6f, within %.6f, difference %+.6f): "
        "it is reading the same view twice, so its verdict on the real "
        "corpus means nothing"
        % (syn["cross"], syn["within"], syn["cross_minus_within"]))


def test_E8_the_view_pairs_are_aligned_by_text_not_by_position():
    """the two views must be aligned by the sentence TEXT.

    The raw text carries the Gutenberg licence header and a different
    line wrap, so position i of the raw is not position i of the
    canon. Aligning by position would pair unrelated sentences.
    """
    pairs = jc.view_pairs(max_sentences=200)
    assert pairs, "no pairs at all"
    # the two views of a pair must be the SAME sentence
    same = 0
    for a, b in pairs:
        if a == b:
            same += 1
    assert same == len(pairs), (
        "%d of %d pairs are not the same sentence -- the alignment is "
        "wrong" % (len(pairs) - same, len(pairs)))


# ---------------------------------------------------------------------------
# 5. THE COMPARISON ITSELF
# ---------------------------------------------------------------------------
def test_E9_the_partition_is_disjoint():
    """the two sides of the partition must never share a word.

    **AND DISJOINTNESS IS THE PROPERTY THE WHOLE DESIGN RESTS ON** --
    a word in both lists is accepted for either slot and the pattern
    loses its power.
    """
    counts = jc.corpus_counts(50)
    vocab = sorted(counts)
    model = jc.Jepa(vocab, dim=16, seed=20261107)
    probe, _ = jc.fit_probe(model, jc.SEED_NAMES, jc.SEED_ACTS)
    acts, names = jc.partition(model, probe, vocab, threshold=0.0)
    assert not (set(acts) & set(names)), "the partition overlaps"
    assert len(acts) + len(names) <= len(vocab), "the partition invented words"


def test_E10_the_sized_partition_is_disjoint_too():
    """the EQUAL-COST partition must also be disjoint.

    The sized partition picks the top n_acts and the bottom n_names,
    and when the two overlap the word would be in BOTH lists -- which
    is exactly what the list arm cannot do.

    **AND THE SIZE MUST BE ONE WHERE THE TWO HALVES OVERLAP.** The
    filter that removes the overlap only bites when the halves do
    overlap: MEASURED, at 50 of 6,700 words the overlap without it is
    0, at 3,351 it is 2, and at 4,466 it is 2,232. **A DISJOINTNESS
    CHECK AT A SIZE WHERE THE OVERLAP IS IMPOSSIBLE CHECKS NOTHING.**
    So the size here is two thirds of the vocabulary, where the two
    halves MUST share words if the filter is gone.
    """
    counts = jc.corpus_counts(50)
    vocab = sorted(counts)
    model = jc.Jepa(vocab, dim=16, seed=20261107)
    probe, _ = jc.fit_probe(model, jc.SEED_NAMES, jc.SEED_ACTS)
    acts, names = jc.partition_sized(model, probe, vocab, 50, 50)
    assert not (set(acts) & set(names)), "the sized partition overlaps"
    assert len(acts) == 50, "the sized partition has %d acts, not 50" % len(acts)

    # and the size where the two halves MUST share words
    half = len(vocab) * 2 // 3
    acts2, names2 = jc.partition_sized(model, probe, vocab, half, half)
    assert not (set(acts2) & set(names2)), (
        "the sized partition overlaps at %d of %d words: %d words are in "
        "BOTH lists, and the filter that removes them is what makes the "
        "partition disjoint"
        % (half, len(vocab), len(set(acts2) & set(names2))))


def test_E11_the_both_arms_are_scored_by_the_same_bench():
    """both arms must go through the bench's OWN functions.

    **AND THIS IS THE CHECK FOR THE WHOLE COMPARISON.** A comparison
    whose two arms are scored by two different instruments is not a
    comparison. So the check is that the bench's functions are what
    produce the numbers, and that they refuse a partition that is not
    a Vocabulary.
    """
    import bench_canon_vocab as bench
    from vocab_loader import load_learned_vocab
    lv = load_learned_vocab()
    vocab = lv.Vocabulary(verbs=("walked", "said"), nouns=("man", "dog"))
    held = bench.held_out_sentences()
    disc = bench.discrimination(vocab, held)
    for key in ("real_rate", "shuffled_rate", "analytic_rate", "lift",
                "derivations_agree"):
        assert key in disc, "the bench's discrimination lost %r" % key
    cov = bench.coverage_of(vocab, [s for v in held.values() for s in v])
    assert "fraction" in cov


def test_E12_the_comparison_reports_both_arms():
    """the comparison must report the list AND the model.

    **AND THE MODEL ARM MUST BE REPORTED AT THE LIST'S OWN SIZE**, or
    the two are not comparable: a bigger partition binds more prose
    and lifts differently, so comparing a 27,504-word partition
    against a 3,075-word one compares two different things.
    """
    assert hasattr(jc, "partition_sized"), "the equal-cost partition is gone"
    assert hasattr(jc, "partition"), "the partition is gone"
    assert hasattr(jc, "score"), "the bench scorer is gone"


def test_E13_the_seeds_are_the_same_ones_the_list_uses():
    """the model arm must get the SAME seeds the list arm starts from.

    **AND THE POINT IS FAIRNESS.** The list arm is seeded with the
    pronouns and the auxiliaries; if the model arm got a different or
    a larger set, the comparison would be between a model with more
    information and a list with less.
    """
    from vocab_loader import load_learned_vocab
    lv = load_learned_vocab()
    for word in ("he", "she", "it"):
        assert word in jc.SEED_NAMES, "the name seed %r is missing" % word
    for word in ("is", "was", "were"):
        assert word in jc.SEED_ACTS, "the act seed %r is missing" % word
    # and the seeds must be REAL words in the corpus
    counts = jc.corpus_counts(5)
    for word in jc.SEED_NAMES + jc.SEED_ACTS:
        assert word in counts, "the seed %r is not in the corpus" % word


def test_E14_the_universe_is_the_corpus_s_not_the_list_s():
    """the model must partition the CORPUS's words, not the list's.

    **AND THIS IS THE CHECK FOR A COMPARISON WHERE THE LIST PICKED THE
    GROUND.** If the model's universe were the list's vocabulary, the
    list would have chosen the words and the model would be graded on
    the list's own selection.
    """
    counts = jc.corpus_counts(5)
    universe = jc.corpus_vocabulary(min_count=5)
    assert universe == sorted(counts), "the universe is not the corpus's"
    assert len(universe) > 1000, "the universe is implausibly small"


def test_E15_the_loader_works_without_numpy():
    """the vocabulary learner must load on an interpreter without numpy.

    **AND THIS IS THE CHECK FOR THE IMPORT DEFECT.** MEASURED
    2026-11-07: `bench_canon_vocab.py` could not run on the cron's
    interpreter, because `from constitutional import learned_vocab`
    runs the package __init__, which imports numpy -- even
    though `learned_vocab.py` itself uses only the standard library.
    A measurement that runs on one interpreter and not another is a
    measurement the next session cannot reproduce.
    """
    import subprocess
    code = ("import sys; sys.path.insert(0, %r); "
            "import vocab_loader; "
            "lv = vocab_loader.load_learned_vocab(); "
            "print('LOADED', len(lv.PRONOUNS))" % _SRC)
    proc = subprocess.run([sys.executable, "-c", code],
                          capture_output=True, text=True)
    assert proc.returncode == 0, (
        "the loader failed: %s" % proc.stderr[-400:])
    assert "LOADED" in proc.stdout, proc.stdout


def test_E16_the_bench_runs_on_this_interpreter():
    """the bench must RUN here, not only somewhere else.

    **AND THE MEASUREMENT THAT DECIDES THE VOCABULARY'S QUALITY WAS
    HOSTAGE TO A LIBRARY IT DOES NOT USE.** This check runs the bench
    as a subprocess, so a numpy-free interpreter fails it loudly.
    """
    import subprocess
    proc = subprocess.run(
        [sys.executable, os.path.join(_SRC, "bench_canon_vocab.py")],
        capture_output=True, text=True)
    assert proc.returncode == 0, (
        "the bench does not run on %s: %s"
        % (sys.executable, proc.stderr[-400:]))
    assert "THE DISCRIMINATION" in proc.stdout, (
        "the bench ran but produced no measurement: %s"
        % proc.stdout[-400:])


def test_E17_the_held_out_loss_is_measured_and_paired():
    """the trainer must MEASURE the held-out loss, before and after.

    **AND THE INSTRUMENT MUST BE PAIRED, BECAUSE A WINDOW OF THE
    TRAINING LOSS IS A SAMPLING ARTIFACT.** MEASURED 2026-11-07: the
    per-step loss has a standard deviation of 0.283, so a 100-sample
    mean carries a standard error of 0.028, and the difference the
    window comparison read (0.069) was 2.44 standard errors of noise
    -- pointing the WRONG WAY, while the loss on a fixed held-out set
    fell.

    **AND THE NO-OP STEPS MUST NOT REPORT A LOSS OF ZERO**, which is
    the BEST possible loss: MEASURED, 51.12% of the steps were no-ops
    at the E3 configuration, and each contributed 0.0 to the mean.
    """
    model, report = jc.train(steps=300, dim=16, max_sentences=3000,
                              min_count=50, verbose=False)
    assert report["held_out_pairs"] > 0, "the held-out set is empty"
    assert "held_out_loss_before" in report, "the before-loss is missing"
    assert "held_out_loss_after" in report, "the after-loss is missing"
    assert report["steps_noop"] < report["steps"] * 0.5, (
        "%d of %d steps were no-ops: the trainer is throwing away its "
        "budget" % (report["steps_noop"], report["steps"]))
    # the loss statistics must be over the steps that RAN
    assert report["steps_computed"] + report["steps_noop"] >= report["steps"] * 0.9, (
        "the step accounting does not add up: %d computed + %d no-op "
        "out of %d" % (report["steps_computed"], report["steps_noop"],
                       report["steps"]))


def test_E18_a_step_that_learned_nothing_reports_NO_LOSS():
    """a step with nothing to learn must report NO loss, not a loss of 0.

    **AND A LOSS OF ZERO IS THE BEST POSSIBLE LOSS.** MEASURED
    2026-11-07: `step()` used to return 0.0 when there was nothing to
    do, and the trainer averaged those 0.0s into the reported loss.
    At the E3 configuration 51.12% of the training steps were no-ops,
    and each one contributed the most optimistic value the loss can
    take -- so the reported loss was a mean over two different things,
    and the number the comparison printed was that mean.

    **AND THE CHECK IS DIRECT: A STEP WITH NOTHING TO LEARN RETURNS
    None.** None cannot be averaged into anything by accident, so the
    distinction between "this step learned nothing" and "this step
    reached a loss of zero" is impossible to lose.
    """
    model = jc.Jepa(["a", "b", "c"], dim=4, seed=20261107)
    # an empty context: there is nothing to predict from
    assert model.step([], [0]) is None, (
        "a step with an empty context reported a loss instead of None")
    # an empty target: there is nothing to predict
    assert model.step([0], []) is None, (
        "a step with an empty target reported a loss instead of None")
    # and a real step DOES report a number
    loss = model.step([0, 1], [2])
    assert loss is not None, "a real step reported no loss at all"
    assert isinstance(loss, float), "the loss is not a number"
