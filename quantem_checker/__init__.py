"""Quantem Checker — a model-agnostic forensic harness for leakage in financial-ML backtests.

    from quantem_checker import run_check
    rec = run_check(pred, ret)          # pred, ret: [T, N] aligned arrays
    print(rec["verdict"])

Or via the CLI:

    quantem-checker --predictions pred.parquet --returns ret.parquet
"""
from quantem_checker.core import (
    baseline_convergence,
    decile_ls_returns,
    net_of_cost,
    net_of_cost_per_name,
    portfolio_baseline_convergence,
    random_graph_control,
    run_check,
    timing_dose_response,
)

__version__ = "0.1.0"

__all__ = [
    "run_check",
    "timing_dose_response",
    "net_of_cost",
    "net_of_cost_per_name",
    "baseline_convergence",
    "portfolio_baseline_convergence",
    "decile_ls_returns",
    "random_graph_control",
    "__version__",
]
