from typing import List, Dict, Any, Tuple
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
    """รวม Tag ที่ไม่อยู่ใน Top N เข้ากลุ่ม 'อื่นๆ'"""
    if not top_n_enabled or len(rows) <= top_n:
        return rows
    if not include_others:
        return rows[:top_n]

    head, tail = rows[:top_n], rows[top_n:]
    head.append({
        "tag_id": OTHERS_TAG_ID,
        "tag_name": OTHERS_TAG_NAME,
        "income": float(sum(r["income"] for r in tail)),
        "expense": float(sum(r["expense"] for r in tail)),
    })
    return head


def _format_tag_item(idx: int, r: Dict[str, Any], t_inc: float, t_exp: float) -> Dict[str, Any]:
    """Helper สำหรับจัด Format และคำนวณ % (ช่วยลด Cognitive Complexity)"""
    inc, exp = r["income"], r["expense"]
    return {
        "tag_id": r["tag_id"],
        "tag_name": r["tag_name"],
        "income": inc,
        "expense": exp,
        "net": inc - exp,
        "percent_of_expense": round((exp / t_exp * 100), 2) if t_exp > 0 else 0,
        "percent_of_income": round((inc / t_inc * 100), 2) if t_inc > 0 else 0,
        "color_index": idx
    }


def build_tag_report(db: Session, payload: ReportTagRequest) -> ReportTagResponse:
    # 1. Resolve Range
    start, end = resolve_date_range(
        mode=payload.mode, date=payload.date, month=payload.month,
        year=payload.year, start_date=payload.start_date, end_date=payload.end_date
    )

    # 2. Summary (Income/Expense รวม)
    summary_q = db.query(
        func.coalesce(func.sum(
            case((Transaction.type == "income", Transaction.amount), else_=0)), 0),
        func.coalesce(func.sum(
            case((Transaction.type == "expense", Transaction.amount), else_=0)), 0)
    ).filter(
        Transaction.user_id_line == payload.user_id_line,
        Transaction.transaction_at >= start, Transaction.transaction_at < end,
        Transaction.status == "active"
    ).first()

    income_sum, expense_sum = float(summary_q[0]), float(summary_q[1])

    # 3. เตรียม Expression สำหรับ Group By (Fix GroupingError)
    tag_id_expr = func.coalesce(TagModel.id, OTHERS_TAG_ID)
    tag_name_expr = func.coalesce(TagModel.name, OTHERS_TAG_NAME)

    # 4. Query Group by Tag
    rows = (
        db.query(
            tag_id_expr.label("tag_id"),
            tag_name_expr.label("tag_name"),
            func.coalesce(func.sum(case((Transaction.type == "income",
                          Transaction.amount), else_=0)), 0).label("income"),
            func.coalesce(func.sum(case((Transaction.type == "expense",
                          Transaction.amount), else_=0)), 0).label("expense"),
        )
        .select_from(Transaction)
        .outerjoin(TransactionTag, TransactionTag.transaction_id == Transaction.id)
        .outerjoin(TagModel, TagModel.id == TransactionTag.tag_id)
        .filter(
            Transaction.user_id_line == payload.user_id_line,
            Transaction.transaction_at >= start, Transaction.transaction_at < end,
            Transaction.status == "active"
        )
        # ใช้ expression ตัวเต็มใน group_by
        .group_by(tag_id_expr, tag_name_expr)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    # 5. Normalize & Finalize Data
    raw = [{"tag_id": int(r.tag_id), "tag_name": str(r.tag_name),
            "income": float(r.income), "expense": float(r.expense)}
           for r in rows if float(r.income) > 0 or float(r.expense) > 0]

    normalized = to_top_n_with_others(
        raw, payload.top_n_enabled, payload.top_n, payload.include_others)

    t_inc = sum(r["income"] for r in normalized)
    t_exp = sum(r["expense"] for r in normalized)

    tags_list = [_format_tag_item(i, r, t_inc, t_exp)
                 for i, r in enumerate(normalized)]

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "summary": {"income": income_sum, "expense": expense_sum, "net": income_sum - expense_sum},
        "tags": tags_list,
        "charts": {
            "expense": {
                "bar": [{"x": r["tag_name"], "y": r["expense"]} for r in normalized if r["expense"] > 0],
                "donut": [{"x": r["tag_name"], "y": r["expense"]} for r in normalized if r["expense"] > 0]
            },
            "income": {
                "bar": [{"x": r["tag_name"], "y": r["income"]} for r in normalized if r["income"] > 0],
                "donut": [{"x": r["tag_name"], "y": r["income"]} for r in normalized if r["income"] > 0]
            }
        }
    }
