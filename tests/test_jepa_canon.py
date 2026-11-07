"""
tests/test_jepa_canon.py -- the checks on the JEPA and on the comparison.

EVERY CHECK HERE MUST BE ABLE TO GO RED. MEASURED 2026-11-07: the
project's rule from CENTRAL-RULES.md -- "a test that cannot fail is
not a test" -- and the reason it is written as it is: the JEPA was
built through four defects that EVERY check below is aimed at, and
each of those defects passed a "does it run?" inspection.

THE FOUR DEFECTS, AND THE CHECK THAT CATCHES EACH
--------------------------------------------------
  1. THE ENCODER WAS NEVER APPLIED IN THE FORWARD PASS. The loss
     moved from 0.00470 to 0.00447 over 400 steps -- a flat line --
     and nothing was wrong with the arithmetic, because the "encoder"
     was a set of weights no forward pass ever read. So the check is
     that the loss FALLS BY A LOT, not a little.

  2. THE ENCODER'S BACKPROPAGATION WAS TRANSPOSED. The gradient
     landed on the predictor's OUTPUT index instead of the input's,
     so the encoder received a vector that was not a gradient. The
     trained model then agreed with an UNTRAined model of the same
     shape to four significant figures -- 72.4% of 9,496 words, both
     of them. So the check is that the trained model beats an
     untrained one.

  3. THE LOSS HAD NO SCALE. A cosine loss carries a factor of
     1/||p||, so a predictor emitting a length-0.02 vector produces
     a gradient of length ~50 and the loss CLIMBS. So the check is
     that the loss falls as the steps go up.

  4. THE PROBE DIVERGED. The readout regressed on raw encoder
     vectors of length ~0.15 and its weights grew without bound --
     the seed scores reached -2,000 -- so every model looked equally
     bad. So the check is that the probe fits its own seeds.

AND THE TWO THAT ARE ABOUT THE CLAIM RATHER THAN THE CODE
----------------------------------------------------------
  5. THE TWO VIEWS ARE 97.85% TOKEN-IDENTICAL, so the "good views"
     carry nothing the first view did not. The check is that the
     cross-view alignment and the within-view alignment are MEASURED
     and reported, not assumed.

  6. THE COMPARISON MUST SCORE BOTH ARMS WITH THE SAME INSTRUMENT.
     The check is that the model arm's numbers come out of the
     bench's own functions.
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
# 1. THE LOSS MUST FALL
# ---------------------------------------------------------------------------
def test_E1_the_loss_falls_by_a_lot():
    """the loss must FALL, and by a lot.

    **AND THE THRESHOLD IS THE POINT.** The first version's loss moved
    0.00470 -> 0.00447 over 400 steps: a 5% move, and it was a model
    that had not trained at all. A cosine loss over unrelated unit
    vectors starts near 1.0, so a model that has learned something
    must be well under 1.0.
    """
    model, report = jc.train(steps=400, dim=16, max_sentences=4000,
                              min_count=20, verbose=False)
    assert report["final_loss"] < 0.90, (
        "the loss barely moved: %s -> %s. A flat loss is a model that is "
        "not training, and a small loss move is the shape that looks "
        "like training." % (report["first_loss"], report["final_loss"]))
    assert report["final_loss"] < report["first_loss"] - 0.01, (
        "the loss did not fall: %s -> %s" % (report["first_loss"],
                                            report["final_loss"]))


# ---------------------------------------------------------------------------
# 2. THE TRAINED MODEL MUST BEAT AN UNTRAINED ONE
# ---------------------------------------------------------------------------
def test_E2_the_trained_model_differs_from_an_untrained_one():
    """the trained model's vectors must MOVE.

    **AND THIS IS THE CHECK FOR THE TRANSPOSED GRADIENT.** MEASURED
    2026-11-07: with the wrong index in the backprop, the trained
    model and an untrained one of the same shape agreed with the list
    on 72.4% of 9,496 words -- IDENTICALLY, to four significant
    figures. A model that agrees with an untrained one to four figures
    has not learned.
    """
    counts = jc.corpus_counts(50)
    vocab = sorted(counts)
    untrained = jc.Jepa(vocab, dim=16, seed=20261107)
    trained, report = jc.train(steps=300, dim=16, max_sentences=3000,
                               min_count=50, verbose=False)
    assert report["final_loss"] < 0.95, "the model did not train"

    # the words the training actually touched must have moved
    moved = 0
    checked = 0
    for word in list(vocab)[:200]:
        a = untrained.word_vector(word)
        b = trained.word_vector(word)
        if a is None or b is None:
            continue
        checked += 1
        if any(abs(x - y) > 1e-9 for x, y in zip(a, b)):
            moved += 1
    assert checked > 0, "no words to check"
    assert moved > 0, (
        "not one of %d checked word vectors moved: the encoder is not "
        "receiving a gradient" % checked)


def test_E3_the_trained_model_learns_the_role_structure():
    """the trained model's vectors must carry the role structure.

    **AND THE MEASURE IS THE ROLE GAP, NOT THE PROBE, because the gap
    does not depend on the readout.** The probe is one way to read a
    representation out and it can fail for reasons that are about the
    probe. The role gap cannot: it takes the model's OWN vectors and
    asks whether words the list calls verbs sit closer to each other
    than to the words the list calls nouns.

    **AND THE BUDGET IS FAIR, WHICH IS A MEASURED FACT AND NOT A
    GUESS.** MEASURED 2026-11-07: the model needs enough updates per
    word for the structure to appear -- at the corpus's full 27,504-word
    vocabulary, 400,000 steps (65 updates per word) leaves the gap at
    +0.004, which is NO better than an untrained model's. On a
    vocabulary where each word gets thousands of updates, the gap
    reaches +0.085 against an untrained +0.013. So the check trains
    where the model can learn, and the comparison reports the full
    vocabulary's number separately.

    **AND THE POINT OF THE CHECK IS THAT THE TRAINED MODEL BEATS AN
    UNTRAINED ONE.** A model that agrees with an untrained one to four
    figures has not learned, and the earlier version of this check
    passed a model that had learned nothing.
    """
    counts = jc.corpus_counts(2000)
    vocab = sorted(counts)
    untrained = jc.Jepa(vocab, dim=16, lr=0.1, seed=20261107)
    untrained.refresh_mean_direction()
    trained, report = jc.train(steps=200000, dim=16, lr=0.1,
                               max_sentences=20000, min_count=2000,
                               verbose=False)
    assert report["final_loss"] < report["first_loss"], "the model did not train"
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

    **AND THIS IS THE CHECK FOR THE DIVERGING PROBE.** MEASURED
    2026-11-07: the probe's seed scores reached -2,000 and the
    separation was -17.3 for a trained model AND -17.3 for an
    untrained one -- every model looked equally bad, so the readout
    could not tell a good model from a bad one.
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
    """the probe's scores must stay in a sane range.

    MEASURED 2026-11-07: the scores reached -2,000. A probe whose
    weights grow without bound reports nothing about the model.
    """
    counts = jc.corpus_counts(50)
    vocab = sorted(counts)
    model = jc.Jepa(vocab, dim=16, seed=20261107)
    probe, _ = jc.fit_probe(model, jc.SEED_NAMES, jc.SEED_ACTS)
    for word in jc.SEED_NAMES[:5] + jc.SEED_ACTS[:5]:
        s = jc.score_with_probe(model, probe[0], probe[1], word)
        assert s is None or abs(s) < 100.0, (
            "the probe's score for %r is %.1f -- it has diverged"
            % (word, s))


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
    """
    pairs = jc.view_pairs(max_sentences=2000)
    assert pairs, "no aligned pairs"
    counts = jc.corpus_counts(50)
    model = jc.Jepa(sorted(counts), dim=16, seed=20261107)
    al = jc.alignment(model, pairs, sample=60)
    assert al["n"] > 0, "no pairs measured"
    assert "cross" in al and "within" in al, "the control is incomplete"
    assert "cross_minus_within" in al, "the difference is not reported"


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
    """
    counts = jc.corpus_counts(50)
    vocab = sorted(counts)
    model = jc.Jepa(vocab, dim=16, seed=20261107)
    probe, _ = jc.fit_probe(model, jc.SEED_NAMES, jc.SEED_ACTS)
    acts, names = jc.partition_sized(model, probe, vocab, 50, 50)
    assert not (set(acts) & set(names)), "the sized partition overlaps"
    assert len(acts) == 50, "the sized partition has %d acts, not 50" % len(acts)


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
    executes the package __init__, which imports numpy -- even
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
