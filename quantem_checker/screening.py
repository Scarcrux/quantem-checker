"""Versioned screening v3; legacy core.py and its bound records stay unchanged.

Derived from the first-party checker. Correct tied ranks, preselect assets before
outcome marks, and label cost/baseline/graph outputs as diagnostic proxies.

Quantem Checker — a model-agnostic forensic harness for the four-control battery.

A model-agnostic screening entry point: aligned prediction and return panels
produce timing, cost and baseline diagnostics, plus an optional graph comparison.
The screens do not prove leakage, equivalence, graph advantage or profitability.

Convention. `pred[t, n]` is the score for asset n formed from information available at
the end of period t, intended to predict the return realized in period t+1. `ret[t, n]`
is asset n's realized return IN period t. Both are [T, N] float arrays, NaN allowed.

The four controls:
  1. Honest-timing dose-response. IC of pred[t] against ret[t+k] for k = 0,1,2,...
     k=0 is a same-period comparison; k=1 is the declared next-period horizon.
     A large same-period IC that collapses at k=1 is one possible warning sign,
     not a necessary or sufficient test of information availability.
  2. Net-of-cost. The declared (k=1) decile long-short Sharpe gross vs net of a per-side
     target-weight turnover cost proxy (no holdings drift or funding model).
  3. Naive-baseline convergence. Correlation of the strategy's long-leg return to a
     1/N (equal-weight) portfolio return: high correlation is an overlap diagnostic,
     not proof of identical portfolios or absent factor alpha.
  4. Random-graph control (optional). If a boolean adjacency is supplied, compare the
     graph-neighbor-averaged signal to an out-degree-matched per-node random graph
     (self-loops excluded from both).

Flags are nullable when required evidence is not computable. A false timing
flag means only "not flagged", never clean. These flags are a SCREEN: the leak
flag in particular is a heuristic symptom (a large lag0/lag1 ratio that
must also have an insignificant honest-horizon IC before the verdict fires), and economic
conclusions require separately validated data, accounting and inference that this
module does not supply.
"""

from __future__ import annotations

import numpy as np

from .adequacy import MIN_NAMES, MIN_PERIODS, finalize_screen, status, validate_inputs


def _rankdata(a):
    """Zero-based average ranks; tied scores cannot encode asset order."""
    _, inverse, counts = np.unique(a, return_inverse=True, return_counts=True)
    ranks = np.cumsum(counts) - (counts + 1) / 2
    return ranks[inverse]


def _row_ic(pred_row, ret_row):
    m = np.isfinite(pred_row) & np.isfinite(ret_row)
    if m.sum() < MIN_NAMES or np.nanstd(pred_row[m]) == 0 or np.nanstd(ret_row[m]) == 0:
        return np.nan
    return np.corrcoef(_rankdata(pred_row[m]), _rankdata(ret_row[m]))[0, 1]


def _per_period_ics(pred, ret, k):
    """Per-period cross-sectional rank-ICs of pred[t] vs ret[t+k]. Each lag uses its
    own bound (T - k), so a lag's IC does not depend on which other shifts were
    requested alongside it."""
    T = pred.shape[0]
    return np.array([_row_ic(pred[t], ret[t + k]) for t in range(T - k)])


def timing_dose_response(pred, ret, shifts=(0, 1, 2, 3)):
    """Mean cross-sectional rank-IC of pred[t] vs ret[t+k] for each k in shifts.

    Each lag k is truncated at T - k (a per-lag bound), so the IC at a given lag is
    independent of which other shifts were requested in the same call."""
    out = {}
    for k in shifts:
        values = _per_period_ics(pred, ret, k)
        out[k] = (
            float(np.mean(values[np.isfinite(values)]))
            if np.isfinite(values).any()
            else np.nan
        )
    return out


def decile_ls_returns(pred, ret, q=0.1, horizon=1):
    """Per-period decile long-short return earning ret[t+horizon] under the declared indexing."""
    T, N = pred.shape
    k = max(1, int(N * q))
    out, longs = [], []
    for t in range(T - horizon):
        s = pred[t]
        r = ret[t + horizon]
        m = np.isfinite(s)
        if m.sum() < 2 * k:
            out.append(np.nan)
            longs.append(np.nan)
            continue
        idx = np.where(m)[0]
        order = idx[np.argsort(s[idx], kind="stable")]
        lo, hi = order[:k], order[-k:]
        if not np.isfinite(r[np.concatenate((lo, hi))]).all():
            out.append(np.nan)
            longs.append(np.nan)
            continue
        out.append(r[hi].mean() - r[lo].mean())
        longs.append(r[hi].mean())
    return np.array(out), np.array(longs)


def _turnover(pred, q=0.1):
    """Mean target L1 change including initial entry; no holdings drift model."""
    _, n = pred.shape
    k = max(1, int(n * q))
    previous_hi = previous_lo = set()
    turns = []
    for scores in pred:
        idx = np.flatnonzero(np.isfinite(scores))
        if len(idx) < 2 * k:
            return np.nan
        order = idx[np.argsort(scores[idx], kind="stable")]
        lo, hi = set(order[:k].tolist()), set(order[-k:].tolist())
        turns.append((len(hi ^ previous_hi) + len(lo ^ previous_lo)) / k)
        previous_hi, previous_lo = hi, lo
    return float(np.mean(turns)) if turns else np.nan


def net_of_cost(pred, ret, cost_bps=10.0, q=0.1, periods_per_year=252):
    """Target-turnover sensitivity only; not a funded execution simulation.

    Initial entry is included, terminal positions stay open, and missing selected
    marks invalidate the cost summary rather than selecting replacement assets.
    Gross exposure is two (one long plus one short); costs are per side.
    """
    ls, _ = decile_ls_returns(pred, ret, q, horizon=1)
    valid = len(ls) > 0 and np.isfinite(ls).all()
    ann = np.sqrt(periods_per_year)
    turn = _turnover(pred[:-1], q)
    cost_per_period = turn * cost_bps / 1e4
    gross_sh = float(ls.mean() / ls.std() * ann) if valid and ls.std() > 0 else np.nan
    net = ls - cost_per_period
    net_sh = float(net.mean() / net.std() * ann) if valid and net.std() > 0 else np.nan
    return {
        "gross_sharpe": round(gross_sh, 3),
        "net_sharpe": round(net_sh, 3),
        "turnover_per_period": round(turn, 3),
        "cost_drag_per_period_bps": round(cost_per_period * 1e4, 2)
        if valid
        else np.nan,
        "cost_scope": "target-change proxy; initial entry included; no drift/borrow/funding/fill model; terminal inventory open",
    }


def net_of_cost_per_name(weights, ret, cost_per_name, periods_per_year=252):
    """Net-of-cost Sharpe for a DENSE allocation matrix charging a per-name one-way
    half-spread on target-weight turnover — the calibrated-cost analogue of `net_of_cost`
    (which charges a single scalar rate on decile-LS membership turnover, the wrong
    object for a portfolio allocator). `weights` [T, N] rows are portfolio weights formed
    at t and earning `ret[t+1]`; `cost_per_name` is a length-N vector of one-way
    half-spreads (decimal). The cost of forming w[t] is Σ_i |w[t,i] − w[t-1,i]|·c_i,
    charged against that period's gross return."""
    W = np.asarray(weights, dtype=float)
    ret = np.asarray(ret, dtype=float)
    c = np.asarray(cost_per_name, dtype=float)
    if (
        W.ndim != 2
        or W.shape != ret.shape
        or c.shape != (W.shape[1],)
        or not np.isfinite(W).all()
        or not np.isfinite(ret).all()
        or not np.isfinite(c).all()
        or (c < 0).any()
    ):
        raise ValueError(
            "aligned finite weights/marks and nonnegative per-name costs required"
        )
    T = W.shape[0]
    if T < 4:
        return {
            "gross_sharpe": float("nan"),
            "net_sharpe": float("nan"),
            "turnover_per_period": float("nan"),
            "cost_drag_per_period_bps": float("nan"),
        }
    g = np.sum(W[:-1] * ret[1:], axis=1)
    turn = np.abs(np.diff(np.vstack([np.zeros((1, W.shape[1])), W[:-1]]), axis=0))
    cost = (turn * c[None, :]).sum(axis=1)
    net = g - cost
    ann = np.sqrt(periods_per_year)

    def sh(x):
        x = x[np.isfinite(x)]
        return (
            float(x.mean() / x.std() * ann) if len(x) and x.std() > 0 else float("nan")
        )

    return {
        "gross_sharpe": round(sh(g), 3),
        "net_sharpe": round(sh(net), 3),
        "turnover_per_period": round(float(np.nanmean(turn.sum(axis=1))), 3),
        "cost_drag_per_period_bps": round(float(np.nanmean(cost)) * 1e4, 2),
    }


def baseline_convergence(pred, ret, q=0.1):
    """Correlation of the long-leg return to the 1/N (equal-weight) return."""
    _, longs = decile_ls_returns(pred, ret, q, horizon=1)
    ew = np.array([_finite_mean(ret[t + 1]) for t in range(pred.shape[0] - 1)])
    m = np.isfinite(longs) & np.isfinite(ew)
    if m.sum() < MIN_PERIODS or np.std(longs[m]) == 0 or np.std(ew[m]) == 0:
        return np.nan
    return round(float(np.corrcoef(longs[m], ew[m])[0, 1]), 3)


def _finite_mean(values):
    values = values[np.isfinite(values)]
    return float(values.mean()) if len(values) else np.nan


def portfolio_baseline_convergence(weights, ret):
    """1/N-convergence control for a DENSE allocation matrix `weights` [T, N] whose
    rows are portfolio weights (e.g. an RL allocator or a softmax portfolio head),
    not a decile long-short. Returns the correlation of the portfolio's realized
    return to the equal-weight (1/N) return, and the mean absolute deviation of the
    weights from 1/N. High correlation indicates return overlap, while near-zero weight deviation
    indicates allocation similarity. Neither establishes absent factor alpha. `weights[t]` is applied to `ret[t+1]` (honest horizon)."""
    weights = np.asarray(weights, dtype=float)
    ret = np.asarray(ret, dtype=float)
    T = weights.shape[0]
    port = np.array([np.nansum(weights[t] * ret[t + 1]) for t in range(T - 1)])
    ew = np.array([np.nanmean(ret[t + 1]) for t in range(T - 1)])
    m = np.isfinite(port) & np.isfinite(ew)
    if m.sum() < 10:
        return {"corr_to_1N": float("nan"), "mean_abs_dev_from_1N": float("nan")}
    n_active = np.sum(np.isfinite(weights) & (weights != 0), axis=1, keepdims=True)
    ew_w = np.divide(
        1.0,
        n_active,
        out=np.full_like(n_active, np.nan, dtype=float),
        where=n_active > 0,
    )
    mad = float(np.nanmean(np.abs(np.nan_to_num(weights) - ew_w)))
    return {
        "corr_to_1N": round(float(np.corrcoef(port[m], ew[m])[0, 1]), 3),
        "mean_abs_dev_from_1N": round(mad, 4),
    }


def random_graph_control(pred, ret, adj, seeds=10, q=0.1, periods_per_year=252):
    """Compare the real-graph neighbor-averaged signal to an out-degree-matched per-node
    random graph. Self-loops are excluded from both the real and the random adjacency
    (the diagonal is zeroed and candidate neighbours are drawn off-diagonal), so each
    node averages only over *other* nodes and the random control never includes a node's
    own signal. This matches each node's out-degree but does not preserve the in-degree
    sequence — it is a per-node random rewiring, not a true double-edge-swap.
    Returns (real_ls_sharpe, mean_random_ls_sharpe)."""
    adj = adj.astype(float).copy()
    np.fill_diagonal(adj, 0.0)  # no self-loops in the real graph

    def neighbor_signal(a):
        deg = a.sum(1, keepdims=True)
        deg[deg == 0] = np.nan
        W = a / deg
        return np.vstack([W @ np.nan_to_num(pred[t]) for t in range(pred.shape[0])])

    def sharpe(p):
        ls, _ = decile_ls_returns(p, ret, q)
        ls = ls[np.isfinite(ls)]
        return (
            float(ls.mean() / ls.std() * np.sqrt(periods_per_year))
            if ls.std() > 0
            else np.nan
        )

    real = sharpe(neighbor_signal(adj))
    rng = np.random.default_rng(0)
    rand = []
    N = adj.shape[0]
    deg = adj.sum(1)
    for _ in range(seeds):
        ra = np.zeros_like(adj)
        for i in range(N):
            if deg[i] > 0:
                # draw out-degree-many neighbours from the off-diagonal candidates only
                cand = np.delete(np.arange(N), i)
                js = rng.choice(cand, size=min(int(deg[i]), len(cand)), replace=False)
                ra[i, js] = 1.0
        rand.append(sharpe(neighbor_signal(ra)))
    return round(real, 3), round(float(np.nanmean(rand)), 3)


def run_check(
    pred,
    ret,
    cost_bps=10.0,
    q=0.1,
    shifts=(0, 1, 2, 3),
    adj=None,
    seeds=10,
    leak_ratio_threshold=0.4,
    leak_abs_floor=0.02,
    name="signal",
    periods_per_year=252,
    weights=None,
):
    """Run the four-control battery; return the leak-collapse record + a verdict.

    `periods_per_year` sets the Sharpe annualization (252 daily, 12 monthly, etc.).
    `weights` (optional [T, N] dense allocation matrix) adds the dense-weight
    1/N-convergence control for portfolio/RL allocators that output allocations rather
    than a decile long-short.

    The leak flag is a *screening heuristic*: a large lag0/lag1 ratio is a
    heuristic symptom of a contemporaneous lookahead. The verdict
    additionally requires the honest one-period-ahead IC to be itself insignificant —
    both small in magnitude (`abs(ic1) < leak_abs_floor`) and not statistically distinct
    from zero across periods (a t-test on the per-period lag1 ICs). A signal that genuinely
    predicts at lag1 (e.g. an AR(1) reversal `pred=-ret[t]`, whose lag0 IC is also large
    by construction) is NOT flagged, because its lag1 IC clears the floor / t-test."""
    pred, ret, shifts, adj, weights = validate_inputs(
        pred,
        ret,
        shifts=shifts,
        cost_bps=cost_bps,
        q=q,
        periods_per_year=periods_per_year,
        seeds=seeds,
        adj=adj,
        weights=weights,
        leak_ratio_threshold=leak_ratio_threshold,
        leak_abs_floor=leak_abs_floor,
    )
    dose = timing_dose_response(pred, ret, shifts)
    ic0, ic1 = dose.get(0, np.nan), dose.get(1, np.nan)
    # Is the honest one-period-ahead IC itself insignificant? Test BOTH its magnitude
    # against an absolute floor AND, where lag1 is in `shifts`, a one-sample t-test on the
    # per-period lag1 ICs (cheap, and the right object: a genuine forward edge has a lag1
    # IC that is reliably non-zero across periods even if its mean magnitude is modest).
    ic1_insignificant = bool(np.isfinite(ic1) and abs(ic1) < leak_abs_floor)
    if 1 in shifts:
        per1 = _per_period_ics(pred, ret, 1)
        per1 = per1[np.isfinite(per1)]
        if per1.size >= 10 and per1.std(ddof=1) > 0:
            t_lag1 = float(per1.mean() / (per1.std(ddof=1) / np.sqrt(per1.size)))
            # honest IC is insignificant only if it also fails a |t| ~ 2 screen
            ic1_insignificant = ic1_insignificant and abs(t_lag1) < 2.0
        elif not np.isfinite(ic1):
            ic1_insignificant = True
    # leak flag: contemporaneous IC large, the honest one-period-ahead IC is a small
    # fraction of it (lives in the same period, not the future), AND that honest IC is
    # itself near-zero/insignificant — so a genuinely-predictive-at-lag1 signal whose
    # lag0 IC happens to be large too is NOT false-positived.
    ratio_symptom = bool(
        not np.isfinite(ic1) or abs(ic1) < leak_ratio_threshold * abs(ic0)
    )
    leak = bool(
        np.isfinite(ic0)
        and abs(ic0) > leak_abs_floor
        and ratio_symptom
        and ic1_insignificant
    )
    cost = net_of_cost(pred, ret, cost_bps, q, periods_per_year)
    rec = {
        "name": name,
        "timing_dose_ic": {str(k): round(v, 4) for k, v in dose.items()},
        "contemporaneous_ic_lag0": round(ic0, 4),
        "honest_ic_lag1": round(ic1, 4),
        "ic_collapse_ratio_lag1_over_lag0": round(abs(ic1) / abs(ic0), 3)
        if ic0
        else None,
        "leak_flagged": leak,
        **cost,
        "baseline_1N_corr": baseline_convergence(pred, ret, q),
    }
    if weights is not None:
        rec["portfolio_1N_convergence"] = portfolio_baseline_convergence(weights, ret)
    if adj is not None:
        has_edges = bool((adj.sum() - np.trace(adj)) > 0)
        r_sh, rand_sh = (
            random_graph_control(pred, ret, adj, seeds, q, periods_per_year)
            if has_edges
            else (np.nan, np.nan)
        )
        rec["graph_ls_sharpe"] = r_sh
        rec["random_graph_ls_sharpe_mean"] = rand_sh
        rec["graph_beats_random"] = bool(
            np.isfinite(r_sh) and np.isfinite(rand_sh) and r_sh > rand_sh + 0.1
        )
    timing_reasons, counts = [], {}
    for lag in (0, 1):
        values = _per_period_ics(pred, ret, lag) if lag in shifts else np.array([])
        finite = values[np.isfinite(values)]
        counts[f"finite_lag{lag}_periods"] = len(finite)
        if lag not in shifts:
            timing_reasons.append(f"required lag {lag} was not requested")
        elif len(finite) < MIN_PERIODS:
            timing_reasons.append(
                f"lag {lag} needs {MIN_PERIODS} valid periods with {MIN_NAMES} finite nonconstant name pairs each"
            )
        elif lag == 1 and finite.std(ddof=1) == 0:
            timing_reasons.append("lag-1 IC variation is zero; t-screen undefined")
    coverage = {
        "timing": status(
            timing_reasons,
            minimum_names=MIN_NAMES,
            minimum_periods=MIN_PERIODS,
            **counts,
        ),
        "cost": status(
            []
            if all(
                np.isfinite(cost[k])
                for k in (
                    "gross_sharpe",
                    "net_sharpe",
                    "turnover_per_period",
                    "cost_drag_per_period_bps",
                )
            )
            else ["undefined gross/net Sharpe, turnover or selected marks"],
            accounting="target-turnover sensitivity; not funded portfolio performance",
        ),
        "baseline": status(
            []
            if np.isfinite(rec["baseline_1N_corr"])
            else ["baseline correlation needs ten valid nonconstant paired periods"]
        ),
        "dense_baseline": {"status": "NOT_REQUESTED", "reasons": []},
        "graph": {"status": "NOT_REQUESTED", "reasons": []},
    }
    if weights is not None:
        coverage["dense_baseline"] = status(
            []
            if all(np.isfinite(v) for v in rec["portfolio_1N_convergence"].values())
            else ["dense baseline correlation/weight diagnostic undefined"]
        )
    if adj is not None:
        coverage["graph"] = status(
            []
            if np.isfinite(r_sh) and np.isfinite(rand_sh)
            else ["no usable off-diagonal graph comparison or finite spread Sharpe"]
        )
    result = finalize_screen(rec, coverage)
    result["report_schema"] = "quantem-checker/3"
    result["screen_scope"] = (
        "diagnostic heuristics, not a calibrated leakage detector or economic certification"
    )
    return result
