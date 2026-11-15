"""Statistical illustration: same-period signal and generated forward oracle.

Both arrays are generated, not delivered model forecasts. The forward oracle is
constructed from future returns; a nonflagged timing screen is not availability
validation. Run quantem-checker demo for direct good/bad pipeline controls.
"""

import numpy as np

from quantem_checker import audit_prefix_consistency, run_check
from quantem_checker.__main__ import _format_table


def leaked(T=400, N=150, lam=0.30, seed=0):
    rng = np.random.default_rng(seed)
    ret = rng.standard_normal((T, N))
    pred = lam * ret + np.sqrt(1 - lam**2) * rng.standard_normal((T, N))
    return pred, ret


def clean_forward(T=400, N=150, lam=0.10, seed=1):
    """Legacy helper name: generated future oracle, not a causal forecast."""
    rng = np.random.default_rng(seed)
    ret = rng.standard_normal((T, N))
    pred = np.empty((T, N))
    pred[:-1] = lam * ret[1:] + np.sqrt(1 - lam**2) * rng.standard_normal((T - 1, N))
    pred[-1] = rng.standard_normal(N)
    return pred, ret


def main():
    print("\nA generated same-period signal — expected timing screen flag:\n")
    p, r = leaked()
    leak_rec = run_check(p, r, name="leaked-signal")
    print(_format_table(leak_rec))

    print(
        "\n\nA generated forward oracle — timing nonflag does not establish availability:\n"
    )
    p, r = clean_forward()
    clean_rec = run_check(p, r, name="generated-forward-oracle")
    print(_format_table(clean_rec))

    print("\n")
    assert leak_rec["leak_flagged"] and not leak_rec["survives_battery"], (
        "leak should be caught"
    )
    assert clean_rec["leak_flagged"] is False, (
        "forward oracle expected not to trigger this timing symptom"
    )
    direct = audit_prefix_consistency(
        lambda d: {"score": np.roll(d["returns"], -1, axis=0)},
        {"returns": r},
        [100, 200],
    )
    assert direct["verdict"] == "FAIL", (
        "actual future-dependent pipeline must fail direct probes"
    )
    print(
        "Expected screen symptoms observed; direct audit rejects the future oracle. No market or availability claim.\n"
    )


if __name__ == "__main__":
    main()
