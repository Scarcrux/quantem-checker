"""Actual CLI compatibility and strict axes/nullable reports, generated inputs only."""

import json

import numpy as np
import pytest

from quantem_checker import core, run_check
from quantem_checker.__main__ import main


def panels(tmp_path):
    pd = pytest.importorskip("pandas")
    pytest.importorskip("pyarrow")
    pred = pd.DataFrame(np.arange(32.0).reshape(8, 4))
    ret = pd.DataFrame(np.arange(32.0).reshape(8, 4) / 1000)
    p, r = tmp_path / "pred.parquet", tmp_path / "ret.parquet"
    pred.to_parquet(p)
    ret.to_parquet(r)
    return pred, ret, p, r


def test_core_import_path_retains_function_identity():
    assert core.run_check is run_check
    from quantem_checker import (
        audit_event_clock,
        audit_ledger,
        audit_prefix_consistency,
    )

    assert callable(audit_prefix_consistency) and callable(audit_ledger)
    assert audit_event_clock([])["verdict"] == "NOT TESTED"


def test_legacy_flags_and_strict_json_output(tmp_path, capsys):
    _, _, p, r = panels(tmp_path)
    output = tmp_path / "report.json"
    graph = tmp_path / "graph.npy"
    np.save(graph, np.zeros((4, 4)))
    status = main(
        [
            "--predictions",
            str(p),
            "--returns",
            str(r),
            "--cost-bps",
            "7.5",
            "--q",
            ".25",
            "--periods-per-year",
            "12",
            "--leak-ratio-threshold",
            ".3",
            "--leak-abs-floor",
            ".01",
            "--name",
            "compatibility",
            "--adjacency",
            str(graph),
            "--format",
            "json",
            "--json",
            str(output),
        ]
    )
    assert status == 2
    record = json.loads(capsys.readouterr().out)
    assert record == json.loads(output.read_text())
    assert (
        record["name"] == "compatibility"
        and record["report_schema"] == "quantem-checker/3"
    )
    assert record["leak_flagged"] is None and record["graph_beats_random"] is None
    assert "NaN" not in output.read_text()


def test_table_can_format_unavailable_metrics(tmp_path, capsys):
    _, _, p, r = panels(tmp_path)
    assert main(["--predictions", str(p), "--returns", str(r)]) == 2
    text = capsys.readouterr().out
    assert "NOT TESTED" in text and "INSUFFICIENT EVIDENCE" in text
    assert "SCOPE:" in text


@pytest.mark.parametrize(
    "mutation", ["rows", "columns", "order", "duplicates", "reversed_time"]
)
def test_misaligned_axes_fail_instead_of_intersecting(tmp_path, mutation):
    pred, ret, p, r = panels(tmp_path)
    if mutation == "rows":
        ret = ret.iloc[1:]
    elif mutation == "columns":
        ret = ret.iloc[:, :-1]
    elif mutation == "order":
        ret = ret.iloc[:, ::-1]
    elif mutation == "duplicates":
        ret.index = [0] * len(ret)
    else:
        pred, ret = pred.iloc[::-1], ret.iloc[::-1]
    pred.to_parquet(p)
    ret.to_parquet(r)
    with pytest.raises(SystemExit) as error:
        main(["--predictions", str(p), "--returns", str(r)])
    assert error.value.code == 2


def test_invalid_cost_and_graph_shape_reject(tmp_path):
    _, _, p, r = panels(tmp_path)
    base = ["--predictions", str(p), "--returns", str(r)]
    with pytest.raises(SystemExit) as error:
        main(base + ["--cost-bps", "-1"])
    assert error.value.code == 2
    graph = tmp_path / "bad.npy"
    np.save(graph, np.eye(2))
    with pytest.raises(SystemExit) as error:
        main(base + ["--adjacency", str(graph)])
    assert error.value.code == 2
