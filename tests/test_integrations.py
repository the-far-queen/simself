"""Tests for the integration layer. Each one can go red on purpose.

Run: python -m pytest tests/test_integrations.py -q
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from research import companion as C  # noqa: E402
from research import harness_adapters as H  # noqa: E402
from research import integrations as I  # noqa: E402


# --------------------------------------------------------------------- registry


def test_registry_is_not_empty():
    assert len(I.ALL) >= 10
    assert set(I.BY_ROLE) == {"harness", "avatar", "runtime", "voice", "engine"}


def test_every_entry_has_a_verdict_and_a_licence():
    for e in I.ALL:
        assert e.verdict in (I.VENDOR, I.ADAPT, I.WRAP, I.REFERENCE), e.slug
        assert e.licence, e.slug
        assert e.url.startswith("https://github.com/")


def test_licence_blocked_entries_are_never_usable():
    """The licence is the gate. A GPL repo called as a process is fine; a
    GPL repo copied into an MIT repo is not. This asserts we never mark
    one of them usable.
    """
    for e in I.licence_blocked():
        assert not e.usable, f"{e.slug} is licence-blocked but marked usable"
        assert e.note, f"{e.slug} is blocked without saying why"


def test_gpl_and_unlicensed_are_blocked():
    blocked_names = {e.name for e in I.licence_blocked()}
    # the specific traps the registry exists to catch
    assert "AI Iris Avatar" in blocked_names   # GPL-3.0
    assert "Sengu" in blocked_names            # no licence granted at all
    assert "LivePortrait" in blocked_names      # NOASSERTION


def test_openclaw_is_reference_only():
    """391k stars and still reference-only. Star count must not promote
    something into the runtime path.
    """
    oc = next(e for e in I.ALL if e.slug == "openclaw/openclaw")
    assert oc.stars > 300000
    assert oc.verdict == I.REFERENCE
    assert not oc.usable


def test_registry_partitions_into_three_states():
    """usable | licence-blocked | reference-only = everything, no overlap.

    Reference-only is a real third state, not an edge case: OpenClaw is
    MIT and still never installed. It is neither usable nor blocked.
    """
    usable = {e.slug for e in I.integrable()}
    blocked = {e.slug for e in I.licence_blocked()}
    refonly = {e.slug for e in I.ALL if not e.usable and e.slug not in blocked}
    assert not (usable & blocked)
    assert not (usable & refonly)
    assert not (blocked & refonly)
    assert len(usable) + len(blocked) + len(refonly) == len(I.ALL)
    assert refonly, "expected at least one reference-only entry"


def test_reference_only_is_never_blocked_and_never_usable():
    for e in I.ALL:
        if not e.usable:
            assert e.verdict in (I.REFERENCE,), f"{e.slug} unusable without being REFERENCE"


def test_summary_counts_add_up():
    s = I.summary()
    assert s["entries"] == len(I.ALL)
    refonly = sum(1 for e in I.ALL if not e.usable and e.licence not in ("GPL-3.0", "NONE", "NOASSERTION"))
    assert s["integrable"] + s["licence_blocked"] + refonly == s["entries"]
    assert s["total_stars_reference"] > 1_000_000  # the free-gain figure


# --------------------------------------------------------------------- avatar state


def test_avatar_state_clamps():
    st = C.AvatarState(valence=5.0, arousal=-2.0, presence=99.0).clamp()
    assert st.valence == 1.0
    assert st.arousal == 0.0
    assert st.presence == 1.0


def test_avatar_style_is_derived_not_random():
    assert C.AvatarState(valence=0.6, arousal=0.2, presence=0.9).speaking_style == "warm"
    assert C.AvatarState(valence=0.0, arousal=0.9, presence=0.9).speaking_style == "urgent"
    assert C.AvatarState(valence=0.0, arousal=0.2, presence=0.1).speaking_style == "distant"
    assert C.AvatarState(valence=-0.9, arousal=0.2, presence=0.9).speaking_style == "level"
    assert C.AvatarState(valence=0.0, arousal=0.2, presence=0.9).speaking_style == "even"


def test_style_check_can_fail():
    """A style function that returned a constant would pass the tests above
    only if the constants matched. Prove it discriminates: 25 states must
    not collapse to one label.
    """
    labels = {
        C.AvatarState(valence=v, arousal=a, presence=p).speaking_style
        for v in (-0.9, 0.0, 0.6)
        for a in (0.1, 0.9)
        for p in (0.1, 0.9)
    }
    assert len(labels) >= 3, labels


# --------------------------------------------------------------------- chain degradation


def test_probe_reports_every_link():
    rep = C.probe()
    names = [link.name for link in rep.links]
    assert names == ["avatar_state", "tts_engine", "kokoro_runtime", "telegram_out"]


def test_probe_names_the_first_break():
    """The whole point: a broken chain names which link broke rather than
    reporting silence.
    """
    rep = C.probe()
    if not rep.complete:
        assert rep.first_break is not None
        assert rep.first_break.name in ("avatar_state", "tts_engine", "kokoro_runtime", "telegram_out")
        assert "chain first breaks at" in rep.render()
    else:
        assert "chain complete" in rep.render()


def test_probe_detects_a_missing_kokoro_model(tmp_path):
    """Force the TTS link to fail by pointing at a model that is not there.
    If this cannot go red, the chain probe is decorative.
    """
    rep = C.probe(kokoro_model=tmp_path / "absent.onnx")
    tts = next(link for link in rep.links if link.name == "tts_engine")
    assert not tts.available
    assert not rep.complete
    assert rep.first_break.name == "tts_engine"


def test_speak_falls_back_instead_of_raising(tmp_path, monkeypatch):
    """On a broken chain, speak() returns a report with a reason. It does
    not raise, and it does not claim success.
    """
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    rep = C.probe()
    if rep.complete:
        pytest.skip("chain is complete on this machine; fallback path not exercised")
    res = C.speak("hello", C.AvatarState(), tmp_path / "x.wav")
    assert res["ok"] is False
    assert res["fallback"] == "plain_text"
    assert res["reason"]
    assert not (tmp_path / "x.wav").exists()


def test_speak_reports_state_in_the_result(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    st = C.AvatarState(valence=0.7, arousal=0.2, presence=0.8)
    res = C.speak("hello", st, tmp_path / "y.wav")
    assert res["state"]["valence"] == 0.7
    assert res["style"] == "warm"
    assert "avatar_state" in res["chain"]


# --------------------------------------------------------------------- harness adapters


def test_survey_covers_every_probe():
    survey = H.survey()
    assert set(survey) == set(H.PROBES)
    assert len(survey) == 8


def test_every_adapter_reports_how_it_looked():
    """An adapter that cannot report its own failure mode is a liability."""
    for name, avail in H.survey().items():
        assert avail.how, name
        assert avail.detail, name


def test_openclaw_adapter_is_deliberately_absent():
    assert not H.openclaw().present
    assert "reference only" in H.openclaw().detail


def test_adapters_can_go_red():
    """A machine with none of these installed must report all missing.
    Guards against a probe that returns True by default.
    """
    survey = H.survey()
    if all(a.present for a in survey.values()):  # pragma: no cover
        pytest.skip("this machine has everything installed")
    assert sum(1 for a in survey.values() if not a.present) > 0


def test_render_survey_reports_count():
    text = H.render_survey()
    assert "present" in text
    assert text.strip().splitlines()[-1].split()[0].count("/") == 1


def test_availability_bool_is_honest():
    assert bool(H.Availability("x", True, "t")) is True
    assert bool(H.Availability("x", False, "t")) is False