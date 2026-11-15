"""Local diagnostics on aligned panels, or an offline generated-control demo.

Legacy flags remain available. Panel axes must match exactly; no inner join.
Exit 0: requested screens not flagged; 1: flagged; 2: invalid/insufficient input.
None is a certification of authentic inputs, profitability or absence of leakage.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from .audit_demo import demo_report
from .core import run_check


def _number(value, digits=4, sign=False):
    if value is None:
        return "not tested"
    return format(value, f"{'+' if sign else ''}.{digits}f")


def _format_table(rec):
    dose = "  ".join(
        f"k={k}:{_number(v, 3, True)}" for k, v in rec["timing_dose_ic"].items()
    )
    lines = [
        f"Quantem Checker — {rec['name']}",
        "─" * 56,
        f"  1. timing dose-response   {dose}",
        f"     same-period IC         {_number(rec['contemporaneous_ic_lag0'], sign=True)}",
        f"     declared next-period IC {_number(rec['honest_ic_lag1'], sign=True)}",
        f"     collapse ratio k1/k0   {rec['ic_collapse_ratio_lag1_over_lag0']}",
        f"     timing flag            {rec['leak_flagged'] if rec['leak_flagged'] is not None else 'NOT TESTED'}",
        f"  2. cost proxy             gross Sharpe {_number(rec['gross_sharpe'], 3)} → net {_number(rec['net_sharpe'], 3)}",
        f"     turnover / cost drag   {_number(rec['turnover_per_period'], 3)} / {_number(rec['cost_drag_per_period_bps'], 2)} bps",
        f"  3. 1/N return overlap     {_number(rec['baseline_1N_corr'], 3)}",
    ]
    if "portfolio_1N_convergence" in rec:
        c = rec["portfolio_1N_convergence"]
        lines.append(
            f"     dense-weight 1/N corr  {_number(c['corr_to_1N'], 3)} (MAD {_number(c['mean_abs_dev_from_1N'], 4)})"
        )
    if "graph_ls_sharpe" in rec:
        lines.append(
            f"  4. graph diagnostic       {_number(rec['graph_ls_sharpe'], 3)} vs {_number(rec['random_graph_ls_sharpe_mean'], 3)}"
        )
    lines += [
        "─" * 56,
        f"  VERDICT: {rec['verdict']}",
        f"  SCOPE: {rec['battery_scope']}",
    ]
    return "\n".join(lines)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "demo":
        demo_parser = argparse.ArgumentParser(
            prog="quantem-checker demo",
            description="Eight generated good/bad/empty controls; no data or accounts",
        )
        demo_parser.parse_args(argv[1:])
        report = demo_report()
        print(json.dumps(report, indent=2, allow_nan=False))
        return 0 if report["all_expected_verdicts_observed"] else 1
    ap = argparse.ArgumentParser(
        prog="quantem-checker",
        description=__doc__,
        epilog="Offline demo: quantem-checker demo",
    )
    ap.add_argument(
        "--predictions", required=True, help="wide parquet: ordered time x asset scores"
    )
    ap.add_argument(
        "--returns", required=True, help="wide parquet: matching time x asset returns"
    )
    ap.add_argument(
        "--cost-bps",
        type=float,
        default=10,
        help="per-side basis points; target-turnover sensitivity only",
    )
    ap.add_argument("--q", type=float, default=0.1)
    ap.add_argument(
        "--adjacency",
        default=None,
        help="optional .npy binary graph with exactly matching asset order",
    )
    ap.add_argument("--periods-per-year", type=int, default=252)
    ap.add_argument("--leak-ratio-threshold", type=float, default=0.4)
    ap.add_argument("--leak-abs-floor", type=float, default=0.02)
    ap.add_argument("--name", default="signal")
    ap.add_argument("--format", choices=("table", "json"), default="table")
    ap.add_argument(
        "--json",
        default=None,
        help="also write the strict JSON record to this local path",
    )
    args = ap.parse_args(argv)
    try:
        import pandas as pd
        import pyarrow  # noqa: F401 - explicit optional dependency check
    except ImportError:
        ap.error("Parquet input requires optional pandas/pyarrow: install '.[parquet]'")
    try:
        pred, ret = pd.read_parquet(args.predictions), pd.read_parquet(args.returns)
        if (
            not pred.index.is_unique
            or not pred.columns.is_unique
            or not ret.index.is_unique
            or not ret.columns.is_unique
            or not pred.index.equals(ret.index)
            or not pred.columns.equals(ret.columns)
            or not pred.index.is_monotonic_increasing
            or pred.index.hasnans
        ):
            ap.error(
                "identical unique axes in increasing time order required; no silent join/sort"
            )
        adjacency = (
            np.load(args.adjacency, allow_pickle=False) if args.adjacency else None
        )
        rec = run_check(
            pred.to_numpy(),
            ret.to_numpy(),
            cost_bps=args.cost_bps,
            q=args.q,
            adj=adjacency,
            leak_ratio_threshold=args.leak_ratio_threshold,
            leak_abs_floor=args.leak_abs_floor,
            name=args.name,
            periods_per_year=args.periods_per_year,
        )
    except (OSError, EOFError, TypeError, ValueError, NotImplementedError):
        ap.error("could not read inputs or validate the screening contract")
    payload = json.dumps(rec, indent=2, allow_nan=False)
    print(_format_table(rec) if args.format == "table" else payload)
    if args.json:
        try:
            Path(args.json).write_text(payload + "\n")
        except OSError:
            ap.error("could not write requested local JSON report")
    if rec["screen_status"] == "INSUFFICIENT_EVIDENCE":
        return 2
    return 0 if rec["survives_battery"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
