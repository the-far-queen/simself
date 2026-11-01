"""
test_roles.py -- the role registry, pinned.

WHAT THIS FILE ASSERTS, and why each assertion is there
--------------------------------------------------------
1. EVERY ROLE HAS EXACTLY ONE MASTER. Bobby's own rule: *"The smear
   starts when Dickens and Herbert share a paragraph."* So one role, one
   master -- that is what makes the registry a boundary and not a list.

2. THE ROLES ARE THE ONES NAMED. Mary, the college girl, the Scottish
   Far Queen, the goddess in Berkeley, the Tibetan lama, the Sufi master.
   Not "a role like these" -- these.

3. A ROLE'S EVIDENCE IS NAMED, AND ITS ABSENCE IS REPORTED. Three
   roles have their evidence on disk and four do not, and the registry
   has to be able to say which -- because the daily task needs a role
   that can be CHECKED today, not one that is merely named.

4. THE RABBIT ROLE IS MEASURED, NOT ASSUMED. The widest-open phrases
   on this machine (rabbit shedding 3 results, nails 11, hay 18) and
   the top-of-list competitor being a book ABOUT COOPS rather than
   about the animal -- which is why nobody is being the rabbit-care
   expert.

5. NO TWO ROLES SHARE A VOICE AND A MASTER. If two roles had both,
   they would be the same role wearing two hats, and the registry
   would have failed at the only job it has.

Run:
    python -m pytest tests/test_roles.py -q
"""

from __future__ import annotations

import os
import sys

import pytest

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from constitutional import roles as R  # noqa: E402


# ===========================================================================
# 1. ONE ROLE, ONE MASTER
# ===========================================================================

def test_every_role_has_exactly_one_master():
    """Bobby's rule: the smear starts when two masters share a paragraph."""
    for r in R.ROLES:
        assert r.master, ("the role %r has no master" % (r.key,))
        assert r.master.strip(), ("the role %r has an empty master"
                                 % (r.key,))


def test_two_roles_never_share_both_a_master_and_a_voice():
    """if they did, they would be one role wearing two hats."""
    seen = {}
    for r in R.ROLES:
        k = (r.master, r.voice)
        assert k not in seen, (
            "the roles %r and %r share both the master %r and the voice "
            "%r -- they are the same role" % (seen.get(k), r.key,
                                             r.master, r.voice))
        seen[k] = r.key


# ===========================================================================
# 2. THE ROLES ARE THE ONES NAMED
# ===========================================================================

@pytest.mark.parametrize("key", ["mary", "college_girl", "scottish_far_queen",
                                 "goddess_in_berkeley", "tibetan_lama",
                                 "sufi_master"])
def test_the_named_roles_are_present(key):
    """Mary, the college girl, the Scottish Far Queen, the goddess in
    Berkeley, the Tibetan lama, the Sufi master."""
    r = R.by_key(key)
    assert r is not None, ("the role %r is not in the registry" % (key,))
    assert r.role.strip(), ("the role %r has no description" % (key,))
    assert r.subject.strip(), ("the role %r has no subject" % (key,))
    assert r.not_this.strip(), (
        "the role %r has no non-goal, and the non-goals are part of the "
        "frame" % (key,))


def test_every_role_names_a_voice_from_the_catalog():
    """the axes, not a mood. And the catalog ships four."""
    shipped = ("lean", "gritty", "lyric", "didactic")
    for r in R.ROLES:
        assert r.voice in shipped, (
            "the role %r names the voice %r, which is not one of the %d "
            "shipped voices" % (r.key, r.voice, len(shipped)))


# ===========================================================================
# 3. THE EVIDENCE, AND ITS ABSENCE REPORTED
# ===========================================================================

def test_the_evidence_status_distinguishes_present_from_absent():
    """three roles have evidence on disk and four do not, and the
    registry has to be able to say which."""
    status = R.evidence_status()
    assert len(status) == len(R.ROLES)
    present = [k for k, has, _n in status if has]
    absent = [k for k, has, _n in status if not has]
    assert present, "no role has its evidence on disk"
    assert absent, (
        "every role claims evidence -- and the registry must be able to "
        "report a role whose evidence is NOT on disk, because the daily "
        "task needs a role that can be checked today")


def test_the_evidence_files_that_are_named_actually_exist():
    """for every role whose evidence IS on disk, the named files exist."""
    for key, has, n in R.evidence_status():
        r = R.by_key(key)
        for p in r.evidence_paths():
            if os.path.isfile(p):
                continue
            # a missing file is only a failure if the registry claims
            # the role HAS evidence
            assert not has, (
                "the role %r is reported as having evidence, but %r is "
                "not on disk" % (key, os.path.basename(p)))


# ===========================================================================
# 4. THE RABBIT ROLE IS MEASURED
# ===========================================================================

def test_the_rabbit_role_exists_and_is_scoped_to_the_measured_phrases():
    """the widest-open market measured, and nobody in it."""
    r = R.by_key("rabbit_care_expert")
    assert r is not None
    for symptom in ("shedding", "nails", "hay", "potty"):
        assert symptom in r.subject, (
            "the rabbit role's subject does not name the symptom %r, and "
            "those are the phrases that measured open" % (symptom,))


def test_the_rabbit_role_is_not_the_cute_pet_owner():
    """the register is the boundary, and the non-goal says so."""
    r = R.by_key("rabbit_care_expert")
    assert "cute" in r.not_this.lower(), (
        "the rabbit role does not refuse the cute-pet-owner register, "
        "and that register is what the competitors write in")


# ===========================================================================
# 5. THE ROLES ARE DISTINCT
# ===========================================================================

def test_no_two_roles_share_the_same_subject():
    """two roles with one subject are one role."""
    subjects = {}
    for r in R.ROLES:
        assert r.subject not in subjects, (
            "the roles %r and %r have the same subject" % (subjects.get(
                r.subject), r.key))
        subjects[r.subject] = r.key


def test_the_role_keys_are_unique():
    keys = R.role_names()
    assert len(keys) == len(set(keys))
