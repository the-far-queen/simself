"""
distributed — Distributed SimSelf primitives.

See README.md for the pattern. Public surface:
- StalkNode — a self-contained mini-SimSelf node
- compress_to_log_int8, taylor_recovery — mixed-precision bridge
- basic_governor — gating predicate for gluing
- norm_invariant, energy_invariant, balance_invariant — common predicates
"""
from .stalk_node import StalkNode, compress_to_log_int8, taylor_recovery
from .governor import (
    basic_governor,
    norm_invariant,
    energy_invariant,
    balance_invariant,
)

__all__ = [
    "StalkNode",
    "compress_to_log_int8",
    "taylor_recovery",
    "basic_governor",
    "norm_invariant",
    "energy_invariant",
    "balance_invariant",
]