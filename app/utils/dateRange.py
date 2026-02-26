from datetime import datetime, timedelta
from typing import Tuple


def _day_range(date: str | None) -> Tuple[datetime, datetime]:
    if date:
        target = datetime.fromisoformat(date)
    else:
        target = datetime.now()

    start = target.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


def _7d_range() -> Tuple[datetime, datetime]:
    now = datetime.now()
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    start = (now - timedelta(days=7)).replace(hour=0,
                                              minute=0, second=0, microsecond=0)
    return start, end


def _month_range(month: int, year: int) -> Tuple[datetime, datetime]:
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end


def _year_range(year: int) -> Tuple[datetime, datetime]:
    return datetime(year, 1, 1), datetime(year + 1, 1, 1)


def _custom_range(start_date: str, end_date: str) -> Tuple[datetime, datetime]:
    start = datetime.fromisoformat(
        start_date).replace(hour=0, minute=0, second=0)
    end = datetime.fromisoformat(end_date).replace(
        hour=23, minute=59, second=59)
    return start, end


def resolve_date_range(
    mode: str,
    date: str | None = None,
    month: int | None = None,
    year: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Tuple[datetime, datetime]:

    if mode == "today" or mode == "day":
        return _day_range(date)

    if mode == "7d":
        return _7d_range()

    if mode == "month":
        now = datetime.now()
        m = month if month else now.month
        y = year if year else now.year
        return _month_range(m, y)

    if mode == "year":
        y = year if year else datetime.now().year
        return _year_range(y)

    if mode == "range":
        if not start_date or not end_date:
            raise ValueError(
                "start_date and end_date are required for range mode")
        return _custom_range(start_date, end_date)

    raise ValueError(f"invalid mode: {mode}")
