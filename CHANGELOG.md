# Changes

## 0.2.0a1 — private integration, not a public release

- Retain `quantem_checker` library imports, helper exports and existing CLI flags.
- Add `audit_prefix_consistency`, `audit_event_clock`, `audit_ledger` and
  `quantem-checker demo`; all examples are generated locally without vendor data.
- Explicitly version the statistical screen as schema `quantem-checker/3`.
  Add nullable/insufficient-evidence handling. CLI invalid or insufficient input
  returns 2; a 0 result means only the requested screens were not flagged.
- Reject mismatched/duplicate/unordered panel axes instead of intersecting them.
  Asset order must also match the optional graph; no implicit graph reshaping.
- Average tied ranks rather than encoding order inside a tie. Select assets
  before observing future marks; missing selected marks cannot select substitutes.
  Label target-turnover costs as a proxy, include initial entry, keep terminal
  positions open, and reject missing dense marks. No funded-performance claim
  is inferred from the statistical cost proxy.
- Distinguish predictive correlation, leakage symptoms and observed availability.
  Correct the old forward-oracle description and retire the old specificity
  grid's causal error-rate claims. Its original code remains at `bc4751c`.
- Base install requires NumPy >=1.24 and Python >=3.10. Parquet input now uses
  the optional `.[parquet]` group (pandas/PyArrow); existing installations with
  those dependencies retain them. Local demo/help/core audits do not need pandas.
- Keep the existing LICENSE unchanged and use organization maintenance metadata.
  Public privacy/notice review remains a separate gate. No dataset, empirical
  evidence, paper verifier, history rewrite or repository visibility change.

Existing numerical outputs are not promised identical: corrected ranking,
selection, initial-cost treatment and adequacy rules change relevant results.
Use the original commit for exact old behavior; do not relabel a new result as
an independently reproduced historical one. Prefix tests and these software
controls are not universal causality, authentic-feed or investment certification.
