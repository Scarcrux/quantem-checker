"""Explicit execution-lineage audit, separate from statistical IC screening."""

from __future__ import annotations

from datetime import datetime


def _timestamp(value):
    stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("timezone-aware timestamp required")
    return stamp


def audit_event_clock(receipts):
    """Check supplied receipts, not the truth/completeness of historical logs.

    Exact-cutoff arrivals are excluded. An empty log cannot establish delivery.
    """
    errors = []
    for i, row in enumerate(receipts):
        try:
            public, available, cutoff, entry, exit_time = (
                _timestamp(row[k])
                for k in ("published_at", "available_at", "cutoff", "entry", "exit")
            )
            if not public <= available < cutoff < entry < exit_time:
                errors.append(
                    {
                        "receipt": i,
                        "event_id": row.get("event_id"),
                        "reason": "unavailable_at_order_or_invalid_clock",
                    }
                )
        except (KeyError, TypeError, ValueError):
            errors.append(
                {
                    "receipt": i,
                    "event_id": row.get("event_id"),
                    "reason": "missing_or_naive_clock",
                }
            )
    return {
        "verdict": "FAIL" if errors else ("PASS" if receipts else "NOT TESTED"),
        "n_receipts": len(receipts),
        "errors": errors,
        "scope": "supplied execution-lineage receipts; not statistical leakage proof",
    }
