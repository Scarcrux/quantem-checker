"""Small executable good/bad controls; generated data only, no market study."""

from __future__ import annotations

import copy
import json

import numpy as np

from .availability import audit_event_clock
from .ledger import audit_ledger
from .pipeline import audit_prefix_consistency


def example_ledger(round_trip_bps=20.0):
    """Initial purchase, drift, no second trade, then exact total loss."""
    units = 1 / (1 + round_trip_bps / 20000)
    first = {
        "values_before": [0.0],
        "units_before": [0.0],
        "units_after": [units],
        "prices_before": [1.0],
        "return_row": [0.1],
        "traded_notional": [units],
        "cash_before": 1.0,
        "cash_after": 0.0,
        "nav_before": 1.0,
        "nav_post_fee": units,
        "nav_end": units * 1.1,
        "fee": units * round_trip_bps / 20000,
    }
    second = {
        "values_before": [units * 1.1],
        "units_before": [units],
        "units_after": [units],
        "prices_before": [1.1],
        "return_row": [-1.0],
        "traded_notional": [0.0],
        "cash_before": 0.0,
        "cash_after": 0.0,
        "nav_before": units * 1.1,
        "nav_post_fee": units * 1.1,
        "nav_end": 0.0,
        "fee": 0.0,
    }
    return [first, second]


def demo_report():
    values = np.arange(1.0, 49.0).reshape(16, 3)
    inputs = {"features": values}
    pipelines = {
        "causal_cumulative": lambda d: {"scores": np.cumsum(d["features"], axis=0)},
        "future_oracle": lambda d: {"scores": np.roll(d["features"], -1, axis=0)},
        "full_series_centering": lambda d: {
            "scores": d["features"] - np.mean(d["features"], axis=0)
        },
    }
    cases = {
        name: audit_prefix_consistency(fn, inputs, [4, 8, 12])
        for name, fn in pipelines.items()
    }
    receipt = {
        "event_id": "synthetic-event",
        "published_at": "2026-01-05T12:00:00+00:00",
        "available_at": "2026-01-05T12:01:00+00:00",
        "cutoff": "2026-01-05T20:55:00+00:00",
        "entry": "2026-01-05T21:00:00+00:00",
        "exit": "2026-01-06T21:00:00+00:00",
    }
    cases["available_clock"] = audit_event_clock([receipt])
    cases["exact_cutoff_clock"] = audit_event_clock(
        [{**receipt, "available_at": receipt["cutoff"]}]
    )
    cases["empty_clock"] = audit_event_clock([])
    ledger = example_ledger()
    cases["funded_ledger"] = audit_ledger(ledger, round_trip_bps=20)
    broken = copy.deepcopy(ledger)
    broken[0]["fee"] += 0.01
    cases["corrupt_fee"] = audit_ledger(broken, round_trip_bps=20)
    expected = {
        "causal_cumulative": "PASS",
        "future_oracle": "FAIL",
        "full_series_centering": "FAIL",
        "available_clock": "PASS",
        "exact_cutoff_clock": "FAIL",
        "empty_clock": "NOT TESTED",
        "funded_ledger": "PASS",
        "corrupt_fee": "FAIL",
    }
    return {
        "schema": "quantem-checker/demo-1",
        "synthetic_only": True,
        "all_expected_verdicts_observed": all(
            cases[k]["verdict"] == v for k, v in expected.items()
        ),
        "expected": expected,
        "cases": cases,
        "limits": "finite software controls; not leakage error-rate calibration, authentic receipts, market alpha or paper reproduction",
    }


def main():
    report = demo_report()
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report["all_expected_verdicts_observed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
