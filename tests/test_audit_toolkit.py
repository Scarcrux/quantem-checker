"""Meaningful good/bad pipeline and accounting controls, no private inputs."""

import json

import numpy as np
import pytest

from quantem_checker.audit_demo import demo_report, example_ledger
from quantem_checker.availability import audit_event_clock
from quantem_checker.ledger import audit_ledger
from quantem_checker.pipeline import audit_prefix_consistency


def test_actual_demo_discriminates_all_cases_without_network(monkeypatch):
    import socket

    monkeypatch.setattr(
        socket.socket, "connect", lambda *_: pytest.fail("network forbidden")
    )
    report = demo_report()
    assert report["all_expected_verdicts_observed"]
    assert {x["verdict"] for x in report["cases"].values()} == {
        "PASS",
        "FAIL",
        "NOT TESTED",
    }
    json.dumps(report, allow_nan=False)


def test_pipeline_exercises_truncation_values_and_missingness_without_mutating_inputs():
    values = np.arange(32.0).reshape(16, 2)
    original = values.copy()
    calls = []

    def runner(data):
        calls.append(data["x"].copy())
        return {"features": np.cumsum(np.nan_to_num(data["x"]), axis=0)}

    report = audit_prefix_consistency(runner, {"x": values}, [4, 9])
    assert report["verdict"] == "PASS"
    assert report["runner_calls"] == 8 and len(calls) == 8
    assert {r["probe"] for r in report["checks"]} == {
        "truncate",
        "future_values",
        "future_missingness",
    }
    np.testing.assert_equal(values, original)
    # Real delivered probes retain the prefix and change the suffix.
    np.testing.assert_equal(calls[3][:4], original[:4])
    assert not np.array_equal(calls[3][4:], original[4:])
    assert np.isnan(calls[4][4:]).all()


def test_forward_oracle_is_detected_even_though_rank_screen_can_accept_it():
    from quantem_checker.screening import run_check

    rng = np.random.default_rng(7)
    ret = rng.normal(size=(80, 30))

    def oracle(d):
        return {"scores": np.roll(d["returns"], -1, axis=0) + 0.05 * d["returns"]}

    scores = oracle({"returns": ret})["scores"]
    assert run_check(scores, ret)["leak_flagged"] is False
    assert (
        audit_prefix_consistency(oracle, {"returns": ret}, [20, 40])["verdict"]
        == "FAIL"
    )


def test_global_preprocessing_and_hidden_state_are_not_clean_passes():
    x = np.arange(20.0).reshape(10, 2)
    result = audit_prefix_consistency(
        lambda d: {"z": d["x"] - d["x"].mean()}, {"x": x}, [3]
    )
    assert result["verdict"] == "FAIL"
    counter = iter(range(100))
    result = audit_prefix_consistency(
        lambda d: {"z": d["x"] + next(counter)}, {"x": x}, [3]
    )
    assert result["verdict"] == "NOT TESTED"
    assert result["errors"] == [{"reason": "runner_not_repeatable"}]


@pytest.mark.parametrize(
    "runner",
    [
        lambda d: {},
        lambda d: {"z": [1.0]},
        lambda d: {"z": np.full_like(d["x"], np.nan)},
    ],
)
def test_empty_wrong_shape_or_unobserved_output_cannot_pass(runner):
    report = audit_prefix_consistency(runner, {"x": np.ones((8, 2))}, [3])
    assert report["verdict"] == "NOT TESTED"


def test_callback_exception_does_not_disclose_its_message():
    def runner(_):
        raise RuntimeError("private payload that must never enter a report")

    result = audit_prefix_consistency(runner, {"x": np.ones((8, 2))}, [3])
    assert result["verdict"] == "NOT TESTED"
    assert "private payload" not in json.dumps(result)


@pytest.mark.parametrize("cuts", [[], [0], [8], [True], [2, 2]])
def test_invalid_cutoffs_rejected(cuts):
    with pytest.raises(ValueError):
        audit_prefix_consistency(lambda d: d, {"x": np.ones((8, 2))}, cuts)


def test_initial_cost_drift_and_exact_terminal_loss_reconcile():
    ledger = example_ledger()
    assert audit_ledger(ledger, round_trip_bps=20)["verdict"] == "PASS"
    assert ledger[1]["fee"] == 0 and ledger[1]["nav_end"] == 0
    assert audit_ledger([], round_trip_bps=20)["verdict"] == "NOT TESTED"


@pytest.mark.parametrize(
    "row,key,value",
    [
        (0, "fee", 0.1),
        (0, "cash_after", 0.2),
        (0, "units_after", [2.0]),
        (1, "units_before", [0.5]),
        (1, "return_row", [np.nan]),
        (1, "return_row", [-1.1]),
        (1, "prices_before", [1.2]),
        (1, "cash_before", 0.01),
        (1, "nav_end", 0.2),
        (1, "traded_notional", [0.1]),
    ],
)
def test_corrupted_ledger_does_not_pass(row, key, value):
    ledger = example_ledger()
    ledger[row][key] = value
    report = audit_ledger(ledger, round_trip_bps=20)
    assert report["verdict"] == "FAIL" and report["errors"]
    assert "return_row" not in json.dumps(report)


def test_ledger_independently_accepts_cash_only_and_validates_fee_contract():
    row = {
        "values_before": [0.0],
        "units_before": [0.0],
        "units_after": [0.0],
        "prices_before": [10.0],
        "return_row": [0.7],
        "traded_notional": [0.0],
        "cash_before": 1.0,
        "cash_after": 1.0,
        "nav_before": 1.0,
        "nav_post_fee": 1.0,
        "nav_end": 1.0,
        "fee": 0.0,
    }
    assert audit_ledger([row], round_trip_bps=0)["verdict"] == "PASS"
    assert audit_ledger(example_ledger(), round_trip_bps=40)["verdict"] == "FAIL"
    with pytest.raises(ValueError):
        audit_ledger([row], round_trip_bps=-1)


def test_clock_contract_positive_negative_empty_and_naive():
    row = {
        "published_at": "2026-01-01T09:00:00Z",
        "available_at": "2026-01-01T09:01:00Z",
        "cutoff": "2026-01-01T09:05:00Z",
        "entry": "2026-01-01T09:10:00Z",
        "exit": "2026-01-01T10:00:00Z",
    }
    assert audit_event_clock([row])["verdict"] == "PASS"
    assert (
        audit_event_clock([{**row, "available_at": row["cutoff"]}])["verdict"] == "FAIL"
    )
    assert (
        audit_event_clock([{**row, "published_at": "2026-01-01T09:00:00"}])["verdict"]
        == "FAIL"
    )
    assert audit_event_clock([])["verdict"] == "NOT TESTED"


def test_actual_cli_demo_reports_observed_controls(capsys):
    from quantem_checker.__main__ import main

    assert main(["demo"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["all_expected_verdicts_observed"]
    assert len(report["cases"]) == 8
