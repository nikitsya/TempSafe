"""Classify observation age independently of temperature."""

from datetime import datetime, timedelta
from typing import Literal


def classify_freshness(
        observed_at: datetime | None,
        clock_reliable: bool,
        now: datetime,
) -> Literal["fresh", "stale", "unknown"]:
    """Compare timezone-aware timestamps; exactly 90 seconds remains fresh."""
    if not clock_reliable or observed_at is None:
        return "unknown"
    age = now - observed_at
    if age < timedelta(0):
        return "unknown"
    return "stale" if age > timedelta(seconds=90) else "fresh"
