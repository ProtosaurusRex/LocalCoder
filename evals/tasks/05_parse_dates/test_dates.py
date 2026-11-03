from datetime import date

from dates import parse_date


def test_parse():
    assert parse_date("2026-11-02") == date(2026, 11, 2)


def test_parse_late_month():
    assert parse_date("2026-12-25") == date(2026, 12, 25)
