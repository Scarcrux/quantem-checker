"""Compatibility example path; the old specificity grid is retired.

Its former labels conflated forward prediction with availability: an oracle made
from future returns could be called honest. Those rates are not calibrated causal
leakage error rates. Historical source remains at bc4751c. This entry now exercises
the bounded generated pipeline/clock/ledger controls, not a new grid study.
"""

from quantem_checker.audit_demo import demo_report


def main():
    report = demo_report()
    print("Generated control verdicts (not calibrated detection rates):")
    for name, value in report["cases"].items():
        print(f"  {name}: {value['verdict']} (expected {report['expected'][name]})")
    return 0 if report["all_expected_verdicts_observed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
