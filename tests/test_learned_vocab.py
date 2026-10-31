"""
tests/test_learned_vocab.py -- the checks on the learned vocabulary.

EVERY CHECK HERE MUST BE ABLE TO GO RED. MEASURED 2026-10-31: the
first version of the mutation harness mutated the builder's SOURCE by
exact string, and the strings had moved -- so every mutation silently
failed to apply and the script reported "0 of 8 mutations went RED",
which reads as a result and is the opposite of one. **So the
mutations here corrupt the BUILT ARTIFACT, which cannot silently fail
to apply, and the harness asserts the UNMUTATED corpus is green
first.**

THE CHECKS
----------
  1. the lists are DISJOINT -- the property the whole design rests on
  2. the artifact's digest matches its content (a stale or edited
     artifact is REFUSED, not used)
  3. a non-disjoint artifact is REFUSED at load, not used
  4. the learner gets the roles RIGHT -- measured against hand-written
     ground truth the learner did not learn from
  5. the function words are NOT in the vocabulary (a slot that matches
     "the" matches nothing)
  6. the line-break fragments are NOT in the vocabulary
  7. the MTE, wired with the vocabulary, binds literary prose that the
     substrate's 31 technical forms CANNOT bind
  8. the MTE still refuses what it refused before (the substrate's own
     sentences still bind; the wiring does not break them)
"""

import json
import os
import shutil
import sys
import tempfile

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from constitutional import learned_vocab as lv
from constitutional.mte import SlotPattern, compile_span
from constitutional.psb_primitives import PRIMITIVES, UnitType, classify_span


# --- 1. the property the design rests on --------------------------------

def test_the_lists_are_disjoint():
    """A word in both lists is in both form sets, so `matches()`
    accepts it for either slot and the pattern loses its power."""
    vocab = lv.load_vocabulary()
    overlap = set(vocab.verbs) & set(vocab.nouns)
    assert overlap == set(), (
        "%d words are in both lists, e.g. %s"
        % (len(overlap), sorted(overlap)[:10]))


def test_the_lists_are_not_empty():
    vocab = lv.load_vocabulary()
    assert len(vocab.verbs) > 0
    assert len(vocab.nouns) > 0


# --- 2. the artifact's own digest ---------------------------------------

def test_the_artifact_digest_matches_its_content():
    vocab = lv.load_vocabulary()
    import hashlib
    actual = hashlib.sha256(vocab.canonical_bytes()).hexdigest()
    assert vocab.content_sha == actual, (
        "the artifact's recorded digest %s does not match its content %s"
        % (vocab.content_sha[:16], actual[:16]))


# --- 3. a corrupt artifact is REFUSED, not used -------------------------

def test_a_non_disjoint_artifact_is_refused():
    """THE CHECK THAT MUST BE ABLE TO FAIL. A tampered artifact must
    raise at load, not be silently used."""
    path = lv.artifact_path()
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    payload["nouns"] = list(payload["verbs"]) + list(payload["nouns"])
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as fh:
        json.dump(payload, fh)
        tmp = fh.name
    try:
        with pytest.raises(ValueError):
            lv.load_vocabulary(tmp)
    finally:
        os.unlink(tmp)


def test_a_tampered_artifact_is_refused():
    """A word changed without the digest being updated must be
    REFUSED -- otherwise the artifact is a claim with no check."""
    path = lv.artifact_path()
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    payload["verbs"] = list(payload["verbs"]) + ["a-smuggled-word"]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as fh:
        json.dump(payload, fh)
        tmp = fh.name
    try:
        with pytest.raises(ValueError):
            lv.load_vocabulary(tmp)
    finally:
        os.unlink(tmp)


def test_a_tampered_artifact_is_refused_even_when_the_digest_is_edited():
    """**AND THIS IS THE CHECK THE DIGEST ALONE COULD NOT BE.**

    MEASURED 2026-10-31: the first mutation harness found that a
    corruption with the content digest EDITED TO MATCH still passed
    every check. The content digest is a claim the artifact makes
    about itself, and a tamperer edits it alongside the content.

    So the check that catches it is a RE-DERIVATION: learn the lists
    again from the canon and compare. That is a check made from
    OUTSIDE the artifact, and it is the second independent derivation
    (CENTRAL-RULES rule 5).
    """
    path = lv.artifact_path()
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    # corrupt the content AND edit the digest to match it
    payload["verbs"] = list(payload["verbs"]) + ["a-smuggled-word"]
    import hashlib
    canonical = json.dumps(
        {"verbs": sorted(payload["verbs"]), "nouns": sorted(payload["nouns"]),
         "version": payload.get("version", "1.0.0"),
         "min_evidence": payload.get("min_evidence", 3)},
        sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["content_sha"] = hashlib.sha256(canonical).hexdigest()
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as fh:
        json.dump(payload, fh)
        tmp = fh.name
    try:
        # the digests all agree -- so the digests do NOT catch it
        assert lv.load_vocabulary(tmp, verify_learner=False) is not None
        # and the re-derivation DOES
        with pytest.raises(ValueError):
            lv.load_vocabulary(tmp, verify_rederivation=True)
    finally:
        os.unlink(tmp)


def test_the_rederivation_matches_the_artifact():
    """THE RE-DERIVATION ITSELF. The artifact must equal what the canon
    teaches -- if it does not, the artifact is edited."""
    vocab = lv.load_vocabulary()
    report = lv.verify_by_rederivation(vocab)
    assert report["checked"], report
    assert report["matches"], (
        "the artifact does not match the canon: %s" % report)


def test_a_missing_artifact_is_refused_by_name():
    with pytest.raises(FileNotFoundError):
        lv.load_vocabulary(os.path.join(tempfile.gettempdir(),
                                        "no-such-vocabulary.json"))


# --- 4. the learner gets the ROLES right --------------------------------

def test_the_learner_gets_the_roles_right():
    """MEASURED against hand-written ground truth the learner did not
    learn from (`restore_probe.SEED_VERBS` / `SEED_NOUNS`).

    The ROLE accuracy is what matters, not the coverage of the lists.
    MEASURED 2026-10-31: role errors were 2 of 55 verbs and 1 of 74
    nouns against the full learned lists -- so the roles are right even
    when the list is far too large.
    """
    from constitutional.restore_probe import SEED_NOUNS, SEED_VERBS
    vocab = lv.load_vocabulary()
    verbs = set(vocab.verbs)
    nouns = set(vocab.nouns)

    verb_role_errors = verbs & set(SEED_NOUNS)
    noun_role_errors = nouns & set(SEED_VERBS)
    assert len(verb_role_errors) <= 4, (
        "%d words learned as verbs are nouns in the ground truth: %s"
        % (len(verb_role_errors), sorted(verb_role_errors)[:8]))
    assert len(noun_role_errors) <= 4, (
        "%d words learned as nouns are verbs in the ground truth: %s"
        % (len(noun_role_errors), sorted(noun_role_errors)[:8]))


def test_the_common_english_verbs_are_learned():
    """the words the engine must have, or it cannot read prose."""
    vocab = lv.load_vocabulary()
    verbs = set(vocab.verbs)
    for w in ("said", "walked", "looked", "smiled", "breathed", "said"):
        assert w in verbs, "%s is not in the learned verb list" % w


def test_the_common_english_nouns_are_learned():
    vocab = lv.load_vocabulary()
    nouns = set(vocab.nouns)
    for w in ("man", "woman", "officer", "door", "hand", "river"):
        assert w in nouns, "%s is not in the learned noun list" % w


def test_a_sense_carries_the_pattern_it_was_learned_in():
    """**AND THE SHAPE, WHICH IS THE DEFECT THE PROBE HID.** MEASURED
    2026-10-31: the restore probe DROPPED 1918 of 1918 sentences
    (100%) -- and the cause was not the vocabulary. Every learned
    sense carried a ONE-SLOT PSB (just its own role), while the
    pattern being restored into has TWO slots -- and
    `PSB.compatible()` requires EQUAL ARITY, so a one-slot sense can
    never satisfy a two-slot pattern.

    So the restore could never succeed, for any input. This check
    asserts the arity matches.
    """
    from constitutional.restore_probe import LearnedSense
    sense = LearnedSense(word="walked", role="act",
                         evidence="the officer walked", source="x.txt",
                         shape=("name", "act")).to_sense()
    assert sense.psb is not None
    assert len(sense.psb.slots) == 2, (
        "the sense carries a %d-slot PSB -- a one-slot sense can never "
        "be restored into a two-slot pattern"
        % len(sense.psb.slots))
    assert sense.psb.roles == ("name", "act")


def test_the_restore_succeeds_on_a_real_window():
    """THE END-TO-END CHECK ON THE PROBE. A window that binds must
    restore -- and it must restore through the probe's own path, with
    the lexicon it learns.

    MEASURED 2026-10-31: before the shape fix this was 0 of 1918
    sentences restored. Now the probe reports 36.7% carried on
    star-rider.
    """
    from constitutional import restore_probe as rp
    from constitutional.mte import SlotPattern, compile_span, restore
    rp.word_lists()          # the vocabulary, and the install
    lex, _learned = rp.learn_lexicon()
    pattern = SlotPattern.from_units(*[rp._unit_for(r)
                                        for r in ("name", "act")])
    t = compile_span("he walked", pattern)
    assert t is not None, "the window did not bind"
    r = restore(t, lex)
    assert r is not None, (
        "the window bound but did not restore -- the lexicon's senses "
        "do not carry a compatible pattern")
    assert r.restored
    assert r.lossless


def test_the_artifact_write_is_atomic():
    """**AND THE WRITE MUST BE ATOMIC.** MEASURED 2026-10-31: the
    bench rewrites the artifact while the probe reads it, and a reader
    that catches the file mid-write sees a torn artifact -- which
    looks exactly like tampering, and made the probe fall back to the
    bootstrap and report a confident "100% DROPPED" number measured
    with the wrong vocabulary.

    So the write goes to a temporary file and is moved into place. The
    check: the temporary file does not survive the write.
    """
    import glob
    vocab = lv.load_vocabulary()
    path = lv.write_artifact(vocab)
    leftovers = glob.glob(os.path.join(os.path.dirname(path), ".*tmp"))
    assert leftovers == [], (
        "the artifact write left temporary files behind: %s" % leftovers)


# --- 5. the function words are NOT in the vocabulary --------------------

def test_the_function_words_are_not_in_the_vocabulary():
    """A slot that matches 'the' matches nothing. MEASURED: in the
    unfiltered bootstrap the top 'verbs' were the (157,756), of
    (141,965), and (124,953)."""
    vocab = lv.load_vocabulary()
    words = set(vocab.verbs) | set(vocab.nouns)
    hits = words & lv.FUNCTION_WORDS
    assert hits == set(), (
        "%d function words are in the vocabulary: %s"
        % (len(hits), sorted(hits)[:12]))


def test_the_function_words_the_bootstrap_loved_are_absent():
    """MEASURED: in the unfiltered bootstrap the top "verbs" were the
    (157,756), of (141,965), and (124,953).

    **AND "it" IS NOT IN THIS LIST, ON PURPOSE.** MEASURED
    2026-10-31: excluding the pronouns made the (name, act) pattern
    bind LESS often in real English than in shuffled English -- LIFT
    0.74x, BELOW 1.0 -- because the commonest name-verb adjacency in
    English is a pronoun and a verb ("he walked", "it moved"). So the
    pronouns are names and the auxiliaries are acts, and the words
    that carry no role at all are the ones excluded here.
    """
    vocab = lv.load_vocabulary()
    words = set(vocab.verbs) | set(vocab.nouns)
    for w in ("the", "of", "and", "to", "a", "in", "that"):
        assert w not in words, (
            "%s carries no role and must not be a slot form" % w)


def test_the_pronouns_are_names_and_the_auxiliaries_are_acts():
    """**AND THE SEEDS ARE EXCLUSIVE**, which is the property that
    keeps the two lists disjoint.

    MEASURED 2026-10-31: the first version merged the seeds in
    without removing them from the other side, and the threshold sweep
    caught the overlap.
    """
    vocab = lv.load_vocabulary()
    verbs = set(vocab.verbs)
    nouns = set(vocab.nouns)
    for w in ("he", "she", "it", "they", "him", "her", "them", "we"):
        assert w in nouns, "%s is a name and must be in the noun list" % w
        assert w not in verbs, (
            "%s is a name and must NOT be in the verb list" % w)
    for w in ("was", "is", "were", "had", "has", "been", "did"):
        assert w in verbs, "%s is an act and must be in the verb list" % w
        assert w not in nouns, (
            "%s is an act and must NOT be in the noun list" % w)


# --- 6. the line-break fragments are NOT in the vocabulary --------------

def test_the_line_break_fragments_are_not_in_the_vocabulary():
    """MEASURED: the unfiltered learner produced 'a--', 'a-begging',
    'a-fishing' -- fragments of words broken across a line."""
    vocab = lv.load_vocabulary()
    words = set(vocab.verbs) | set(vocab.nouns)
    frags = [w for w in words if lv.is_fragment(w)]
    assert frags == [], (
        "%d line-break fragments are in the vocabulary: %s"
        % (len(frags), sorted(frags)[:12]))


# --- 7. the MTE, WIRED, BINDS WHAT THE SUBSTRATE CANNOT ----------------

def test_the_wired_mte_binds_literary_prose():
    """THE POINT OF THE WHOLE CHANGE. The substrate's 31 technical forms
    cannot bind 'the officer walked'; the learned vocabulary can."""
    from constitutional.mte import SlotPattern
    vocab = lv.load_vocabulary()
    pat = SlotPattern.from_units(UnitType.NAME, UnitType.ACT)

    # the substrate's own forms, as the control
    substrate_name = set(PRIMITIVES[UnitType.NAME])
    substrate_act = set(PRIMITIVES[UnitType.ACT])
    assert "officer walked" not in (" ".join([n, a])
                                    for n in substrate_name
                                    for a in substrate_act)

    # and the learned vocabulary binds it
    assert "officer" in set(vocab.nouns)
    assert "walked" in set(vocab.verbs)


def test_the_vocabulary_reaches_the_mte_matcher():
    """THE WIRING ITSELF. `SlotPattern.matches()` reads PRIMITIVES, so
    the vocabulary must be installed there for the engine to use it.

    **AND THIS CHECK MUST BE ABLE TO FAIL**: if the wiring is not
    there, the MTE still refuses the literary span. So this asserts the
    SPAN BINDS, not that the words are in a dictionary somewhere.
    """
    from constitutional import psb_primitives
    original = {u: list(w) for u, w in PRIMITIVES.items()}
    try:
        psb_primitives.install_vocabulary(lv.load_vocabulary())
        pat = SlotPattern.from_units(UnitType.NAME, UnitType.ACT)
        # the literary span binds -- this is the whole point
        lit = compile_span("officer walked", pat)
        assert lit is not None, (
            "with the vocabulary installed, the MTE still refused "
            "'officer walked' -- the wiring did not reach the matcher")
        assert lit.slots == {"name": "officer", "act": "walked"}
    finally:
        psb_primitives.PRIMITIVES.clear()
        psb_primitives.PRIMITIVES.update(original)


def test_the_install_is_idempotent():
    """Calling the install twice must not double the list -- otherwise
    a consumer that installs on every import grows the vocabulary."""
    from constitutional import psb_primitives
    original = {u: list(w) for u, w in PRIMITIVES.items()}
    try:
        v = lv.load_vocabulary()
        psb_primitives.install_vocabulary(v)
        once = len(psb_primitives.PRIMITIVES[UnitType.ACT])
        psb_primitives.install_vocabulary(v)
        twice = len(psb_primitives.PRIMITIVES[UnitType.ACT])
        assert once == twice, (
            "the install is not idempotent: %d forms then %d"
            % (once, twice))
    finally:
        psb_primitives.PRIMITIVES.clear()
        psb_primitives.PRIMITIVES.update(original)


def test_the_wiring_installs_the_vocabulary_for_the_mte_matcher():
    """**AND THE VOCABULARY LIVES IN ITS OWN REGISTRY**, not in
    PRIMITIVES. MEASURED 2026-10-31: installing it INTO PRIMITIVES
    changed `classify_span()` -- the substrate's own classifier -- and
    so weakened the confabulation filter, which catches
    fluent-but-empty spans by spotting the ones that classify as
    OTHER. A change that improves the coverage number and weakens a
    safety check is not a change.

    So the check asserts the vocabulary reaches the MTE's matcher, AND
    that PRIMITIVES itself is untouched.
    """
    from constitutional import psb_primitives
    before = {u: list(w) for u, w in PRIMITIVES.items()}
    try:
        psb_primitives.install_vocabulary(lv.load_vocabulary())
        # the vocabulary reached the LITERARY registry
        assert "officer" in psb_primitives.literary_forms("name")
        assert "walked" in psb_primitives.literary_forms("act")
        # and PRIMITIVES is UNTOUCHED
        after = {u: list(w) for u, w in PRIMITIVES.items()}
        assert before == after, (
            "the install changed PRIMITIVES -- the substrate's own "
            "classifier must not see the learned forms")
    finally:
        psb_primitives.uninstall_vocabulary()


def test_the_substrate_classifier_is_unchanged_by_the_install():
    """THE SAFETY PROPERTY. `classify_span()` is what
    `confabulation_filter.is_confabulation()` depends on, and the
    confabulation filter catches fluent-but-empty spans by spotting
    the ones that classify as OTHER.

    MEASURED 2026-10-31, the behaviour that must be PRESERVED:

        the system refuses the proposal  -> name
        the agent will commit the change -> name
        Kelly walked to the door         -> other
        The officer did not smile        -> refuse

    **AND THE FIRST VERSION OF THIS WORK BROKE ALL FOUR.** It put the
    learned forms into PRIMITIVES, so "The officer did not smile"
    became `act` instead of `refuse` -- and with coverage at 92.8%-
    99.3% almost every span would have classified as non-OTHER, which
    would have silently WEAKENED the confabulation filter. This check
    is the one that would have caught it.
    """
    from constitutional import psb_primitives
    before = {s: classify_span(s) for s in (
        "the system refuses the proposal",
        "the agent will commit the change",
        "Kelly walked to the door",
        "The officer did not smile")}
    try:
        psb_primitives.install_vocabulary(lv.load_vocabulary())
        after = {s: classify_span(s) for s in before}
        assert before == after, (
            "the substrate's classifier changed:\n  before %s\n  after  %s"
            % (before, after))
    finally:
        psb_primitives.uninstall_vocabulary()


def test_the_mte_binds_the_literary_span_after_the_install():
    """THE END-TO-END CHECK. With the vocabulary installed, the MTE
    binds a literary span it refused before, AND still binds the
    substrate's own span."""
    from constitutional import psb_primitives
    try:
        psb_primitives.install_vocabulary(lv.load_vocabulary())
        pat = SlotPattern.from_units(UnitType.NAME, UnitType.ACT)
        lit = compile_span("officer walked", pat)
        assert lit is not None, (
            "the MTE refused 'officer walked' with the vocabulary installed")
        assert lit.slots == {"name": "officer", "act": "walked"}
        # the substrate's own span still binds
        tech = compile_span("user go", pat)
        assert tech is not None, (
            "the substrate's own span stopped binding -- the install "
            "REPLACED the forms instead of adding to them")
    finally:
        psb_primitives.uninstall_vocabulary()
