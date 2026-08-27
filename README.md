# Quantem Checker

**A model-agnostic forensic harness for detecting lookahead and leakage in financial-ML backtests.**

Most reported edges in financial machine learning do not survive an honest evaluation. The
usual culprits are mundane and recurring: a feature that quietly peeks at the same period it
is supposed to predict, returns reported gross of transaction costs, an "alpha" that is the
equal-weight premium in disguise, or a relational graph that performs no better than a random
one. `quantem-checker` runs your predictions through four controls that catch these failure modes
and emits a single collapse table — with no coupling to your model.

Point it at an aligned predictions panel and a returns panel and it tells you, in one call,
whether the edge is real or an evaluation artifact.

```bash
pip install -e .            # from a clone; PyPI distribution name TBD
```

`quantem-checker` depends only on `numpy` and `pandas`.

## 30-second quickstart

```python
import numpy as np
from quantem_checker import run_check

# pred[t, n]: score for asset n formed at the end of period t, meant to predict t+1.
# ret[t, n]:  asset n's realized return IN period t.  Both [T, N], NaN allowed.
rec = run_check(pred, ret, cost_bps=10.0)

print(rec["verdict"])
# -> "LEAK: contemporaneous IC collapses under honest timing"
#    "survives the four-control battery"
#    "fails net-of-cost or converges to the 1/N baseline"
```

Or from the command line, on two wide parquet panels (date × asset):

```bash
quantem-checker --predictions pred.parquet --returns ret.parquet --cost-bps 10
```

```
Quantem Checker — signal
────────────────────────────────────────────────────────
  1. timing dose-response   k=0:+0.184  k=1:+0.002  k=2:-0.001
     contemporaneous (k=0)  +0.1840
     honest (k=1)           +0.0020
     collapse ratio k1/k0   0.011
     leak flagged           True
  2. net-of-cost            gross Sharpe 7.81  →  net -0.42
     turnover / cost drag   0.93 / 18.6 bps
  3. 1/N convergence corr   0.991
────────────────────────────────────────────────────────
  VERDICT: LEAK: contemporaneous IC collapses under honest timing
```

The CLI exits `0` if the signal survives and `1` if it does not, so you can wire `quantem-checker`
into a pipeline as a gate on a candidate signal.

## The four controls

| # | Control | Catches |
|---|---------|---------|
| 1 | **Honest-timing dose-response** — rank-IC of `pred[t]` vs `ret[t+k]` for `k = 0,1,2,…` | A leaked signal has large contemporaneous IC (`k=0`) that collapses to ≈0 by the honest one-period-ahead horizon (`k=1`). The dose-response makes the leak a continuous, visible function of how much lookahead you permit. |
| 2 | **Net-of-cost** — decile long-short Sharpe gross vs net of a per-side cost charged on realized turnover | An edge that exists gross but evaporates once you pay for the turnover that produced it. |
| 3 | **Naive-baseline convergence** — correlation of the strategy return to a 1/N (equal-weight) portfolio | An "alpha" that is the equal-weight premium in disguise. A dense-weight variant (`weights=…`) flags RL/softmax allocators that have silently converged to 1/N. |
| 4 | **Random-graph control** (optional) — graph-neighbor-averaged signal vs an out-degree-matched per-node random graph | A relational/GNN model whose graph carries no more signal than a random one of the same per-node out-degree (self-loops excluded from both). |

`run_check` returns a JSON-safe record with every intermediate number and a boolean
`leak_flagged` / `survives_battery` verdict.

**The leak flag is a screening heuristic, not a proof.** A large lag0/lag1 IC ratio is a
*necessary-not-sufficient* symptom of a contemporaneous lookahead: the verdict only fires
when the honest-horizon (`k=1`) IC is *itself* insignificant — both below a small absolute
floor (`leak_abs_floor`, default `0.02`) and not statistically distinct from zero across
periods (a t-test on the per-period lag1 ICs). This matters because an honest signal can
condition on the most recent return and so have a large lag0 IC by construction — e.g. an
AR(1) reversal `pred = -ret[t]` has a lag0 IC near −1 yet genuinely predicts `t+1`; the
floor/t-test gate keeps it from being false-flagged. Likewise the four-control booleans
(`leak_flagged`, `graph_beats_random`, …) are a *screen*: the load-bearing negative results
rest on downstream factor-model / cluster-robust statistics, not on these booleans alone.
`examples/specificity_grid.py` sweeps (leak strength × forward strength × autocorrelation)
and prints a confusion matrix so the Type-I / Type-II rates are stated numbers, with a
short threshold-sensitivity note on the two magic constants (`0.02` floor, `0.4` ratio).

## Convention

This is the whole contract, and getting it right is the point:

- `pred[t, n]` is the score for asset `n` formed from information available **at the end of
  period `t`**, intended to predict the return realized in period **`t+1`**.
- `ret[t, n]` is asset `n`'s realized return **in** period `t`.

So an honest signal lives at `k=1` (predicts the future); a leak lives at `k=0` (correlates
with the present). If your contemporaneous IC dwarfs your one-period-ahead IC, you have a
lookahead, and `quantem-checker` will say so.

## Validation

`quantem-checker` is checked against signals with known ground truth (`tests/`):

- a synthetic **contemporaneous leak** it must flag,
- a **clean forward** signal it must pass,
- a **churning allocator** whose net Sharpe must fall below gross,
- and **hard-negative** honest signals it must NOT flag even though their lag0 IC is large:
  an AR(1) reversal `pred = -ret[t]`, a value signal with a lagged-price denominator, and
  overlapping/EWMA momentum.

Reproduce the ground-truth demo yourself:

```bash
python examples/synthetic_demo.py     # flags the leak, passes the clean signal
python examples/specificity_grid.py   # Type-I / Type-II rates + threshold sensitivity
pytest                                # the full golden-master suite
```

## API

```python
from quantem_checker import (
    run_check,                  # the full battery + verdict
    timing_dose_response,           # control 1
    net_of_cost,                    # control 2 (decile long-short)
    net_of_cost_per_name,           # control 2 (dense allocator, per-name spreads)
    baseline_convergence,           # control 3 (long-short)
    portfolio_baseline_convergence, # control 3 (dense allocator)
    random_graph_control,           # control 4
    decile_ls_returns,
)
```

`run_check(pred, ret, cost_bps=10.0, q=0.1, shifts=(0,1,2,3), adj=None, seeds=10,
leak_ratio_threshold=0.4, leak_abs_floor=0.02, name="signal", periods_per_year=252,
weights=None)`. Set `periods_per_year` to match your frequency (252 daily, 12 monthly).
`leak_ratio_threshold` is the lag1/lag0 ratio below which the leak *symptom* is present;
`leak_abs_floor` is the absolute level below which the honest-horizon IC is treated as
insignificant (the floor/t-test gate that prevents false-positives on signals that
legitimately condition on the latest return). Pass a boolean `[N, N]` adjacency as `adj`
to run the random-graph control, or a dense `[T, N]` allocation matrix as `weights` to run
the dense-weight 1/N-convergence control.

## License

MIT.
