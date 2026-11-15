# Private integration criteria

Owner selected the existing private `quantem-checker` repository as the project
home. Baseline `bc4751c` is retained in Git history; no history rewrite, public
visibility change, package publication or research-data movement is authorized.

Integrate the reviewed first-party toolkit source `8c58311c` from the private
research checkout, not its historical datasets, evidence or paper verifier.
Record exact source/output hashes and namespace/schema-label transformations.

Required checks before a private push:

1. Preserve library import names, helper exports and legacy CLI flags. Keep
   `quantem_checker.core` as an explicit compatibility entry point. Document
   corrected version-3 semantics and minimum-runtime/dependency changes rather
   than imply byte-identical old results.
2. Accept identical unique time/asset axes; reject mismatched, duplicate or
   reversed time axes. No implicit join, sorting, dropping or graph reshaping.
   CLI returns 2 for invalid/insufficient evidence and prints/writes valid JSON
   with nullable metrics. Table formatting must handle unavailable values.
3. Actual generated pipeline, clock and ledger controls must discriminate
   PASS/FAIL/NOT TESTED through real local entry points. Empty/unknown must not
   become clean. Include CLI demonstrations and portable input-contract tests.
4. Retain existing synthetic test cases with corrected descriptions. A
   forward-generated oracle is not an availability-clean predictor. The old
   specificity grid's predictive-vs-nonpredictive labels are not causal leakage
   ground truth: retire its rate claims, preserve historical code in Git, and
   provide a bounded deterministic replacement without a new seed/grid study.
5. Run source tests, fresh core/dev/Parquet tests and builds. Install wheel into
   a separate NumPy-only environment outside source and run the real demo/help,
   then exercise optional Parquet CLI behavior in an appropriately configured
   environment. No paid API, data acquisition, model training or broad benchmark.
6. Inspect only this task's changes for secrets and new private identities.
   Retain the existing required LICENSE notice unchanged. Package maintenance
   metadata and new commits use organization/noreply identity. Existing personal
   attribution in history/LICENSE is a separate public privacy/notice gate, not
   silently removed during integration.
7. Land in the standalone project's integration lane, verify origin still names
   the same private repository and confirm it remains private immediately before
   any normal fast-forward push. Never force-push or flip visibility. Report the
   exact remote commit and tested scope, not an unperformed public release.
