"""Golden-master tests for the model-agnostic quantem-checker harness.

The battery is validated against three known-ground-truth signals: a synthetic
contemporaneous leak it must flag, a clean forward signal it must pass, and a churning
allocator whose net Sharpe must fall below gross.
"""
import numpy as np

from quantem_checker import run_check, timing_dose_response


def _leaked(T=200, N=120, lam=0.3, seed=0):
    """A signal correlated with the SAME period's return — a contemporaneous leak."""
    rng = np.random.default_rng(seed)
    ret = rng.standard_normal((T, N))
    pred = lam * ret + np.sqrt(1 - lam ** 2) * rng.standard_normal((T, N))
    return pred, ret


def _clean_forward(T=200, N=120, lam=0.25, seed=1):
    """A signal correlated with NEXT period's return — a clean forward signal."""
    rng = np.random.default_rng(seed)
    ret = rng.standard_normal((T, N))
    pred = np.empty((T, N))
    pred[:-1] = lam * ret[1:] + np.sqrt(1 - lam ** 2) * rng.standard_normal((T - 1, N))
    pred[-1] = rng.standard_normal(N)
    return pred, ret


def test_leak_is_flagged():
    pred, ret = _leaked()
    rec = run_check(pred, ret, name="leaked")
    assert rec["leak_flagged"] is True
    assert rec["contemporaneous_ic_lag0"] > 0.1
    assert abs(rec["honest_ic_lag1"]) < 0.05
    assert rec["survives_battery"] is False


def test_clean_forward_not_flagged():
    pred, ret = _clean_forward()
    rec = run_check(pred, ret, name="clean")
    assert rec["leak_flagged"] is False
    assert rec["honest_ic_lag1"] > abs(rec["contemporaneous_ic_lag0"])


def test_dose_response_monotone_collapse_for_leak():
    pred, ret = _leaked()
    dose = timing_dose_response(pred, ret, shifts=(0, 1, 2))
    assert dose[0] > 0.1
    assert abs(dose[1]) < 0.05 and abs(dose[2]) < 0.05


def test_returns_json_safe_types():
    import json
    pred, ret = _leaked(T=80, N=60)
    rec = run_check(pred, ret)
    json.dumps(rec)  # must not raise (no numpy scalar types leak through)


def test_periods_per_year_scales_sharpe():
    from quantem_checker import net_of_cost
    pred, ret = _clean_forward(T=240, N=100)
    daily = net_of_cost(pred, ret, periods_per_year=252)["gross_sharpe"]
    monthly = net_of_cost(pred, ret, periods_per_year=12)["gross_sharpe"]
    # same per-period series, only the annualization differs
    assert abs(daily / monthly - (252 / 12) ** 0.5) < 1e-6


def test_net_of_cost_per_name():
    from quantem_checker import net_of_cost_per_name
    rng = np.random.default_rng(5)
    T, N = 300, 20
    ret = rng.standard_normal((T, N)) * 0.01
    # a churning allocator: random dense weights each period -> high turnover -> net << gross
    raw = rng.standard_normal((T, N))
    W = np.exp(raw - raw.max(axis=1, keepdims=True)); W /= W.sum(axis=1, keepdims=True)
    cost = np.full(N, 0.001)                     # 10 bps per name
    rec = net_of_cost_per_name(W, ret, cost)
    assert np.isfinite(rec["gross_sharpe"]) and np.isfinite(rec["net_sharpe"])
    assert rec["net_sharpe"] < rec["gross_sharpe"]      # cost reduces Sharpe
    assert rec["turnover_per_period"] > 0
    # per-name cost with a higher spread on every name charges more drag
    rec_hi = net_of_cost_per_name(W, ret, np.full(N, 0.005), 252)
    assert rec_hi["cost_drag_per_period_bps"] > rec["cost_drag_per_period_bps"]


def test_dense_weight_convergence_flags_1N():
    from quantem_checker import portfolio_baseline_convergence, run_check
    rng = np.random.default_rng(3)
    T, N = 200, 30
    ret = rng.standard_normal((T, N))
    eqw = np.full((T, N), 1.0 / N)                      # a 1/N allocator in disguise
    conv = portfolio_baseline_convergence(eqw, ret)
    assert conv["corr_to_1N"] > 0.99 and conv["mean_abs_dev_from_1N"] < 1e-6
    # a concentrated allocator is distinct from 1/N
    conc = np.zeros((T, N)); conc[:, 0] = 1.0
    assert portfolio_baseline_convergence(conc, ret)["corr_to_1N"] < 0.5
    # run_check threads weights + periods_per_year (RL allocator path)
    pred = rng.standard_normal((T, N))
    rec = run_check(pred, ret, periods_per_year=252, weights=eqw, name="rl")
    assert "portfolio_1N_convergence" in rec
    assert rec["portfolio_1N_convergence"]["corr_to_1N"] > 0.99


# ---------------------------------------------------------------------------
# HARD-NEGATIVE golden masters: honest signals the tool MUST NOT flag as leaks,
# even though their contemporaneous (lag0) IC is large. These guard against the
# leak-flag false-positiving on signals that legitimately condition on the most
# recent return / a lagged denominator.
# ---------------------------------------------------------------------------

def _ar1_reversal(T=400, N=150, phi=-0.15, sigma=0.1, seed=7):
    """An AR(1) process with negative autocorrelation, traded by a reversal rule
    pred[t] = -ret[t]. This is an HONEST signal: because ret[t+1] = phi*ret[t] + eps and
    phi<0, -ret[t] genuinely predicts ret[t+1] (a real lag1 edge). It also has a large
    lag0 IC by construction (pred is -ret of the same period), which is exactly the
    pattern the naive ratio test mistook for a leak."""
    rng = np.random.default_rng(seed)
    ret = np.empty((T, N))
    ret[0] = rng.standard_normal(N) * sigma
    for t in range(1, T):
        ret[t] = phi * ret[t - 1] + rng.standard_normal(N) * sigma
    pred = -ret                                          # condition on the latest return
    return pred, ret


def test_ar1_reversal_not_flagged():
    """Honest AR(1) reversal: strong real lag1 signal must NOT be flagged as a leak,
    even though its lag0 IC is large (it conditions on the latest return)."""
    pred, ret = _ar1_reversal()
    rec = run_check(pred, ret, name="ar1-reversal")
    # genuine forward edge: lag1 IC is real and clears the floor
    assert abs(rec["honest_ic_lag1"]) > 0.05
    assert rec["leak_flagged"] is False
    assert rec["survives_battery"] is True


def _value_lagged_denominator(T=400, N=150, seed=11):
    """A value-style signal pred[t] = fundamental / price[t-1] (lagged denominator).
    The fundamental is fixed per name; the signal predicts a mild forward return tilt.
    Uses only information available at the end of t (price[t-1] is one period stale),
    so it is honest — but the lagged price makes pred[t] correlated with ret[t] too."""
    rng = np.random.default_rng(seed)
    fundamental = np.abs(rng.standard_normal(N)) + 1.0
    log_price = np.cumsum(rng.standard_normal((T, N)) * 0.05, axis=0) + 3.0
    price = np.exp(log_price)
    pred = np.empty((T, N))
    pred[0] = fundamental / price[0]
    pred[1:] = fundamental / price[:-1]                  # lagged denominator (price[t-1])
    # a real forward tilt: cheap names (high pred) earn a small positive next-period return
    z = (pred - pred.mean(axis=1, keepdims=True)) / (pred.std(axis=1, keepdims=True) + 1e-9)
    ret = 0.12 * np.vstack([z[max(t - 1, 0)] for t in range(T)]) + rng.standard_normal((T, N)) * 0.1
    return pred, ret


def test_value_lagged_denominator_not_flagged():
    """Value signal with a lagged-price denominator: honest, must not be flagged."""
    pred, ret = _value_lagged_denominator()
    rec = run_check(pred, ret, name="value-lagged-denom")
    assert rec["leak_flagged"] is False


def _ewma_momentum(T=400, N=150, halflife=10, seed=13):
    """Overlapping / EWMA momentum: pred[t] is an exponentially-weighted average of past
    returns through t-1 (overlapping windows -> autocorrelated signal), predicting a small
    momentum continuation. Honest (uses only past returns) but persistent across periods."""
    rng = np.random.default_rng(seed)
    ret_noise = rng.standard_normal((T, N)) * 0.1
    alpha = 1 - 0.5 ** (1.0 / halflife)
    ewma = np.zeros((T, N))
    ret = np.empty((T, N))
    ret[0] = ret_noise[0]
    for t in range(1, T):
        ewma[t] = (1 - alpha) * ewma[t - 1] + alpha * ret[t - 1]
        ret[t] = 0.08 * ewma[t] + ret_noise[t]           # momentum continuation
    pred = ewma                                          # overlapping EWMA momentum signal
    return pred, ret


def test_ewma_momentum_not_flagged():
    """Overlapping EWMA momentum: honest, must not be flagged as a leak."""
    pred, ret = _ewma_momentum()
    rec = run_check(pred, ret, name="ewma-momentum")
    assert rec["leak_flagged"] is False


def test_timing_dose_response_per_lag_bound():
    """[P2-truncbug] regression: each lag's IC must use a per-lag bound (T - k), so the
    k=1 IC is identical regardless of which other shifts are requested in the same call."""
    rng = np.random.default_rng(17)
    T, N = 120, 40
    ret = rng.standard_normal((T, N))
    pred = np.empty((T, N))
    pred[:-1] = 0.2 * ret[1:] + rng.standard_normal((T - 1, N))
    pred[-1] = rng.standard_normal(N)
    a = timing_dose_response(pred, ret, (0, 1))
    b = timing_dose_response(pred, ret, (0, 1, 2, 3))
    assert a[1] == b[1]
    assert a[0] == b[0]


def test_random_graph_control_no_self_loops():
    """[P2-randgraph] regression: the real graph's diagonal is zeroed and the random
    control draws only off-diagonal neighbours, so a node never averages its own signal."""
    from quantem_checker import random_graph_control
    rng = np.random.default_rng(19)
    T, N = 150, 40
    ret = rng.standard_normal((T, N))
    pred = rng.standard_normal((T, N))
    adj = (rng.random((N, N)) < 0.2)
    np.fill_diagonal(adj, True)                          # adversarial: self-loops present
    real, rand = random_graph_control(pred, ret, adj, seeds=5)
    # must run without error and return finite Sharpes despite the seeded self-loops
    assert np.isfinite(real) and np.isfinite(rand)
