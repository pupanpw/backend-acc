from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta

from app.config.database import SessionLocal
from app.models.periodSummaryModel import PeriodSummary
from app.dto.peroidSummary import (
    SummaryFilterPayload,
    SummaryAggregateResponse,
    SummaryType,
)

router = APIRouter(prefix="/period-summary", tags=["Period Summary"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _month_range(year: int, month: int) -> tuple[date, date]:
    # [start, end)  end = first day of next month
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="month must be 1..12")

    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start, end


def _year_range(year: int) -> tuple[date, date]:
    # [start, end)
    start = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    return start, end


@router.post("/report", response_model=SummaryAggregateResponse)
def get_period_summary(payload: SummaryFilterPayload, db: Session = Depends(get_db)):
    """
    Summary type:
    - daily   -> start_date, end_date
    - monthly -> month, year
    - yearly  -> year
    """

    if not payload.user_id_line:
        raise HTTPException(status_code=400, detail="user_id_line is required")

    # ---- resolve date range (inclusive for daily input) ----
    start: date | None = None
    end_exclusive: date | None = None  # use [start, end_exclusive)

    if payload.type == SummaryType.daily:
        if payload.start_date is None or payload.end_date is None:
            raise HTTPException(
                status_code=400, detail="start_date and end_date are required for daily")

        if payload.start_date > payload.end_date:
            raise HTTPException(
                status_code=400, detail="start_date must be <= end_date")

        start = payload.start_date
        end_exclusive = payload.end_date + timedelta(days=1)

    elif payload.type == SummaryType.monthly:
        if payload.year is None or payload.month is None:
            raise HTTPException(
                status_code=400, detail="year and month are required for monthly")

        start, end_exclusive = _month_range(payload.year, payload.month)

    elif payload.type == SummaryType.yearly:
        if payload.year is None:
            raise HTTPException(
                status_code=400, detail="year is required for yearly")

        start, end_exclusive = _year_range(payload.year)

    else:
        raise HTTPException(status_code=400, detail="Invalid summary type")

    base = (
        db.query(PeriodSummary)
        .filter(PeriodSummary.user_id_line == payload.user_id_line)
        .filter(PeriodSummary.summary_date >= start)
        .filter(PeriodSummary.summary_date < end_exclusive)
    )

    # scalar() จะคืนค่าเดียว ไม่ต้อง first() และไม่หลุด None แบบงง ๆ
    total_income = base.with_entities(func.coalesce(
        func.sum(PeriodSummary.total_income), 0)).scalar() or 0
    total_expense = base.with_entities(func.coalesce(
        func.sum(PeriodSummary.total_expense), 0)).scalar() or 0
    total_balance = base.with_entities(func.coalesce(
        func.sum(PeriodSummary.total_balance), 0)).scalar() or 0

    return SummaryAggregateResponse(
        user_id_line=payload.user_id_line,
        total_income=total_income,
        total_expense=total_expense,
        total_balance=total_balance,
    )
