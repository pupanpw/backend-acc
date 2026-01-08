from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from app.config.database import SessionLocal
from app.models.periodSummaryModel import PeriodSummary
from app.dto.peroidSummary import (
    SummaryFilterPayload,
    SummaryAggregateResponse,
    SummaryType,
)

router = APIRouter(
    prefix="/period-summary",
    tags=["Period Summary"]
)


# =============================
# Dependency: DB Session
# =============================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================
# PERIOD SUMMARY
# =============================
@router.post("/report", response_model=SummaryAggregateResponse)
def get_period_summary(
    payload: SummaryFilterPayload,
    db: Session = Depends(get_db)
):
    """
    Summary type:
    - daily   -> start_date, end_date
    - monthly -> month, year
    - yearly  -> year
    """

    query = db.query(
        func.coalesce(func.sum(PeriodSummary.total_income),
                      0).label("total_income"),
        func.coalesce(func.sum(PeriodSummary.total_expense),
                      0).label("total_expense"),
        func.coalesce(func.sum(PeriodSummary.total_balance),
                      0).label("total_balance"),
    ).filter(
        PeriodSummary.user_id_line == payload.user_id_line
    )

    # ---------- DAILY ----------
    if payload.type == SummaryType.daily:
        query = query.filter(
            PeriodSummary.summary_date.between(
                payload.start_date,
                payload.end_date
            )
        )

    # ---------- MONTHLY ----------
    elif payload.type == SummaryType.monthly:
        query = query.filter(
            func.extract("month", PeriodSummary.summary_date) == payload.month,
            func.extract("year", PeriodSummary.summary_date) == payload.year,
        )

    # ---------- YEARLY ----------
    elif payload.type == SummaryType.yearly:
        query = query.filter(
            func.extract("year", PeriodSummary.summary_date) == payload.year
        )

    result = query.first()

    if not result:
        return SummaryAggregateResponse(
            total_income=0,
            total_expense=0,
            total_balance=0,
        )

    return SummaryAggregateResponse(
        user_id_line=payload.user_id_line,
        total_income=result.total_income,
        total_expense=result.total_expense,
        total_balance=result.total_balance,
    )
