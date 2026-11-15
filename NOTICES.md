# Notices

The existing repository MIT license and required copyright notice are retained.
Additional reviewed first-party audit code is selected from the private research
repository under the same license; maintenance metadata uses Quantem Research. The statistical
screening v3 module is an explicitly versioned first-party derivative of the
legacy checker; frozen empirical records are not part of this distribution.

This archive does not bundle dependency source or wheels. NumPy is installed
separately (BSD-3-Clause). Optional pandas (BSD-3-Clause) and PyArrow (Apache-2.0)
support user-supplied Parquet input. Pytest (MIT) and build tooling are development
dependencies. Installed distributions retain their own notices. The first-party
MIT notice does not relicense those dependencies, vendor data or paper results.

Prefix/truncation and input-perturbation testing are established techniques;
this toolkit does not claim to have invented them. Freqtrade documents a related
strategy-specific lookahead analysis:
https://www.freqtrade.io/en/stable/lookahead-analysis/
The implementation here is first-party code, not a bundled Freqtrade dependency
or implementation. No affiliation or endorsement is implied.

The candidate is private and not yet cleared for external distribution.
