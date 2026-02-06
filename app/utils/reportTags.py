# app/utils/reportTags.py

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.transactionModel import Transaction
from app.models.tagModel import Tag as TagModel
from app.models.transactionTagModel import TransactionTag
from app.utils.dateRange import resolve_date_range
from app.dto.reportDto import ReportTagRequest, ReportTagResponse

OTHERS_TAG_ID = 999999
OTHERS_TAG_NAME = "อื่นๆ"


def to_top_n_with_others(
    rows: List[Dict[str, Any]],
    top_n_enabled: bool,
    top_n: int,
    include_others: bool
) -> List[Dict[str, Any]]:

    if not top_n_enabled:
        return rows

    if not include_others:
        return rows[:top_n]

    if len(rows) <= top_n:
        return rows

    head = rows[:top_n]
    tail = rows[top_n:]

    others_income = sum(r["income"] for r in tail)
    others_expense = sum(r["expense"] for r in tail)

    # รวม tail เป็น "อื่นๆ"
    head.append({
        "tag_id": OTHERS_TAG_ID,
        "tag_name": OTHERS_TAG_NAME,
        "income": float(others_income),
        "expense": float(others_expense),
    })

    return head


def build_tag_report(db: Session, payload: ReportTagRequest) -> ReportTagResponse:
    start, end = resolve_date_range(
        mode=payload.mode,
        date=payload.date,
        month=payload.month,
        year=payload.year,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )

    # -----------------------------
    # Summary (income/expense)
    # -----------------------------
    income_sum, expense_sum = db.query(
        func.coalesce(
            func.sum(
                case((Transaction.type == "income", Transaction.amount))
            ),
            0
        ),
        func.coalesce(
            func.sum(
                case((Transaction.type == "expense", Transaction.amount))
            ),
            0
        ),
    ).filter(
        Transaction.user_id_line == payload.user_id_line,
        Transaction.transaction_at >= start,
        Transaction.transaction_at < end,
        Transaction.status == "active"
    ).first()

    income_sum = float(income_sum or 0)
    expense_sum = float(expense_sum or 0)

    # -----------------------------
    # Group by Tag (NULL => "อื่นๆ")
    # -----------------------------
    rows = (
        db.query(
            func.coalesce(TagModel.id, OTHERS_TAG_ID).label("tag_id"),
            func.coalesce(TagModel.name, OTHERS_TAG_NAME).label("tag_name"),
            func.coalesce(
                func.sum(case((Transaction.type == "income", Transaction.amount))),
                0
            ).label("income"),
            func.coalesce(
                func.sum(
                    case((Transaction.type == "expense", Transaction.amount))),
                0
            ).label("expense"),
        )
        .select_from(Transaction)
        .outerjoin(TransactionTag, TransactionTag.transaction_id == Transaction.id)
        .outerjoin(TagModel, TagModel.id == TransactionTag.tag_id)
        .filter(
            Transaction.user_id_line == payload.user_id_line,
            Transaction.transaction_at >= start,
            Transaction.transaction_at < end,
            Transaction.status == "active"
        )
        .group_by(
            func.coalesce(TagModel.id, OTHERS_TAG_ID),
            func.coalesce(TagModel.name, OTHERS_TAG_NAME),
        )
        .order_by(
            func.coalesce(
                func.sum(
                    case((Transaction.type == "expense", Transaction.amount))),
                0
            ).desc(),
            func.coalesce(TagModel.name, OTHERS_TAG_NAME).asc()
        )
        .all()
    )

    raw: List[Dict[str, Any]] = []
    for r in rows:
        inc = float(r.income or 0)
        exp = float(r.expense or 0)
        if inc <= 0 and exp <= 0:
            continue

        raw.append({
            "tag_id": int(r.tag_id),
            "tag_name": str(r.tag_name),
            "income": inc,
            "expense": exp,
        })

    normalized = to_top_n_with_others(
        rows=raw,
        top_n_enabled=payload.top_n_enabled,
        top_n=payload.top_n,
        include_others=payload.include_others
    )

    total_expense = sum(r["expense"] for r in normalized)

    tags = []
    bar = []
    donut = []

    for idx, r in enumerate(normalized):
        exp = float(r["expense"])
        inc = float(r["income"])
        net = inc - exp
        percent = (exp / total_expense * 100) if total_expense > 0 else 0

        tags.append({
            "tag_id": r["tag_id"],
            "tag_name": r["tag_name"],
            "income": inc,
            "expense": exp,
            "net": net,
            "percent_of_expense": round(percent, 2),
            "color_index": idx
        })

        bar.append({"x": r["tag_name"], "y": exp})
        donut.append({"x": r["tag_name"], "y": exp})

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "summary": {
            "income": income_sum,
            "expense": expense_sum,
            "net": income_sum - expense_sum
        },
        "tags": tags,
        "charts": {
            "bar": bar,
            "donut": donut
        }
    }
