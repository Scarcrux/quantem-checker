"""Audit supplied long-only unit/cash ledgers without market data or simulation."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np


def audit_ledger(rows, *, round_trip_bps, initial_nav=1.0, atol=1e-10):
    """Reconcile an initial-cash, zero-interest, terminal-open long-only ledger.

    Uses the holdings_v1 row fields. This checks arithmetic and continuity,
    not authentic marks, executable fills, liquidity, broker funding or alpha.
    Only row positions/reasons are returned, never supplied values.
    """
    if (
        not np.isfinite(round_trip_bps)
        or not 0 <= round_trip_bps < 20000
        or not np.isfinite(initial_nav)
        or initial_nav <= 0
        or not np.isfinite(atol)
        or atol < 0
    ):
        raise ValueError(
            "finite positive initial NAV, tolerance and valid RT fee required"
        )
    rows = list(rows)
    result = {
        "schema": "quantem-checker/ledger-1",
        "verdict": "NOT TESTED",
        "n_rows": len(rows),
        "checked_rows": 0,
        "errors": [],
        "scope": "supplied long-only cash/unit arithmetic; no mark authenticity, fill or profitability certification",
    }
    previous = None
    arrays = (
        "values_before",
        "units_before",
        "units_after",
        "prices_before",
        "return_row",
        "traded_notional",
    )
    scalars = (
        "cash_before",
        "cash_after",
        "nav_before",
        "nav_post_fee",
        "nav_end",
        "fee",
    )
    for i, row in enumerate(rows):

        def reject(reason, row_index=i):
            result["errors"].append({"row": row_index, "reason": reason})

        try:
            if not isinstance(row, Mapping):
                raise TypeError("mapping required")
            a = {k: np.asarray(row[k], dtype=float) for k in arrays}
            v = {k: float(row[k]) for k in scalars}
            shape = a["prices_before"].shape
            if (
                len(shape) != 1
                or shape[0] == 0
                or any(x.shape != shape or not np.isfinite(x).all() for x in a.values())
                or not all(np.isfinite(x) for x in v.values())
            ):
                raise ValueError("finite aligned marks/units/amounts required")
            if (
                any(
                    (a[k] < 0).any()
                    for k in (
                        "values_before",
                        "units_before",
                        "units_after",
                        "prices_before",
                    )
                )
                or (a["return_row"] < -1).any()
                or any(v[k] < 0 for k in scalars)
                or v["nav_before"] <= 0
            ):
                raise ValueError(
                    "invalid long-only amounts/returns or exhausted wealth"
                )
            scale = max(initial_nav, v["nav_before"])

            def equal(x, y, row_scale=scale):
                return np.shape(x) == np.shape(y) and np.allclose(
                    x, y, atol=atol * row_scale, rtol=0
                )

            p, before, after = a["prices_before"], a["units_before"], a["units_after"]
            trades = a["traded_notional"]
            expected_fee = float(np.abs(trades).sum() * round_trip_bps / 20000)
            identities = {
                "values_units_marks": equal(a["values_before"], before * p),
                "trade_notional": equal(trades, (after - before) * p),
                "fee_units": equal(v["fee"], expected_fee),
                "pretrade_nav": equal(
                    v["nav_before"], float(a["values_before"].sum() + v["cash_before"])
                ),
                "cash_conservation": equal(
                    v["cash_after"], float(v["cash_before"] - trades.sum() - v["fee"])
                ),
                "post_fee_nav": equal(v["nav_post_fee"], v["nav_before"] - v["fee"]),
                "post_trade_inventory": equal(
                    v["nav_post_fee"], float((after * p).sum() + v["cash_after"])
                ),
                "ending_nav": equal(
                    v["nav_end"],
                    float((after * p * (1 + a["return_row"])).sum() + v["cash_after"]),
                ),
                "no_zero_price_purchase": not ((p == 0) & (after > before)).any(),
            }
            if previous is None:
                identities["initial_cash"] = equal(
                    v["cash_before"], float(initial_nav)
                ) and equal(before, np.zeros_like(before))
            else:
                identities.update(
                    continuity_units=equal(before, previous["units"]),
                    continuity_cash=equal(v["cash_before"], previous["cash"]),
                    continuity_marks=equal(p, previous["marks"]),
                    continuity_nav=equal(v["nav_before"], previous["nav"]),
                )
            for reason, passed in identities.items():
                if not passed:
                    reject(reason)
            previous = {
                "units": after.copy(),
                "cash": v["cash_after"],
                "marks": p * (1 + a["return_row"]),
                "nav": v["nav_end"],
            }
            result["checked_rows"] += 1
        except (KeyError, TypeError, ValueError, OverflowError):
            reject("missing_or_invalid_ledger_contract")
            break
    if result["errors"]:
        result["verdict"] = "FAIL"
    elif rows:
        result["verdict"] = "PASS"
    return result
