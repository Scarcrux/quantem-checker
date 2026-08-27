"""Quantem Checker — a model-agnostic forensic harness for the four-control battery.

Most reported edges in financial machine learning do not survive an honest evaluation.
`quantem-checker` is the model-agnostic entry point for the four controls that catch the common
failure modes: feed it an aligned predictions panel and a returns panel and it emits the
leak-collapse table, with no coupling to any particular model.

Convention. `pred[t, n]` is the score for asset n formed from information available at
the end of period t, intended to predict the return realized in period t+1. `ret[t, n]`
is asset n's realized return IN period t. Both are [T, N] float arrays, NaN allowed.

The four controls:
  1. Honest-timing dose-response. IC of pred[t] against ret[t+k] for k = 0,1,2,...
     k=0 is the contemporaneous leak (the signal scored against the SAME period's
     return); k=1 is the honest one-period-ahead horizon. A leaked signal has large
     contemporaneous IC that collapses to ~0 by k=1.
  2. Net-of-cost. The honest (k=1) decile long-short Sharpe gross vs net of a per-side
     cost charged on realized turnover.
  3. Naive-baseline convergence. Correlation of the strategy's long-short return to a
     1/N (equal-weight) portfolio return: a high correlation means the "alpha" is the
     equal-weight premium in disguise.
  4. Random-graph control (optional). If a boolean adjacency is supplied, compare the
     graph-neighbor-averaged signal to an out-degree-matched per-node random graph
     (self-loops excluded from both).

The four booleans (`leak_flagged`, `graph_beats_random`, ...) are a SCREEN: the leak
flag in particular is a necessary-not-sufficient symptom (a large lag0/lag1 ratio that
must also have an insignificant honest-horizon IC before the verdict fires), and the
load-bearing negative results rest on downstream factor-model / cluster-robust statistics,
not on these screening booleans alone.
"""
from __future__ import annotations

import numpy as np


def _rankdata(a):
    order = a.argsort()
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(len(a))
    return ranks


def _row_ic(pred_row, ret_row):
    m = np.isfinite(pred_row) & np.isfinite(ret_row)
    if m.sum() < 10 or np.nanstd(pred_row[m]) == 0 or np.nanstd(ret_row[m]) == 0:
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
        out[k] = float(np.nanmean(_per_period_ics(pred, ret, k)))
    return out


def decile_ls_returns(pred, ret, q=0.1, horizon=1):
    """Per-period decile long-short return earning ret[t+horizon] (honest horizon=1)."""
    T, N = pred.shape
    k = max(1, int(N * q))
    out, longs = [], []
    for t in range(T - horizon):
        s = pred[t]; r = ret[t + horizon]
        m = np.isfinite(s) & np.isfinite(r)
        if m.sum() < 2 * k:
            out.append(np.nan); longs.append(np.nan); continue
        idx = np.where(m)[0]
        order = idx[np.argsort(s[idx])]
        lo, hi = order[:k], order[-k:]
        out.append(r[hi].mean() - r[lo].mean())
        longs.append(r[hi].mean())
    return np.array(out), np.array(longs)


def _turnover(pred, q=0.1):
    """Mean per-period one-way turnover of the decile long-short membership."""
    T, N = pred.shape
    k = max(1, int(N * q))
    prev_hi = prev_lo = None
    turns = []
    for t in range(T):
        s = pred[t]; m = np.isfinite(s)
        if m.sum() < 2 * k:
            continue
        idx = np.where(m)[0]; order = idx[np.argsort(s[idx])]
        hi, lo = set(order[-k:].tolist()), set(order[:k].tolist())
        if prev_hi is not None:
            ch = len(hi ^ prev_hi) + len(lo ^ prev_lo)
            turns.append(ch / (2 * k))      # fraction of the book replaced
        prev_hi, prev_lo = hi, lo
    return float(np.nanmean(turns)) if turns else np.nan


def net_of_cost(pred, ret, cost_bps=10.0, q=0.1, periods_per_year=252):
    ls, _ = decile_ls_returns(pred, ret, q, horizon=1)
    ls = ls[np.isfinite(ls)]
    ann = np.sqrt(periods_per_year)
    gross_sh = float(ls.mean() / ls.std() * ann) if ls.std() > 0 else np.nan
    turn = _turnover(pred, q)
    cost_per_period = turn * 2 * (cost_bps / 1e4)    # both legs, per period
    net = ls - cost_per_period
    net_sh = float(net.mean() / net.std() * ann) if net.std() > 0 else np.nan
    return {"gross_sharpe": round(gross_sh, 3), "net_sharpe": round(net_sh, 3),
            "turnover_per_period": round(turn, 3), "cost_drag_per_period_bps": round(cost_per_period * 1e4, 2)}


def net_of_cost_per_name(weights, ret, cost_per_name, periods_per_year=252):
    """Net-of-cost Sharpe for a DENSE allocation matrix charging a per-name one-way
    half-spread on realized turnover — the calibrated-cost analogue of `net_of_cost`
    (which charges a single scalar rate on decile-LS membership turnover, the wrong
    object for a portfolio allocator). `weights` [T, N] rows are portfolio weights formed
    at t and earning `ret[t+1]`; `cost_per_name` is a length-N vector of one-way
    half-spreads (decimal). The cost of forming w[t] is Σ_i |w[t,i] − w[t-1,i]|·c_i,
    charged against that period's gross return."""
    W = np.nan_to_num(np.asarray(weights, dtype=float))
    ret = np.asarray(ret, dtype=float)
    c = np.asarray(cost_per_name, dtype=float)
    T = W.shape[0]
    if T < 4:
        return {"gross_sharpe": float("nan"), "net_sharpe": float("nan"),
                "turnover_per_period": float("nan"), "cost_drag_per_period_bps": float("nan")}
    g = np.nansum(W[1:T - 1] * ret[2:T], axis=1)               # gross for t=1..T-2, earning ret[t+1]
    turn = np.abs(W[1:T - 1] - W[0:T - 2])                      # turnover forming w[t]
    cost = (turn * c[None, :]).sum(axis=1)
    net = g - cost
    ann = np.sqrt(periods_per_year)

    def sh(x):
        x = x[np.isfinite(x)]
        return float(x.mean() / x.std() * ann) if len(x) and x.std() > 0 else float("nan")
    return {"gross_sharpe": round(sh(g), 3), "net_sharpe": round(sh(net), 3),
            "turnover_per_period": round(float(np.nanmean(turn.sum(axis=1))), 3),
            "cost_drag_per_period_bps": round(float(np.nanmean(cost)) * 1e4, 2)}


def baseline_convergence(pred, ret, q=0.1):
    """Correlation of the long-leg return to the 1/N (equal-weight) return."""
    _, longs = decile_ls_returns(pred, ret, q, horizon=1)
    ew = np.array([np.nanmean(ret[t + 1]) for t in range(pred.shape[0] - 1)])
    m = np.isfinite(longs) & np.isfinite(ew)
    if m.sum() < 10:
        return np.nan
    return round(float(np.corrcoef(longs[m], ew[m])[0, 1]), 3)


def portfolio_baseline_convergence(weights, ret):
    """1/N-convergence control for a DENSE allocation matrix `weights` [T, N] whose
    rows are portfolio weights (e.g. an RL allocator or a softmax portfolio head),
    not a decile long-short. Returns the correlation of the portfolio's realized
    return to the equal-weight (1/N) return, and the mean absolute deviation of the
    weights from 1/N. A high correlation (or a near-zero deviation) means the learned
    allocation is an equal-weight portfolio in disguise — the dense-weight analogue of
    `baseline_convergence`. `weights[t]` is applied to `ret[t+1]` (honest horizon)."""
    weights = np.asarray(weights, dtype=float)
    ret = np.asarray(ret, dtype=float)
    T = weights.shape[0]
    port = np.array([np.nansum(weights[t] * ret[t + 1]) for t in range(T - 1)])
    ew = np.array([np.nanmean(ret[t + 1]) for t in range(T - 1)])
    m = np.isfinite(port) & np.isfinite(ew)
    if m.sum() < 10:
        return {"corr_to_1N": float("nan"), "mean_abs_dev_from_1N": float("nan")}
    n_active = np.sum(np.isfinite(weights) & (weights != 0), axis=1, keepdims=True)
    ew_w = np.divide(1.0, n_active, out=np.full_like(n_active, np.nan, dtype=float), where=n_active > 0)
    mad = float(np.nanmean(np.abs(np.nan_to_num(weights) - ew_w)))
    return {"corr_to_1N": round(float(np.corrcoef(port[m], ew[m])[0, 1]), 3),
            "mean_abs_dev_from_1N": round(mad, 4)}


def random_graph_control(pred, ret, adj, seeds=10, q=0.1, periods_per_year=252):
    """Compare the real-graph neighbor-averaged signal to an out-degree-matched per-node
    random graph. Self-loops are excluded from both the real and the random adjacency
    (the diagonal is zeroed and candidate neighbours are drawn off-diagonal), so each
    node averages only over *other* nodes and the random control never includes a node's
    own signal. This matches each node's out-degree but does not preserve the in-degree
    sequence — it is a per-node random rewiring, not a true double-edge-swap.
    Returns (real_ls_sharpe, mean_random_ls_sharpe)."""
    adj = adj.astype(float).copy()
    np.fill_diagonal(adj, 0.0)                       # no self-loops in the real graph
    def neighbor_signal(a):
        deg = a.sum(1, keepdims=True); deg[deg == 0] = np.nan
        W = a / deg
        return np.vstack([W @ np.nan_to_num(pred[t]) for t in range(pred.shape[0])])
    def sharpe(p):
        ls, _ = decile_ls_returns(p, ret, q); ls = ls[np.isfinite(ls)]
        return float(ls.mean() / ls.std() * np.sqrt(periods_per_year)) if ls.std() > 0 else np.nan
    real = sharpe(neighbor_signal(adj))
    rng = np.random.default_rng(0)
    rand = []
    N = adj.shape[0]
    deg = adj.sum(1)
    for s in range(seeds):
        ra = np.zeros_like(adj)
        for i in range(N):
            if deg[i] > 0:
                # draw out-degree-many neighbours from the off-diagonal candidates only
                cand = np.delete(np.arange(N), i)
                js = rng.choice(cand, size=min(int(deg[i]), len(cand)), replace=False)
                ra[i, js] = 1.0
        rand.append(sharpe(neighbor_signal(ra)))
    return round(real, 3), round(float(np.nanmean(rand)), 3)


def run_check(pred, ret, cost_bps=10.0, q=0.1, shifts=(0, 1, 2, 3),
                  adj=None, seeds=10, leak_ratio_threshold=0.4, leak_abs_floor=0.02,
                  name="signal", periods_per_year=252, weights=None):
    """Run the four-control battery; return the leak-collapse record + a verdict.

    `periods_per_year` sets the Sharpe annualization (252 daily, 12 monthly, etc.).
    `weights` (optional [T, N] dense allocation matrix) adds the dense-weight
    1/N-convergence control for portfolio/RL allocators that output allocations rather
    than a decile long-short.

    The leak flag is a *screening heuristic*: a large lag0/lag1 ratio is a
    necessary-not-sufficient symptom of a contemporaneous lookahead. The verdict
    additionally requires the honest one-period-ahead IC to be itself insignificant —
    both small in magnitude (`abs(ic1) < leak_abs_floor`) and not statistically distinct
    from zero across periods (a t-test on the per-period lag1 ICs). A signal that genuinely
    predicts at lag1 (e.g. an AR(1) reversal `pred=-ret[t]`, whose lag0 IC is also large
    by construction) is NOT flagged, because its lag1 IC clears the floor / t-test."""
    pred = np.asarray(pred, dtype=float); ret = np.asarray(ret, dtype=float)
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
    ratio_symptom = bool(not np.isfinite(ic1) or abs(ic1) < leak_ratio_threshold * abs(ic0))
    leak = bool(np.isfinite(ic0) and abs(ic0) > leak_abs_floor and
                ratio_symptom and ic1_insignificant)
    cost = net_of_cost(pred, ret, cost_bps, q, periods_per_year)
    rec = {"name": name, "timing_dose_ic": {str(k): round(v, 4) for k, v in dose.items()},
           "contemporaneous_ic_lag0": round(ic0, 4), "honest_ic_lag1": round(ic1, 4),
           "ic_collapse_ratio_lag1_over_lag0": round(abs(ic1) / abs(ic0), 3) if ic0 else None,
           "leak_flagged": leak, **cost,
           "baseline_1N_corr": baseline_convergence(pred, ret, q)}
    if weights is not None:
        rec["portfolio_1N_convergence"] = portfolio_baseline_convergence(weights, ret)
    if adj is not None:
        r_sh, rand_sh = random_graph_control(pred, ret, adj, seeds, q, periods_per_year)
        rec["graph_ls_sharpe"] = r_sh; rec["random_graph_ls_sharpe_mean"] = rand_sh
        rec["graph_beats_random"] = bool(np.isfinite(r_sh) and np.isfinite(rand_sh) and r_sh > rand_sh + 0.1)
    conv1n = (rec.get("portfolio_1N_convergence") or {}).get("corr_to_1N")
    survives = bool((not leak) and np.isfinite(cost["net_sharpe"]) and cost["net_sharpe"] > 0.2
                    and (rec["baseline_1N_corr"] is None or abs(rec["baseline_1N_corr"]) < 0.95)
                    and (conv1n is None or not np.isfinite(conv1n) or abs(conv1n) < 0.95))
    rec["survives_battery"] = survives
    rec["verdict"] = ("survives the four-control battery" if survives else
                      ("LEAK: contemporaneous IC collapses under honest timing" if leak else
                       "fails net-of-cost or converges to the 1/N baseline"))
    return rec