from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session
from app.dto.transactions import FilterMode, TransactionPayload, TransactionResponse, TransactionUpdatePayload
from app.config.database import SessionLocal
from datetime import datetime, timedelta
from app.models.periodSummaryModel import PeriodSummary
from app.models.transactionModel import Transaction
from app.models.transactionTagModel import TransactionTag
from app.utils.dateRange import resolve_date_range
from sqlalchemy import and_, func, case
from app.models.tagModel import Tag as TagModel
from app.models.transactionTagModel import TransactionTag
from app.utils.tags import make_slug, normalize_tag_name
router = APIRouter(prefix="/transactions", tags=["Transactions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/create", response_model=TransactionResponse)
def create_transaction(payload: TransactionPayload, db: Session = Depends(get_db)):
    try:
        transaction = Transaction(
            title=payload.title,
            amount=payload.amount,
            type=payload.type.value,
            user_id_line=payload.userIdLine,
            transaction_at=payload.transactionAt,
            created_at=datetime.now()
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return {"id": transaction.id, "message": "Transaction created successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
def get_transactions(
    user_id_line: str = Query(...),
    mode: FilterMode = Query(...),
    date: str | None = None,
    month: int | None = None,
    year: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        start, end = resolve_date_range(
            mode=mode,
            date=date,
            month=month,
            year=year,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return (
        db.query(Transaction)
        .filter(
            and_(
                Transaction.user_id_line == user_id_line,
                Transaction.transaction_at >= start,
                Transaction.transaction_at < end,
                Transaction.status == "active",
                Transaction.source != "auto",
            )
        )
        .order_by(Transaction.transaction_at.desc())
        .all()
    )


@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdatePayload,
    user_id_line: str,
    db: Session = Depends(get_db)
):
    tx = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id_line == user_id_line,
        Transaction.status == "active"
    ).first()

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if payload.title is not None:
        tx.title = payload.title
    if payload.amount is not None:
        tx.amount = payload.amount
    if payload.type is not None:
        tx.type = payload.type.value

    db.commit()
    return {"message": "Transaction updated"}


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    user_id_line: str = Query(...),
    db: Session = Depends(get_db),
):
    tx = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id_line == user_id_line,
            Transaction.status == "active",
        )
        .first()
    )

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    tx.status = "inactive"
    db.commit()

    target_date = tx.transaction_at.date()

    income_sum, expense_sum = db.query(
        func.coalesce(
            func.sum(
                case(
                    (Transaction.type == "income", Transaction.amount)
                )
            ),
            0
        ),
        func.coalesce(
            func.sum(
                case(
                    (Transaction.type == "expense", Transaction.amount)
                )
            ),
            0
        )
    ).filter(
        Transaction.user_id_line == user_id_line,
        func.date(Transaction.transaction_at) == target_date,
        Transaction.status == "active"
    ).first()

    ps = db.query(PeriodSummary).filter(
        PeriodSummary.user_id_line == user_id_line,
        PeriodSummary.summary_date == target_date
    ).first()

    if ps:
        ps.total_income = income_sum
        ps.total_expense = expense_sum
        ps.total_balance = income_sum - expense_sum
        ps.updated_at = func.now()
    else:
        ps = PeriodSummary(
            user_id_line=user_id_line,
            summary_date=target_date,
            total_income=income_sum,
            total_expense=expense_sum,
            total_balance=income_sum - expense_sum,
            created_at=func.now(),
            updated_at=func.now()
        )
        db.add(ps)

    db.commit()

    return {"detail": "Transaction deleted (soft delete) and summary updated"}


@router.post("/{transaction_id}/cancel")
def cancel_transaction(
    transaction_id: int,
    user_id_line: str = Query(...),
    db: Session = Depends(get_db),
):
    tx = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id_line == user_id_line,
            Transaction.status == "active",
        )
        .first()
    )

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # 1) ปิดรายการเดิม
    tx.status = "inactive"

    # 2) สร้างรายการคืนยอด
    refund = Transaction(
        title=f"ยกเลิกการทำรายการ: {tx.title}",
        amount=tx.amount,
        type="income" if tx.type == "expense" else "expense",
        user_id_line=tx.user_id_line,
        transaction_at=tx.transaction_at,
        created_at=datetime.now(),
        source="auto",
        status="active",
    )

    db.add(refund)

    # 3) update summary ของวันนั้น (เหมือนโค้ดเดิมคุณ)
    target_date = tx.transaction_at.date()

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
        )
    ).filter(
        Transaction.user_id_line == user_id_line,
        func.date(Transaction.transaction_at) == target_date,
        Transaction.status == "active"
    ).first()

    ps = db.query(PeriodSummary).filter(
        PeriodSummary.user_id_line == user_id_line,
        PeriodSummary.summary_date == target_date
    ).first()

    if ps:
        ps.total_income = income_sum
        ps.total_expense = expense_sum
        ps.total_balance = income_sum - expense_sum
        ps.updated_at = func.now()
    else:
        ps = PeriodSummary(
            user_id_line=user_id_line,
            summary_date=target_date,
            total_income=income_sum,
            total_expense=expense_sum,
            total_balance=income_sum - expense_sum,
            created_at=func.now(),
            updated_at=func.now()
        )
        db.add(ps)

    db.commit()

    return {"detail": "Transaction canceled and refund created"}


@router.get("/today")
def get_today_transactions(user_id_line: str, db: Session = Depends(get_db)):
    THAI_TZ = ZoneInfo("Asia/Bangkok")
    now = datetime.now(THAI_TZ)

    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    transactions = db.query(Transaction).filter(
        and_(
            Transaction.user_id_line == user_id_line,
            Transaction.transaction_at >= start,
            Transaction.transaction_at < end,
            # Transaction.status == "active"
        )
    ).order_by(Transaction.transaction_at.desc()).all()

    return transactions


@router.post("/create/v2", response_model=TransactionResponse)
def create_transaction(payload: TransactionPayload, db: Session = Depends(get_db)):
    try:
        transaction = Transaction(
            title=payload.title,
            amount=payload.amount,
            type=payload.type.value,
            user_id_line=payload.userIdLine,
            transaction_at=payload.transactionAt,
            created_at=datetime.now(),
            status="active",
        )
        db.add(transaction)
        db.flush()  # ได้ transaction.id โดยยังไม่ commit

        # ---- handle tags (optional) ----
        tags = payload.tags or []
        cleaned = []
        seen = set()
        for t in tags:
            n = normalize_tag_name(t)
            if not n:
                continue
            key = n.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(n)

        if cleaned:
            # 1) fetch existing tags for this user & these slugs
            slugs = [make_slug(x) for x in cleaned]
            existing = (
                db.query(TagModel)
                .filter(TagModel.user_id_line == payload.userIdLine, TagModel.slug.in_(slugs))
                .all()
            )
            by_slug = {x.slug: x for x in existing}

            tag_ids = []
            for name in cleaned:
                slug = make_slug(name)
                tag = by_slug.get(slug)
                if not tag:
                    tag = TagModel(user_id_line=payload.userIdLine,
                                   name=name, slug=slug)
                    db.add(tag)
                    db.flush()  # ได้ tag.id
                    by_slug[slug] = tag

                tag_ids.append(tag.id)

            for tag_id in tag_ids:
                db.add(TransactionTag(transaction_id=transaction.id, tag_id=tag_id))

        db.commit()
        db.refresh(transaction)

        return {"id": transaction.id, "message": "Transaction created successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/today/v2")
def get_today_transactions_with_tags(user_id_line: str, db: Session = Depends(get_db)):
    THAI_TZ = ZoneInfo("Asia/Bangkok")
    now = datetime.now(THAI_TZ)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    rows = (
        db.query(Transaction, TagModel)
        .outerjoin(TransactionTag, TransactionTag.transaction_id == Transaction.id)
        .outerjoin(TagModel, TagModel.id == TransactionTag.tag_id)
        .filter(
            Transaction.user_id_line == user_id_line,
            Transaction.transaction_at >= start,
            Transaction.transaction_at < end,
        )
        .order_by(Transaction.transaction_at.desc())
        .all()
    )

    result = {}
    for tx, tag in rows:
        if tx.id not in result:
            result[tx.id] = {
                "id": tx.id,
                "title": tx.title,
                "amount": tx.amount,
                "type": tx.type,
                "status": tx.status,
                "source": tx.source,
                "created_at": tx.created_at,
                "transaction_at": tx.transaction_at,
                "tags": []
            }
        if tag:
            result[tx.id]["tags"].append(
                {"id": tag.id, "name": tag.name, "slug": tag.slug})

    return list(result.values())
