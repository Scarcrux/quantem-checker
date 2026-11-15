# Private review of proposed public scope

Review date: 2026-11-15. Reviewed repository baseline:
`473ad962db7a2aa81b203f251427c7c83f99a6c4f6`.

**Verdict: useful software candidate; public release remains on HOLD.**
The review fixes an omitted imported-source notice and verifies the resulting
private artifacts. It does not authorize publication, identity exceptions,
notice replacement, history rewriting or dataset disclosure.

## Evidence and what it establishes

| Area | Result and practical limit |
| --- | --- |
| Reachable Git history | Three commits, one remote branch (`main`), no tags. Examined every tracked file at each commit. No dataset, model weight, PDF, credential file, submodule or LFS payload is present in the inspected trees. |
| Secret scans | Fully redacted Gitleaks scan of all three reachable commits and working directory: no findings. Pattern scans cannot prove absence of every secret. |
| Identity | Current LICENSE contains personal attribution; original `bc4751c` package metadata also contains personal attribution. All three commits use reviewed organization/handle identities and GitHub noreply emails. Earlier generic warnings must not be read as a finding of personal commit authorship. |
| Other GitHub surfaces | Zero releases, tags, workflows, workflow runs, issues/PRs, issue comments and review comments observed. No public visibility change occurred. Unreachable server objects or copies outside this repository are not covered. |
| Provenance | Eight imported source/test files have source/output hashes in `INTEGRATION-SOURCES.json`; source license verified at imported revision `8c58311c`, not inferred from a current checkout. Hash bindings establish file lineage, not independent proof of ownership or employment/assignment rights. |
| Software verification | 53 tests pass in 1.73s, zero skips; wheel/sdist build and Twine checks pass. All nine packaged runtime modules match source and are unchanged from the already verified integration baseline. Tests and examples are also unchanged. No new research run. |
| Package inspection | Both rebuilt distributions contain the unchanged original LICENSE, the imported source's exact MIT notice and NOTICES.md. No restricted data/paper file types or dependency source are bundled. Both artifacts still expose the required personal notice. |

[PUBLIC-SCOPE-REVIEW.json](PUBLIC-SCOPE-REVIEW.json) binds the inspected baseline,
file hashes, historical identity locations and complete artifact inventories.
The script's initial wheel-path assertion treated a top-level package path as
though it had an archive directory prefix; correcting that inspection logic
made the byte comparisons pass. No product code was changed to satisfy it.

## Notice correction made during this review

The original checker MIT notice was preserved, but the imported research
source's separate MIT copyright notice was missing from the integrated package.
Added `LICENSES/Quantem-Research-MIT.txt` verbatim from source revision
`8c58311ced006a079b6cfa03fd6329447aa95004`, updated NOTICES.md, and configured
the build to include both notices and NOTICES.md. The original LICENSE remains
byte-identical to `bc4751c`. No copyright holder was silently renamed.

The [MIT license text](https://opensource.org/license/mit) requires retention
of its copyright and permission notice with copies or substantial portions.
The observed license files support distribution subject to their terms; this
review does not independently establish every underlying rights assignment.

| Private artifact | SHA256 |
| --- | --- |
| `quantem_checker-0.2.0a1-py3-none-any.whl` | `023bb5d5e6a8170a9526c409f9a50aaf83ebf24a4da48a19e3f7b789fbcfb95f` |
| `quantem_checker-0.2.0a1.tar.gz` | `0d053512bdced05e8250e8c7f9a4b1d5d568894d23c2870d611826f865e4ea97` |

These private rebuilds supersede the earlier integration artifacts for notice
completeness. Old hashes in PRIVATE-INTEGRATION-REVIEW.json describe the earlier
build at its recorded source revision; they are not hashes of these new files.
Neither build is approved for public distribution.

## Exact exposure by release route

**Making the existing repository public** exposes its current tracked source,
tests, examples, README, notices, operational roadmap/review documents, private
research revision references and reachable history. That history includes old
package-author attribution and outdated diagnostic claims. Current documentation
corrects the claims; it cannot erase them from historical commits. This review
and its manifest would also become visible if committed before that change.
GitHub documents that [public visibility exposes code and Actions history](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility).

**Publishing only a wheel or source distribution** omits Git history and the
operational roadmap/review documents in these inspected builds. It still exposes
the existing personal LICENSE notice. A clean-history snapshot similarly cannot
solve that notice conflict by itself. No new repository or snapshot is needed
or approved merely because this alternative was evaluated.

## Public gates and recommendation

1. Resolve the standing privacy rule's conflict with the required personal
   notice. Keep the notice unless an authorized rights-holder disposition is
   established. A narrow privacy exception to retain that notice is an owner
   decision; it is not implied by the paper's public author identity. This review
   recommends keeping the project private until that decision is explicit.
2. If the existing history is to become visible, explicitly review the original
   package metadata and historical claims as part of that exact scope. Any
   alternative history treatment needs separate authorization; none was done.
3. Prepare publication wording after the scope decision. The current GitHub
   description still says “detecting lookahead/leakage”; recommended wording is
   “Local temporal pipeline probes, supplied-clock and portfolio-ledger audits.”
   README/private-status language, source links and package landing-page links
   need a final pass for the chosen destination. No external metadata was edited.
4. Obtain explicit manual approval of the exact repository/history or package
   artifacts before publication. The project's AGENTS.md requires prior approval
   for public visibility and for private-code publication by side effect.

The software is useful without distributing datasets: users run it locally with
authorized inputs and callbacks. A defensible portfolio description is
“Developed and tested a local financial-ML audit toolkit with temporal probes,
availability-clock checks and ledger reconciliation.” Public availability,
external adoption and independent validation are not currently established.

Finite generated controls do not prove universal leakage detection, authentic
historical timestamps or execution marks, profitable strategies, calibrated
error rates, graph superiority or reproduction of the empirical paper. Only one
Python/macOS dependency environment has been tested; the minimum-version matrix
remains unverified. Callbacks are trusted local code and may access external
state; audit reports can contain caller-supplied stage/event identifiers and
should not be treated as automatically anonymized public evidence.

No dataset transfer, public release, deployment, public upload, application edit
or history rewrite was performed in this review. The original empirical manuscript and its
evidence/provenance limitations are unchanged.
