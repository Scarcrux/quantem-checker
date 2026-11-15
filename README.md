# Quantem Checker

Local tools for checking temporal pipeline behavior, supplied availability
clocks and portfolio accounting. Version **0.2.0a1** is a prerelease. All examples
generate their own data; no research datasets, accounts or GPU are required.

- Probe a pipeline for dependence on future input values or missingness.
- Check supplied receipt timestamps against decision and execution clocks.
- Reconcile long-only portfolio units, cash, marks and declared fees.

Run the tools inside your own environment with data you are authorized to use.
No research datasets, private paper evidence or paper-specific verifier are
included. Passing a check is evidence about the supplied case, not certification
that a strategy is causal, profitable or ready to trade.

## Run a meaningful demonstration

```sh
git clone https://github.com/Scarcrux/quantem-checker.git
cd quantem-checker
python -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/quantem-checker demo
```

For development checks:

```sh
.venv/bin/python -m pip install '.[dev,parquet]'
.venv/bin/python -m pytest -q tests
```

The demonstration succeeds only when the correct causal pipeline and funded
ledger pass, future-oracle/full-series-normalization pipelines and a corrupt
fee fail, an available clock passes, an exact-cutoff clock fails, and empty
clock delivery is NOT TESTED. A negative control returning FAIL is the expected
successful diagnostic, not a malfunction. No market result is produced.

## Check your own pipeline locally

```python
import numpy as np
from quantem_checker import audit_prefix_consistency

def pipeline(inputs):
    # Put relevant preprocessing, fitting and decision logic inside this callback.
    return {"scores": np.cumsum(inputs["features"], axis=0)}

x = np.arange(48.0).reshape(16, 3)
report = audit_prefix_consistency(pipeline, {"features": x}, cutoffs=[4, 8, 12])
assert report["verdict"] == "PASS"
```

The checker actually reruns the callback on truncated inputs and on future-value
and future-missingness mutations. Earlier outputs must agree within the declared
tolerances. Fixed seeds/state are the caller's responsibility: non-repeatable,
empty or unsupported output cannot be called a pass. Inputs are copied; reports
contain stages/counts/reasons, not raw values. Choose non-identifying stage names.
Callbacks execute as local trusted code; they are not sandboxed, and may make
external calls if you write them to do so. The toolkit has no telemetry/upload API.

This is a finite behavioral test, not universal proof of causality. It cannot
see hidden inputs outside the callback, certify truthful vendor timestamps,
detect every historical revision, or show that a strategy has economic value.
Time rows must mean what you declare; positional prefix tests alone do not
establish public or customer receipt-time availability.

## Audit supplied clocks and accounting

`audit_event_clock(receipts)` checks timezone-aware publication/availability/
cutoff/entry/exit ordering; exact-cutoff receipt is excluded. Empty logs are
NOT TESTED. Authenticity/completeness of the supplied clocks remain unverified.

`audit_ledger(rows, round_trip_bps=15)` checks long-only units, cash, marked NAV,
consecutive-row continuity and fees on actual supplied traded notional. Its
contract starts with unit cash (configurable), zero cash interest and terminal
inventory open. An exact total loss is allowed; missing marks and unexplained
cash injections fail. `quantem_checker.audit_demo.example_ledger()` supplies a
complete generated example. This is a ledger auditor, not a simulator, broker
execution model, liquidity/borrow model or source-of-price certification.

## Optional statistical screens

```sh
.venv/bin/python -m pip install '.[parquet]'
.venv/bin/quantem-checker --predictions predictions.parquet --returns returns.parquet
```

Panels require identical unique ordered time/asset axes. Predictions on row t
are scored against returns on row t+1; this convention does not itself prove
availability. Costs here are **per side**, unlike the ledger's explicit RT units.
The version-3 screen fixes average ranks for ties and selects assets before
examining outcome availability. Missing selected marks cannot select substitutes.
Tie-breaking at portfolio cutoffs follows input column order, which must be
declared for tied signals.

Lagged rank correlation, equal-weight overlap, target-turnover costs and optional
random-graph comparisons are heuristic diagnostics. Their thresholds are not a
calibrated clean/leaky classifier, power/equivalence test or investment approval.
Target-weight changes omit drift, borrow and fill/funding realism. Baseline
correlation does not establish identical portfolios or eliminate factor alpha.
Graph screening is not a powered graph-advantage study. CLI exits: 0 means the
requested screens were not flagged, 1 means flagged, 2 means invalid/insufficient.

## Scope, attribution and reproducibility

The existing first-party MIT license and required notice are retained. Package
maintenance metadata uses organization attribution. Dependencies are installed
separately and retain their notices; see [NOTICES.md](NOTICES.md). No vendor
records, PDFs, private execution history, production
dashboard or historical numerical claims are bundled. A user with authorized
data access can run the tools inside their environment without sharing data.

The original checker source remains in Git at `bc4751c`. Screening-v3 output must
not replace historical results without an explicitly versioned reanalysis.
[CHANGELOG.md](CHANGELOG.md) records compatibility changes;
[docs/INTEGRATION-SOURCES.json](docs/INTEGRATION-SOURCES.json) binds imported source
and namespace transformations. The referenced research revision is a provenance
identifier, not a promise of access to private research code or evidence.
The retained review records describe the integration and preparation process.
No DOI, journal acceptance or independent external review is claimed.
Do not describe synthetic controls as validation of market results.

## Compatibility and examples

Existing `from quantem_checker import run_check` and
`from quantem_checker.core import run_check` imports remain available. Existing
CLI options remain, including `--q`, `--adjacency`, `--periods-per-year`,
`--leak-ratio-threshold`, `--leak-abs-floor`, `--name`, `--format table|json`, and
`--json report.json`. Table output handles nullable/untested diagnostics.

Input validation is intentionally stricter: old silent axis intersections now
fail, flags may be `None`, and invalid/insufficient evidence exits 2. Per-side
costs include initial entry in the target-turnover proxy. Install `.[parquet]`
for file input; base library/help/demo need only NumPy. Python >=3.10 is required.

`python examples/synthetic_demo.py` preserves the statistical illustration while
labelling its forward-generated oracle honestly. The former
`examples/specificity_grid.py` no longer claims calibrated leakage error rates;
it runs the bounded direct good/bad controls. Its historical implementation
remains in Git. No new grid/threshold benchmark was executed for this integration.

A full minimum-version/platform matrix remains unverified. No external adoption or calibrated
detection error rates are claimed. Caller-supplied stage/event identifiers may
appear in local reports; those reports are not automatically anonymized.
