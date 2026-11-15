# Notices

The existing repository MIT license and required copyright notice are retained.
Additional reviewed first-party audit code is selected from the private research
repository under the same license; maintenance metadata uses Quantem Research. The statistical
screening v3 module is an explicitly versioned first-party derivative of the
legacy checker; frozen empirical records are not part of this distribution.

The imported source's MIT notice is preserved verbatim in
`LICENSES/Quantem-Research-MIT.txt`, from source revision
`8c58311ced006a079b6cfa03fd6329447aa95004`. Both that notice and the original
checker LICENSE are included in built distributions, along with this file.

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

Licensing does not grant access to private research datasets or evidence.
