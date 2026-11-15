"""Versioned screening regressions: ties, future marks, fee units and scope."""

import numpy as np
import pytest

from quantem_checker import screening as screen


def test_average_ranks_and_ic_do_not_encode_order_inside_ties():
    np.testing.assert_equal(
        screen._rankdata(np.array([1.0, 1.0, 2.0])), [0.5, 0.5, 2.0]
    )
    pred = np.repeat(np.arange(10.0), 2)
    ret = np.arange(20.0)
    order = np.arange(20).reshape(-1, 2)[:, ::-1].ravel()
    assert screen._row_ic(pred, ret) == pytest.approx(
        screen._row_ic(pred[order], ret[order])
    )


def test_missing_preselected_outcome_cannot_replace_the_asset():
    p = np.tile(np.arange(4.0), (3, 1))
    r = np.array([[0.0, 0.0, 0.0, 0.0], [0.1, 0.2, 0.3, np.nan], [0.1, 0.2, 0.3, 0.4]])
    spreads, longs = screen.decile_ls_returns(p, r, q=0.25)
    assert np.isnan(spreads[0]) and np.isnan(longs[0])
    assert spreads[1] == pytest.approx(0.3)
    assert np.isnan(screen.net_of_cost(p, r, q=0.25)["net_sharpe"])


def test_target_proxy_charges_initial_entry_and_both_legs_once():
    p = np.tile(np.arange(10.0), (3, 1))
    r = np.array([np.arange(10.0) * scale for scale in (0.001, 0.002, 0.003)])
    rec = screen.net_of_cost(p, r, cost_bps=10, q=0.1)
    # Gross exposure 2: initial L1 entry 2, no second trade; average L1 = 1.
    assert rec["turnover_per_period"] == 1
    assert rec["cost_drag_per_period_bps"] == 10
    assert (
        "proxy" in rec["cost_scope"] and "terminal inventory open" in rec["cost_scope"]
    )


def test_dense_cost_proxy_rejects_missing_marks_instead_of_zero_filling():
    w = np.full((8, 4), 0.25)
    r = np.zeros_like(w)
    r[3, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        screen.net_of_cost_per_name(w, r, np.full(4, 0.001))


def test_new_schema_does_not_relabel_frozen_legacy_source():
    rng = np.random.default_rng(11)
    p, r = rng.normal(size=(50, 20)), rng.normal(size=(50, 20))
    rec = screen.run_check(p, r)
    assert rec["report_schema"] == "quantem-checker/3"
    assert "not a calibrated" in rec["screen_scope"]
