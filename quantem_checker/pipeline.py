"""Local black-box temporal probes; no data acquisition or callback sandbox."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np


def audit_prefix_consistency(runner, inputs, cutoffs, *, atol=0.0, rtol=0.0):
    """Compare earlier outputs after truncating/perturbing later input rows.

    runner receives a fresh mapping of numeric, row-aligned arrays and returns
    a nonempty mapping of numeric outputs with the same row count. It must be
    deterministic and encompass all relevant preprocessing/fitting/decision
    stages. Cutoffs are exclusive: rows [0:cutoff] must not depend on rows
    [cutoff:]. They are positional tests, not proof of truthful timestamps or
    external state. Exact equality is default; NaN matches NaN. No values are
    returned in the report. The callback is trusted code, NOT sandboxed.
    """
    if not callable(runner) or not isinstance(inputs, Mapping) or not inputs:
        raise ValueError("callable runner and nonempty named input arrays required")
    if any(not isinstance(k, str) or not k for k in inputs):
        raise ValueError("nonempty string input names required")
    arrays = {k: np.array(v, dtype=float, copy=True) for k, v in inputs.items()}
    if any(a.ndim == 0 or np.isinf(a).any() for a in arrays.values()):
        raise ValueError("numeric row-aligned arrays without infinity required")
    lengths = {len(a) for a in arrays.values()}
    if len(lengths) != 1 or next(iter(lengths)) < 2:
        raise ValueError("inputs require identical row counts of at least two")
    n = next(iter(lengths))
    cuts = list(cutoffs)
    if (
        not cuts
        or len(set(cuts)) != len(cuts)
        or any(
            isinstance(c, (bool, np.bool_))
            or not isinstance(c, (int, np.integer))
            or not 1 <= c < n
            for c in cuts
        )
    ):
        raise ValueError("unique integer cutoffs strictly inside the input required")
    if any(not np.isfinite(x) or x < 0 for x in (atol, rtol)):
        raise ValueError("finite nonnegative tolerances required")
    report = {
        "schema": "quantem-checker/prefix-1",
        "verdict": "NOT TESTED",
        "n_rows": n,
        "runner_calls": 0,
        "checks": [],
        "errors": [],
        "tolerances": {"atol": float(atol), "rtol": float(rtol)},
        "scope": "finite deterministic callback probes; not universal causality, authentic data availability or model skill",
    }

    def execute(data):
        report["runner_calls"] += 1
        output = runner({k: v.copy() for k, v in data.items()})
        if not isinstance(output, Mapping) or not output:
            raise ValueError("nonempty named output arrays required")
        result = {}
        for key, value in output.items():
            if not isinstance(key, str) or not key:
                raise ValueError("nonempty string output names required")
            arr = np.array(value, dtype=float, copy=True)
            if (
                arr.ndim == 0
                or len(arr) != len(next(iter(data.values())))
                or np.isinf(arr).any()
            ):
                raise ValueError("row-aligned output without infinity required")
            result[key] = arr
        return result

    def compare(left, right, cutoff):
        if set(left) != set(right):
            return ["output_keys"]
        return [
            k
            for k in left
            if left[k][:cutoff].shape != right[k][:cutoff].shape
            or not np.allclose(
                left[k][:cutoff],
                right[k][:cutoff],
                atol=atol,
                rtol=rtol,
                equal_nan=True,
            )
        ]

    try:
        baseline, repeat = execute(arrays), execute(arrays)
        if compare(baseline, repeat, n):
            report["errors"].append({"reason": "runner_not_repeatable"})
            return report
        if not any(np.isfinite(a).any() for a in baseline.values()):
            report["errors"].append({"reason": "no_finite_output_observed"})
            return report
        for cutoff in cuts:
            for mode in ("truncate", "future_values", "future_missingness"):
                data = {
                    k: a[:cutoff].copy() if mode == "truncate" else a.copy()
                    for k, a in arrays.items()
                }
                if mode != "truncate":
                    for arr in data.values():
                        tail = arr[cutoff:]
                        if mode == "future_values":
                            tail[:] = np.where(
                                np.isnan(tail), 1.0, np.where(tail == 0, 1.0, -tail)
                            )
                        else:
                            tail[:] = 0.0 if np.isnan(tail).all() else np.nan
                output = execute(data)
                changed = compare(baseline, output, cutoff)
                # A zero-information prefix cannot validate a supplied stage.
                finite = all(np.isfinite(a[:cutoff]).any() for a in baseline.values())
                report["checks"].append(
                    {
                        "cutoff": int(cutoff),
                        "probe": mode,
                        "verdict": "FAIL"
                        if changed
                        else "PASS"
                        if finite
                        else "NOT TESTED",
                        "changed_stages": changed,
                        "finite_prefix_values": {
                            k: int(np.isfinite(a[:cutoff]).sum())
                            for k, a in baseline.items()
                        },
                    }
                )
    except Exception as error:  # noqa: BLE001 - redact arbitrary user-callback errors into NOT TESTED
        # Callback messages may contain paths, data or credentials: never export them.
        report["errors"].append(
            {
                "reason": "callback_or_output_contract_error",
                "exception_type": type(error).__name__,
            }
        )
        if any(c["verdict"] == "FAIL" for c in report["checks"]):
            report["verdict"] = "FAIL"
        return report
    verdicts = {c["verdict"] for c in report["checks"]}
    report["verdict"] = (
        "FAIL"
        if "FAIL" in verdicts
        else "NOT TESTED"
        if "NOT TESTED" in verdicts
        else "PASS"
    )
    return report
