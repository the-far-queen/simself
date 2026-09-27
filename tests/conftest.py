"""
conftest.py — pytest config for simself.

Defines the `--runslow` CLI flag that overrides the default `-m "not slow"`
addopts from pytest.ini. With `--runslow`, all tests run including the
slow ones (notably test_autocode::test_apply_and_commit_real_patch).
"""
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="Run slow tests (deselected by default)",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # Don't skip anything — let everything run.
        return
    skip_slow = pytest.mark.skip(reason="slow test, use --runslow to enable")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)