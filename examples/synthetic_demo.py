"""Synthetic demo: quantem-checker flags a known leak and passes a clean forward signal.

Run:  python examples/synthetic_demo.py

Generates two signals with known ground truth on the same random returns panel:

  * a LEAKED signal correlated with the same period's return (a contemporaneous
    lookahead — the single most common backtest bug), and
  * a CLEAN forward signal correlated with next period's return.

quantem-checker must flag the first and pass the second. This is the harness's own
ground-truth validation, reproduced here so anyone can see the collapse table.
"""
import numpy as np

from quantem_checker import run_check
from quantem_checker.__main__ import _format_table


def leaked(T=400, N=150, lam=0.30, seed=0):
    rng = np.random.default_rng(seed)
    ret = rng.standard_normal((T, N))
    pred = lam * ret + np.sqrt(1 - lam ** 2) * rng.standard_normal((T, N))
    return pred, ret


def clean_forward(T=400, N=150, lam=0.10, seed=1):
    rng = np.random.default_rng(seed)
    ret = rng.standard_normal((T, N))
    pred = np.empty((T, N))
    pred[:-1] = lam * ret[1:] + np.sqrt(1 - lam ** 2) * rng.standard_normal((T - 1, N))
    pred[-1] = rng.standard_normal(N)
    return pred, ret


def main():
    print("\nA contemporaneous lookahead leak — quantem-checker must FLAG it:\n")
    p, r = leaked()
    leak_rec = run_check(p, r, name="leaked-signal")
    print(_format_table(leak_rec))

    print("\n\nA clean one-period-ahead signal — quantem-checker must PASS it:\n")
    p, r = clean_forward()
    clean_rec = run_check(p, r, name="clean-forward-signal")
    print(_format_table(clean_rec))

    print("\n")
    assert leak_rec["leak_flagged"] and not leak_rec["survives_battery"], "leak should be caught"
    assert not clean_rec["leak_flagged"], "clean signal should not be flagged as a leak"
    print("✓ leak flagged, clean signal passed — ground truth recovered.\n")


if __name__ == "__main__":
    main()
