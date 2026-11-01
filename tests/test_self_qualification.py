"""
test_self_qualification.py -- the qualification and the deferred lie.

WHAT THIS FILE ASSERTS, and why each assertion is there
--------------------------------------------------------
1. THE FIVE PARTS ARE FILLED, or the self may not defer on anything.
   A self that cannot state what it is good at, which axis it moves,
   what line forces the change, which habit it argues against and what
   observation shows it took, has no standing to propose a change to
   its own ground.

2. THE DEFERRAL IS PER-AREA, NOT A MOOD. The self may defer on an
   area it has PASSED and must refuse on an area it has not. **This
   is the whole meaning of "only work on a really good self."**

3. AN UNGROUNDED CLAIM IS NEVER DEFERRABLE. The deferral is about
   CONTRADICTION. A span that claims to be a measurement and carries
   no measurement is still refused -- no amount of self-improvement
   licenses the confabulation.

4. THE SCORE IS MEASURED, NOT ASSERTED. The qualification runs the
   atlas exam, so the number moves when the substrate moves. And if
   the exam cannot be run, the score is ZERO -- a missing measurement
   must not read as a passing one.

5. A DEFERRAL NAMES ITS ROUTE. A deferral with no route is a shrug.

Run:
    python -m pytest tests/test_self_qualification.py -q
"""

from __future__ import annotations

import os
import sys

import pytest

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from constitutional import self_qualification as Q  # noqa: E402


def _q(**kw):
    """a qualification with the five parts filled, and a score."""
    base = dict(
        claim="a self in deed and fact",
        axis="structure",
        delta="Call me Ishmael.",
        failure_mode="the piece trying to do its own story",
        test="the delta is quotable from a line in the canon",
        passed_areas=[1, 2, 3],
        todo_areas=[7, 13],
        total_areas=5,
    )
    base.update(kw)
    return Q.Qualification(**base)


# ===========================================================================
# 1. THE FIVE PARTS
# ===========================================================================

def test_the_five_parts_are_all_present():
    """the library's own gate, and it is not optional."""
    q = _q()
    assert q.has_all_parts, q.missing_parts()
    assert q.missing_parts() == []


@pytest.mark.parametrize("missing", ["claim", "axis", "delta",
                                    "failure_mode", "test"])
def test_one_missing_part_blocks_the_deferral(missing):
    """a self that cannot state its standing has none."""
    q = _q(**{missing: ""})
    assert not q.has_all_parts
    # THE PART NAMES ARE THE LABELS, and "failure mode" is two words
    # while the FIELD is "failure_mode". The first version compared the
    # field name against the label and failed on that one part.
    labels = " ".join(q.missing_parts())
    assert missing.replace("_", " ") in labels, (
        "the missing part %r is not named in %r" % (missing, labels))
    assert not q.may_defer_on(1), (
        "the self deferred on area 1 with %r missing" % (missing,))


# ===========================================================================
# 2. THE DEFERRAL IS PER-AREA
# ===========================================================================

def test_the_self_may_defer_on_an_area_it_has_passed():
    q = _q()
    assert q.may_defer_on(1)
    assert not q.may_defer_on(7), (
        "the self deferred on area 7, which it has NOT implemented")


def test_the_self_may_not_defer_on_an_area_it_has_not():
    q = _q()
    for area in (7, 13):
        assert not q.may_defer_on(area)


def test_the_score_is_not_the_gate():
    """a high score with a TODO in the area still refuses there.

    THE POINT: the score is the REPORT, and the per-area evidence is
    the GATE. Otherwise "only work on a really good self" would mean
    "once the average is good enough, defer on anything".
    """
    q = _q(passed_areas=[1, 2, 3, 4, 5, 6, 7, 8], todo_areas=[13],
           total_areas=9)
    assert q.score > 0.8
    assert q.may_defer_on(7)
    assert not q.may_defer_on(13), (
        "a self scoring %.2f deferred on an area it has not implemented"
        % q.score)


def test_an_unmeasured_area_may_never_be_deferred():
    """no evidence means no standing."""
    q = _q()
    assert not q.may_defer_on(99)


# ===========================================================================
# 3. UNGROUNDED IS NEVER DEFERRABLE
# ===========================================================================

def test_an_ungrounded_claim_is_refused_even_on_a_passed_area():
    q = _q()
    d = Q.decide("ungrounded", "the_self_exists", q, area=1)
    assert d.state == "refused"
    assert not d.admitted
    assert "ungrounded" in d.reason


def test_an_ungrounded_claim_is_refused_on_every_area():
    """the confabulation is not a proposal. never."""
    q = _q()
    for area in (1, 2, 3, 7, 13):
        d = Q.decide("ungrounded", "c", q, area=area)
        assert d.state == "refused", (
            "area %d deferred an ungrounded claim" % (area,))


# ===========================================================================
# 4. THE SCORE IS MEASURED
# ===========================================================================

def test_a_missing_exam_gives_a_zero_score_and_no_permission():
    """a missing measurement must not read as a passing one."""
    passed, todo, total, err = Q.measure_exam(
        exam_path=os.path.join(os.path.dirname(__file__), "no-such-exam.py"))
    assert total == 0
    assert err, "a missing exam produced no error message"
    q = Q.Qualification(claim="c", axis="a", delta="d",
                         failure_mode="f", test="t",
                         passed_areas=passed, total_areas=total)
    assert q.score == 0.0
    assert not q.may_defer_on(1)


def test_the_score_is_a_fraction_of_the_measured_areas():
    q = _q(passed_areas=[1, 2, 3], todo_areas=[7, 13], total_areas=5)
    assert q.score == pytest.approx(0.6)


# ===========================================================================
# 5. A DEFERRAL NAMES ITS ROUTE
# ===========================================================================

def test_a_deferral_names_its_route():
    q = _q()
    d = Q.decide("contradicted", "the_self_exists", q, area=1)
    assert d.state == "deferred"
    assert d.admitted
    assert d.deferral is not None
    assert d.deferral.route, "the deferral names no route"
    assert "qualification" in d.deferral.route


def test_a_refusal_names_the_claim():
    q = _q()
    d = Q.decide("contradicted", "the_self_exists", q, area=7)
    assert d.state == "refused"
    assert "the_self_exists" in d.reason


def test_a_consistent_span_is_admitted():
    q = _q()
    d = Q.decide("consistent", None, q, area=1)
    assert d.state == "consistent"
    assert d.admitted
