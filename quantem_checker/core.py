"""Compatibility imports for the version-3 diagnostic implementation.

The original 0.1 implementation remains in Git at bc4751c. These names retain
existing import paths but intentionally receive the documented corrected semantics.
"""

from .screening import (
    baseline_convergence,
    decile_ls_returns,
    net_of_cost,
    net_of_cost_per_name,
    portfolio_baseline_convergence,
    random_graph_control,
    run_check,
    timing_dose_response,
)

__all__ = [
    "baseline_convergence",
    "decile_ls_returns",
    "net_of_cost",
    "net_of_cost_per_name",
    "portfolio_baseline_convergence",
    "random_graph_control",
    "run_check",
    "timing_dose_response",
]
