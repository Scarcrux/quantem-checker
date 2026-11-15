# Quantem Checker 0.2.0a1: proposed source release

Prepared 2026-11-15 at the owner's request. **Not yet approved or published.**
The owner has approved existing copyright and historical package-author
attribution for this repository; see ATTRIBUTION-EXCEPTION.md.

## Action proposed for approval

Make the existing `Scarcrux/quantem-checker` repository public at
`https://github.com/Scarcrux/quantem-checker`, retaining its current history.
Set its description to:

> Local temporal pipeline probes, supplied-clock and portfolio-ledger audits.

This is a source-first prerelease. The scope is the exact committed tree and
reachable history bound by the final local approval manifest, not an arbitrary
future branch tip. Recheck remote HEAD and PRIVATE visibility before acting;
if the tree or history changes, review the difference before applying approval.

No GitHub release, release tag, package registry upload, wheel/sdist upload,
website deployment, dataset publication or paper-evidence release is proposed.
Private package artifacts are verification evidence, not additional uploads.

## What becomes visible

- All current tracked source modules, tests, generated examples, README,
  changelog, package configuration, LICENSE and imported-source MIT notice.
- Existing Git history, including original `bc4751c` package-author attribution,
  old diagnostic claims and the subsequent documented corrections.
- `commandem.toml`, attribution authorization and integration/release reviews,
  source/output hashes and private research revision identifiers. Those hashes
  do not grant access to the separate research repository or its datasets.
- This proposal and its preparation record. Earlier private/HOLD statements
  are historical review snapshots, not descriptions of a future public state.

The existing attribution exception covers the reviewed names; no new personal
contact details are authorized. New maintenance commits remain organization/
handle attribution with GitHub noreply email. Existing notices are preserved.

## Excluded content and scientific boundaries

No research dataset, vendor feed, account, private paper verifier, empirical
evidence, model weight, execution record, PDF or production platform is included.
Examples generate their inputs locally. The paper's outstanding historical
provenance and empirical limitations remain unresolved by this software work.

Direct checks test supplied callbacks, clocks and long-only accounting. They
do not establish universal causal correctness, true historical receipt times,
execution authenticity, market profitability, calibrated error rates or graph
superiority. Callback code is trusted, not sandboxed. Reports can carry caller
identifiers and are not automatically anonymized. The dependency/platform
minimum-version matrix has not been fully validated. No external adoption or
independent validation is claimed.

## Verification for the prepared wording

- Full selected standalone suite: **53 passed in 1.85s**, zero skips.
- Ruff and whitespace checks pass; runtime, tests and examples are unchanged
  from the already reviewed integration revision.
- Five pre-preparation reachable commits scanned with fully redacted Gitleaks:
  no findings. Current-tree scan is recorded in RELEASE-PREPARATION.json. Pattern
  scans do not guarantee absence of every possible secret.
- Wheel and source distribution build and pass Twine; all nine runtime modules
  and both license notices match source bytes. Complete artifact inventories
  and SHA256 hashes are in RELEASE-PREPARATION.json.
- Fresh installed wheel outside source, without pandas or the research platform:
  all eight demo controls, help, compatibility import identity, README API
  example, empty-clock NOT TESTED, missing-Parquet-dependency exit 2 and
  dependency consistency pass. Final artifact installation is also checked.

The new README explains the actual checks and their limits, gives source
installation and local demo commands, and links the changelog and provenance
record. The package Repository metadata points to the existing destination.
No public availability is claimed before approval and verification.

## Publication completion criteria, only after approval

Verify the approved exact commit and private repository identity; change the
description and visibility only as approved. Then verify public code/README and
anonymous access to the approved commit, and record the public URL and exact
published commit. Keep datasets, the separate research repository and package
uploads private. Record completion in the roadmap; do not infer public
availability from a successful API mutation alone.
