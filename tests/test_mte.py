"""mte tests. every function is test_-prefixed so pytest actually collects them.

three checks in this project shared one shape -- they read as covered and never ran:
  - far-health   t_M1_*      11 tests, pytest collected 0
  - far-law      t_L1_*      12 tests, pytest collected 0
  - this file, first draft    8 checks, pytest collected 0 (a script in a test filename)

a check the runner cannot find is not a check. assert on purpose, name them
test_*, and treat "no tests ran" as the failure it is.
"""
import pytest

from constitutional.mte import PSB, Slot, SlotPattern, compile_span
from constitutional.psb_primitives import UnitType

TWO = PSB((Slot("name", UnitType.NAME), Slot("act", UnitType.ACT)))
ONE = PSB((Slot("name", UnitType.NAME),))
PAT = SlotPattern.from_units(UnitType.NAME, UnitType.ACT)


# --- the Godot / robot-arm pattern from Bobby's own notes -----------------

def test_name_act_binds():
    t = compile_span("user go", PAT)
    assert t is not None
    assert t.slots == {"name": "user", "act": "go"}
    assert t.psb.roles == ("name", "act")


def test_trailing_tokens_refused_not_dropped():
    """zip() stops at the shorter sequence. A 4-token span must not bind
    to a 2-slot pattern and lose two words without saying so."""
    assert compile_span("user go stop move", PAT) is None


def test_short_block_does_not_satisfy_long_pattern():
    """The first draft accepted this. It means 'user' alone satisfies
    'someone does something' -- the exact ambiguity MTE exists to remove."""
    assert TWO.compatible(ONE) is False


def test_equal_arity_compatible():
    assert TWO.compatible(TWO) is True


# --- determinism ----------------------------------------------------------

def test_slot_id_deterministic():
    assert Slot("name", UnitType.NAME).id == Slot("name", UnitType.NAME).id


def test_psb_id_deterministic():
    assert TWO.id == PSB((Slot("name", UnitType.NAME), Slot("act", UnitType.ACT))).id


# --- refusal --------------------------------------------------------------

def test_slot_role_must_be_slug():
    with pytest.raises(ValueError):
        Slot("Name With Spaces")


def test_psb_needs_a_slot():
    with pytest.raises(ValueError):
        PSB(())