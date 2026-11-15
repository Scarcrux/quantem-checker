"""Local timing, availability and accounting diagnostics; no certification of alpha."""

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

from .availability import audit_event_clock
from .ledger import audit_ledger
from .pipeline import audit_prefix_consistency

__version__ = "0.2.0a1"

__all__ = [
    "__version__",
    "audit_event_clock",
    "audit_ledger",
    "audit_prefix_consistency",
    "baseline_convergence",
    "decile_ls_returns",
    "net_of_cost",
    "net_of_cost_per_name",
    "portfolio_baseline_convergence",
    "random_graph_control",
    "run_check",
    "timing_dose_response",
]
