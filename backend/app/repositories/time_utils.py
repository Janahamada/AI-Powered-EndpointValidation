"""
Timestamp normalization helpers.

Evidence timestamps arrive as ISO strings (SQLite) or datetime objects
(other drivers). These convert them to ages (hours/days) relative to now, so
the validators never touch wall-clock time — computed once, here.
"""

from datetime import datetime
from typing import Optional


def parse_dt(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def hours_since(dt: Optional[datetime], reference: Optional[datetime] = None) -> Optional[int]:
    """Age in whole hours between `dt` and `reference` (default: wall-clock now).

    `reference` lets freshness be evaluated against the dataset's own
    collection time rather than the wall clock — see
    `control_repo.reference_time`. Ages are clamped at 0 (evidence stamped
    slightly after the reference is treated as fresh, not negative)."""
    if dt is None:
        return None
    ref = reference or datetime.now()
    return max(0, int((ref - dt).total_seconds() // 3600))


def days_since(dt: Optional[datetime], reference: Optional[datetime] = None) -> Optional[int]:
    hours = hours_since(dt, reference)
    return None if hours is None else hours // 24
