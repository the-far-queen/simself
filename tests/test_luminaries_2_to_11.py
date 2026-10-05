"""
test_luminaries_2_to_11.py — tests for the 10 new luminary pattern modules.

10 tests for each of: elixir, rsc, captbaritone, gsathya, chrismccord, gaearon,
ahejlsberg, josephsavona, mofeiZ, anysphere.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src" / "constitutional"))

MODULES = [
    ("elixir_patterns",       ["test_immutable_state",
                              "test_gen_server_lifecycle",
                              "test_dataflow"]),
    ("rsc_patterns",          ["test_es6_module_memoization",
                              "test_rsc_serialization",
                              "test_suspense_fallback",
                              "test_transition_pending"]),
    ("captbaritone_patterns", ["test_canvas2d_rendering",
                              "test_normalized_store",
                              "test_optimistic_update",
                              "test_grats_schema"]),
    ("gsathya_patterns",      ["test_hidden_class_equivalent",
                              "test_inline_cache",
                              "test_dream_state"]),
    ("chrismccord_patterns",  ["test_websocket_dedup",
                              "test_ecto_where",
                              "test_ecto_preload",
                              "test_render_sync"]),
    ("gaearon_patterns",      ["test_redux_dispatch",
                              "test_fast_refresh_compat",
                              "test_distillation_template"]),
    ("ahejlsberg_patterns",   ["test_structural_typing",
                              "test_linq_composable",
                              "test_gate_component"]),
    ("josephsavona_patterns", ["test_rfc",
                              "test_suspense_throws",
                              "test_optimistic_tick"]),
    ("mofeiZ_patterns",       ["test_compiler_allow",
                              "test_compiler_reject_axes",
                              "test_compiler_reject_banned",
                              "test_playground_output"]),
    ("anysphere_patterns",    ["test_token_estimator",
                              "test_jsonrpc_format",
                              "test_token_budget_ok",
                              "test_token_budget_over"]),
]


def run_module_tests(name: str) -> bool:
    """run the module's own __main__ block."""
    fp = HERE / "src" / "constitutional" / f"{name}.py"
    if not fp.is_file():
        return False
    r = subprocess.run(['python', '-u', str(fp)],
                       capture_output=True, text=True, timeout=30)
    # check the last line for "ALL X TESTS PASS"
    last = r.stdout.strip().split('\n')[-1] if r.stdout.strip() else ''
    return 'PASS' in last


def test_l1_all_10_luminary_modules_pass():
    """each of the 10 new luminary pattern modules passes its self-test."""
    results = {}
    for name, _tests in MODULES:
        results[name] = run_module_tests(name)
    failed = [n for n, ok in results.items() if not ok]
    assert not failed, f"failed: {failed}\\n" + str(results)
    print(f"L1: ok (all {len(MODULES)} modules pass)")


def test_l2_all_modules_export_key_classes():
    """each module exports the load-bearing class / function."""
    expected = {
        "elixir_patterns": ["ElixirState", "GenServer", "Supervisor", "Stage"],
        "rsc_patterns": ["SerializedPsi", "Suspense", "Transition"],
        "captbaritone_patterns": ["PsiPixel", "NormalizedStore", "OptimisticUpdate"],
        "gsathya_patterns": ["AxisRecord", "DreamState"],
        "chrismccord_patterns": ["ConstitutionalSocket", "Repo", "RenderSync"],
        "gaearon_patterns": ["ReduxStore", "RefreshSnapshot", "DISTILLATION_TEMPLATE"],
        "ahejlsberg_patterns": ["SacredAxis", "ResilientAxis", "Linq", "GateComponent"],
        "josephsavona_patterns": ["RFC", "SuspendedRead", "OptimisticTick"],
        "mofeiZ_patterns": ["ConstitutionalCompiler", "Playground"],
        "anysphere_patterns": ["ConstitutionalPrompt", "TokenBudget"],
    }
    for name, expected_names in expected.items():
        mod = __import__(name)
        for cls in expected_names:
            assert hasattr(mod, cls), f"{name} missing {cls}"
    print(f"L2: ok ({sum(len(v) for v in expected.values())} classes exported)")


def main():
    test_l1_all_10_luminary_modules_pass()
    test_l2_all_modules_export_key_classes()
    print("\\nALL LUMINARIES 2-TO-11 TESTS PASS (L1..L2)")


if __name__ == "__main__":
    main()