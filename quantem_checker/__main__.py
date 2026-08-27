"""Quantem Checker CLI: run the four-control battery on a predictions + returns panel.

    quantem-checker --predictions pred.parquet --returns ret.parquet \
        [--cost-bps 10] [--q 0.1] [--adjacency adj.npy] [--format table|json] [--json out.json]

Both parquets are wide panels indexed by date with one column per asset; columns are
inner-joined and rows aligned. pred[t] is intended to predict the return in t+1.

Exit code is 0 if the signal survives the battery, 1 if it does not — so quantem-checker can
gate a CI pipeline.
"""
from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import pandas as pd

from quantem_checker.core import run_check


def _format_table(rec):
    dose = rec["timing_dose_ic"]
    dose_str = "  ".join(f"k={k}:{v:+.3f}" for k, v in dose.items())
    lines = [
        f"Quantem Checker — {rec['name']}",
        "─" * 56,
        f"  1. timing dose-response   {dose_str}",
        f"     contemporaneous (k=0)  {rec['contemporaneous_ic_lag0']:+.4f}",
        f"     honest (k=1)           {rec['honest_ic_lag1']:+.4f}",
        f"     collapse ratio k1/k0   {rec['ic_collapse_ratio_lag1_over_lag0']}",
        f"     leak flagged           {rec['leak_flagged']}",
        f"  2. net-of-cost            gross Sharpe {rec['gross_sharpe']}  →  net {rec['net_sharpe']}",
        f"     turnover / cost drag   {rec['turnover_per_period']} / {rec['cost_drag_per_period_bps']} bps",
        f"  3. 1/N convergence corr   {rec['baseline_1N_corr']}",
    ]
    if "portfolio_1N_convergence" in rec:
        c = rec["portfolio_1N_convergence"]
        lines.append(f"     dense-weight 1/N corr  {c['corr_to_1N']}  (mad {c['mean_abs_dev_from_1N']})")
    if "graph_ls_sharpe" in rec:
        lines.append(f"  4. graph vs random        {rec['graph_ls_sharpe']} vs {rec['random_graph_ls_sharpe_mean']}"
                     f"  (beats random: {rec['graph_beats_random']})")
    lines += ["─" * 56, f"  VERDICT: {rec['verdict']}"]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="quantem-checker", description="four-control leak forensics")
    ap.add_argument("--predictions", required=True, help="wide parquet: date x asset scores")
    ap.add_argument("--returns", required=True, help="wide parquet: date x asset returns")
    ap.add_argument("--cost-bps", type=float, default=10.0)
    ap.add_argument("--q", type=float, default=0.1, help="decile fraction (0.1 = deciles)")
    ap.add_argument("--adjacency", default=None, help="optional .npy boolean [N,N] graph")
    ap.add_argument("--periods-per-year", type=int, default=252, help="Sharpe annualization (252 daily, 12 monthly)")
    ap.add_argument("--leak-ratio-threshold", type=float, default=0.4,
                    help="lag1/lag0 IC ratio below which the leak symptom is present")
    ap.add_argument("--leak-abs-floor", type=float, default=0.02,
                    help="absolute level below which the honest-horizon IC is treated as insignificant")
    ap.add_argument("--name", default="signal")
    ap.add_argument("--format", choices=("table", "json"), default="table")
    ap.add_argument("--json", default=None, help="also write the record to this path")
    args = ap.parse_args(argv)

    pred = pd.read_parquet(args.predictions)
    ret = pd.read_parquet(args.returns)
    cols = [c for c in pred.columns if c in ret.columns]
    idx = pred.index.intersection(ret.index)
    pred = pred.loc[idx, cols]; ret = ret.loc[idx, cols]
    adj = np.load(args.adjacency) if args.adjacency else None

    rec = run_check(pred.to_numpy(), ret.to_numpy(), cost_bps=args.cost_bps,
                        q=args.q, adj=adj, leak_ratio_threshold=args.leak_ratio_threshold,
                        leak_abs_floor=args.leak_abs_floor, name=args.name,
                        periods_per_year=args.periods_per_year)
    print(_format_table(rec) if args.format == "table" else json.dumps(rec, indent=2))
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(rec, fh, indent=2)
    return 0 if rec["survives_battery"] else 1


if __name__ == "__main__":
    sys.exit(main())
