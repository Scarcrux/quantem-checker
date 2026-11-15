# Private checker integration review

The owner selected the existing private checker repository as the project home.
This integrates the reviewed data-free toolkit rather than creating a different
project. Original commit `bc4751c` and its LICENSE notice remain intact. No Git
history rewrite, dataset transfer, paper-evidence export or public release is
part of this work.

## Changes and compatibility

- Keep the `quantem_checker` package, `quantem-checker` command, public helper
  exports and `quantem_checker.core` import path. Package version is `0.2.0a1`.
- Add deterministic prefix/future-value/missingness probes, supplied-clock audit,
  long-only unit/cash ledger audit and the eight-case offline `demo` command.
- Add adequacy/nullable verdicts and screening schema 3. Correct tied ranking,
  outcome-dependent asset replacement and declared initial-entry cost proxies.
- Preserve existing CLI flags and JSON-file output; reject mismatched/duplicate/
  reversed axes instead of silently intersecting them. Unknown results print
  safely in table form and return exit 2. See [CHANGELOG](../CHANGELOG.md).
- Retire the old specificity grid's rate claims. Its labels could call a
  future-return oracle honest because it predicts well. The current example
  path runs bounded direct controls; the historical script remains in Git. No
  new grid, seed sweep, threshold calibration or empirical study was launched.
- Describe the statistical examples as generated diagnostics, not availability
  or investment certification. A noisy future-dependent predictor can escape
  the statistical timing flag while failing the actual pipeline perturbation
  audit; this distinction is covered by the tests.

Imported modules/tests originate at the reviewed research revision
`8c58311ced006a079b6cfa03fd6329447aa95004`.
[INTEGRATION-SOURCES.json](INTEGRATION-SOURCES.json) records their exact hashes,
namespace/schema transformations and the small lint adaptations. No runtime
dependency on the research checkout is introduced.

## Local verification

| Check | Observed result |
| --- | --- |
| Original standalone baseline | 12 tests pass in 0.74s before source replacement |
| Integrated research environment | 53 tests pass in 1.72s |
| Fresh core/dev/Parquet environment | 53 tests pass in 1.73s, zero skips |
| CLI generated diagnostic cases | Same-period fixture exits 1; forward oracle exits 0; stdout and `--json` records agree; neither is a market claim |
| Actual offline demo | All eight expected PASS/FAIL/NOT TESTED verdicts observed |
| Existing example paths after install | Statistical example and bounded replacement example pass |
| Fresh wheel outside source | Imports, version, compatibility alias, help/demo and direct good/bad APIs pass with NumPy only, no pandas or research platform |
| Optional input unavailable | Core-only CLI returns 2 with actionable optional-dependency message |
| Wheel/sdist and Twine | Pass; all nine package modules match reviewed source bytes; original LICENSE retained |
| Formatting/lint | Ruff passes; one narrow callback exception suppression is explained in code to avoid disclosing arbitrary error payloads |

The first direct example invocation in the pre-existing research environment
failed because the newly cloned standalone package was not installed there.
The documented editable install in a fresh environment resolved it without
adding path hacks. The initial package build reported deprecated table-form
license metadata; switching to an SPDX expression and explicit LICENSE file
with a compatible backend fixed the warning, and both artifacts were rebuilt.
See [setuptools configuration](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html)
for the supported metadata format. No dependency source is bundled or relicensed.

[PRIVATE-INTEGRATION-REVIEW.json](PRIVATE-INTEGRATION-REVIEW.json) binds tested
source, build hashes and actual CLI/wheel checks. These checks are software QA,
not calibrated leakage error rates, true vendor/customer receipt validation,
authentic execution marks, profitable trading or historical paper reproduction.
The baseline and integrated tests overlap and are not summed as independent tests.

## Private delivery and remaining public gates

Source commit `f3af444c9d211789ca3b7912f7d3552879a6c4f6` was committed, landed
and pushed normally to the existing private `Scarcrux/quantem-checker` main
branch. Remote HEAD matched exactly, and GitHub reported PRIVATE immediately
before and after the push. The final pre-commit rerun passed all 53 tests in
2.73s; Ruff, whitespace and fully redacted secret scans also passed. This record
and the roadmap are a subsequent documentation-only update. No force push or
visibility change occurred; no public release is approved.

The existing required personal copyright notice and old author attribution in
history remain unchanged. New maintenance metadata and commits use organization/
noreply identity. This is deliberate preservation, not a public privacy clearance.
An owner decision on notice/privacy scope and exact visible history is still
required before any public release. No public repository, PyPI upload, GitHub
release or DOI has been created. No application or resume file was edited.
