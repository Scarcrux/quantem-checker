"""Reporting adequacy and input contracts, not statistical power certification."""

from __future__ import annotations

import numpy as np

MIN_NAMES = 10
MIN_PERIODS = 10


def validate_inputs(
    pred,
    ret,
    *,
    shifts,
    cost_bps,
    q,
    periods_per_year,
    seeds,
    adj,
    weights,
    leak_ratio_threshold,
    leak_abs_floor,
):
    p, r = np.asarray(pred, dtype=float), np.asarray(ret, dtype=float)
    if p.ndim != 2 or p.shape != r.shape or p.shape[0] < 2 or p.shape[1] < 2:
        raise ValueError(
            "aligned nonempty [period, asset] panels with at least two periods/assets required"
        )
    if np.isinf(p).any() or np.isinf(r).any():
        raise ValueError(
            "infinite panel values are invalid; use NaN only for explicitly missing observations"
        )
    shifts = tuple(shifts)
    if (
        not shifts
        or len(set(shifts)) != len(shifts)
        or any(
            isinstance(k, (bool, np.bool_))
            or not isinstance(k, (int, np.integer))
            or k < 0
            for k in shifts
        )
    ):
        raise ValueError("unique nonnegative integer shifts required")
    if not np.isfinite(cost_bps) or cost_bps < 0:
        raise ValueError("finite nonnegative per-side cost required")
    if not np.isfinite(q) or not 0 < q <= 0.5:
        raise ValueError("quantile fraction must satisfy 0 < q <= 0.5")
    if not np.isfinite(periods_per_year) or periods_per_year <= 0:
        raise ValueError("finite positive annualization required")
    if (
        isinstance(seeds, (bool, np.bool_))
        or not isinstance(seeds, (int, np.integer))
        or seeds < 1
    ):
        raise ValueError("positive integer random-graph count required")
    if (
        not np.isfinite(leak_ratio_threshold)
        or not 0 < leak_ratio_threshold < 1
        or not np.isfinite(leak_abs_floor)
        or not 0 <= leak_abs_floor < 1
    ):
        raise ValueError("invalid declared timing-screen thresholds")
    if adj is not None:
        adj = np.asarray(adj)
        if (
            adj.shape != (p.shape[1], p.shape[1])
            or not np.isfinite(adj).all()
            or not np.isin(adj, [0, 1]).all()
        ):
            raise ValueError("finite binary graph matching the asset axes required")
    if weights is not None:
        weights = np.asarray(weights, dtype=float)
        if (
            weights.shape != p.shape
            or not np.isfinite(weights).all()
            or not np.isfinite(r).all()
        ):
            raise ValueError(
                "dense-allocation diagnostics require aligned finite allocations and marks; no missing-mark fill"
            )
    return p, r, shifts, adj, weights


def status(reasons=(), **counts):
    return {
        "status": "NOT_TESTED" if reasons else "TESTED",
        "reasons": list(reasons),
        **counts,
    }


def finalize_screen(record, coverage):
    """Aggregate actual summaries; unit controls here do not simulate IC data."""
    out = dict(record)
    missing = [
        key for key, value in coverage.items() if value["status"] == "NOT_TESTED"
    ]
    if coverage["timing"]["status"] != "TESTED":
        out["leak_flagged"] = None
    if coverage["graph"]["status"] == "NOT_TESTED":
        out["graph_beats_random"] = None
    dense = (out.get("portfolio_1N_convergence") or {}).get("corr_to_1N")
    passes = (
        not missing
        and out["leak_flagged"] is False
        and out["net_sharpe"] > 0.2
        and abs(out["baseline_1N_corr"]) < 0.95
        and (
            coverage["dense_baseline"]["status"] == "NOT_REQUESTED" or abs(dense) < 0.95
        )
        and (
            coverage["graph"]["status"] == "NOT_REQUESTED"
            or out.get("graph_beats_random") is True
        )
    )
    out["diagnostic_status"] = coverage
    out["report_schema"] = "quantem-checker/2"
    out["screen_status"] = (
        "INSUFFICIENT_EVIDENCE" if missing else ("NOT_FLAGGED" if passes else "FLAGGED")
    )
    out["survives_battery"] = bool(passes)
    out["battery_scope"] = (
        "requested diagnostic screens only; not evidence of availability, equivalence or investability"
    )
    if missing:
        out["verdict"] = "INSUFFICIENT EVIDENCE: " + "; ".join(
            f"{key}: {', '.join(coverage[key]['reasons'])}" for key in missing
        )
    elif passes:
        out["verdict"] = (
            "not flagged by requested diagnostic screens; not proof of cleanliness or profitability"
        )
    elif out["leak_flagged"] is True:
        out["verdict"] = (
            "TIMING SCREEN FLAGGED: contemporaneous IC collapses under the stated lag convention"
        )
    else:
        out["verdict"] = (
            "requested cost, baseline or graph screen not passed; not proof of no effect"
        )
    return strict_report(out)


def strict_report(value):
    if isinstance(value, dict):
        return {k: strict_report(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [strict_report(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value
