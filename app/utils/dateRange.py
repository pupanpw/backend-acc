from datetime import datetime, timedelta
from typing import Tuple


def _day_range(date: str | None) -> Tuple[datetime, datetime]:
    target = datetime.fromisoformat(date) if date else datetime.now()
    start = target.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


def _month_range(month: int, year: int) -> Tuple[datetime, datetime]:
    start = datetime(year, month, 1)
    end = datetime(
        year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    return start, end


def _year_range(year: int) -> Tuple[datetime, datetime]:
    return datetime(year, 1, 1), datetime(year + 1, 1, 1)


def _custom_range(start_date: str, end_date: str) -> Tuple[datetime, datetime]:
    return (
        datetime.fromisoformat(start_date),
        datetime.fromisoformat(end_date),
    )


def resolve_date_range(
    mode: str,
    date: str | None = None,
    month: int | None = None,
    year: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Tuple[datetime, datetime]:

    if mode == "day":
        return _day_range(date)

    if mode == "month":
        if not month or not year:
            raise ValueError("month and year are required")
        return _month_range(month, year)

    if mode == "year":
        if not year:
            raise ValueError("year is required")
        return _year_range(year)

    if mode == "range":
        if not start_date or not end_date:
            raise ValueError("start_date and end_date are required")
        return _custom_range(start_date, end_date)

    raise ValueError("invalid mode")
