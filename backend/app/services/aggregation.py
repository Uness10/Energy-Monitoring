"""
Aggregation service — determines the correct aggregation level
based on the requested time range (smart data fetching).
"""

from datetime import datetime, timedelta


def get_aggregation_level(start: datetime, end: datetime) -> str | None:
    """
    Returns the appropriate aggregation level based on time range.

    View Range        | Aggregation  | Max Points/Node
    Last 15 min       | Raw (5-10s)  | ~180
    Last 1 hour       | 1-minute avg | 60
    Last 24 hours     | 5-minute avg | 288
    Last 7 days       | 1-hour avg   | 168
    Last 30 days      | 1-hour avg   | 720
    """
    duration = end - start

    if duration <= timedelta(minutes=15):
        return None  # raw data
    elif duration <= timedelta(hours=1):
        return "1min"
    elif duration <= timedelta(hours=24):
        return "5min"
    else:
        return "1h"
