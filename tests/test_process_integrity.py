"""
test_process_integrity.py — area 0, enforced inside simself.

INDEPENDENT OF ATLAS-EXAM. The exam points at simself and cannot
import it, by architecture, so this check must stand on its own here.

The tests below include one that makes the module FAIL on purpose, to
prove it can go red. A check that has only ever passed is not a check.

Run: python -m pytest tests/test_process_integrity.py -q
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from constitutional import process_integrity as pi  # noqa: E402


class StructureTests(unittest.TestCase):
    def test_seven_rules(self):
        self.assertEqual(len(pi.RULES), 7)
        self.assertEqual([r.number for r in pi.RULES], list(range(1, 8)))

    def test_every_rule_is_actionable(self):
        """A rule that cannot be followed is a slogan."""
        for r in pi.RULES:
            self.assertGreater(len(r.rule), 30, f"rule {r.number} is a slogan")
            self.assertTrue(r.title.strip())

    def test_every_rule_names_what_it_prevents(self):
        """Rules without a named failure are aspirations."""
        for r in pi.RULES:
            self.assertGreater(len(r.prevents), 40,
                               f"rule {r.number} does not say what it "
                               f"prevents")

    def test_rule_one_is_the_central_one(self):
        self.assertIn("diagnose", pi.RULES[0].title.lower())
        self.assertIn("before", pi.RULES[0].rule.lower())


class VerdictTests(unittest.TestCase):
    def test_passes_in_this_repo(self):
        r = pi.check()
        self.assertEqual(r["verdict"], "PASS", f"failed: {r['failed']}")

    def test_is_independent_of_atlas_exam(self):
        r = pi.check()
        self.assertTrue(r["independent_of_atlas_exam"])

    def test_does_not_import_atlas_exam(self):
        """The independence is architectural, so assert it structurally
        rather than trusting the flag."""
        src = Path(pi.__file__).read_text(encoding="utf-8")
        for line in src.splitlines():
            st = line.strip()
            self.assertFalse(st.startswith(("import exam", "from exam")),
                             f"process_integrity must not import the exam: {st}")

    def test_states_its_own_limit(self):
        """The area cannot establish that the process was followed.
        That has to be in the output, not implied."""
        r = pi.check()
        limit = r["does_not_establish"].lower()
        # it must say compliance is not measurable, and that the check
        # only establishes the rules are WRITTEN
        self.assertIn("not measurable", limit)
        self.assertIn("written", limit)
        self.assertIn("followed", limit)


class ItCanGoRedTests(unittest.TestCase):
    """THE POINT. A check that has only ever passed proves nothing."""

    def test_fails_when_the_rules_file_is_absent(self):
        original = pi.rules_path
        try:
            pi.rules_path = lambda: os.path.join(
                str(Path(pi.__file__).parent), "definitely-absent.md")
            r = pi.check()
            self.assertEqual(r["verdict"], "FAIL")
            self.assertIn("rules_file_present", r["failed"])
        finally:
            pi.rules_path = original

    def test_fails_when_the_rules_file_is_trivial(self):
        original = pi.rules_path
        tmp = Path(pi.__file__).parent / "_tmp_rules.md"
        try:
            tmp.write_text("x", encoding="utf-8")     # 1 byte
            pi.rules_path = lambda: str(tmp)
            r = pi.check()
            self.assertEqual(r["verdict"], "FAIL")
            self.assertIn("rules_file_non_trivial", r["failed"])
        finally:
            pi.rules_path = original
            if tmp.exists():
                tmp.unlink()

    def test_fails_when_a_rule_loses_its_reason(self):
        original = list(pi.RULES)
        try:
            pi.RULES[2] = pi.Rule(3, "t", "a rule long enough to pass the "
                                       "length check but empty of reason", "")
            r = pi.check()
            self.assertEqual(r["verdict"], "FAIL")
            self.assertIn("every_rule_states_what_it_prevents",
                          r["failed"])
        finally:
            pi.RULES[:] = original


if __name__ == "__main__":
    unittest.main(verbosity=2)