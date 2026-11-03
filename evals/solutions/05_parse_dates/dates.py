from datetime import datetime


def parse_date(s):
    """Parse an ISO date string like '2026-11-02' into a date."""
    return datetime.strptime(s, "%Y-%m-%d").date()
