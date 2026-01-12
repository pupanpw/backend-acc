from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session
from app.dto.transactions import FilterMode, TransactionPayload, TransactionResponse, TransactionUpdatePayload
from app.config.database import SessionLocal
from datetime import datetime, timedelta
from app.models.transactionModel import Transaction
from app.utils.dateRange import resolve_date_range

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
            )
        )
        .order_by(Transaction.transaction_at.desc())
        .all()
    )


@router.get("/today")
def get_today_transactions(
    user_id_line: str,
    db: Session = Depends(get_db)
):
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    return db.query(Transaction).filter(
        and_(
            Transaction.user_id_line == user_id_line,
            Transaction.transaction_at >= start,
            Transaction.transaction_at < end,
            Transaction.status == "active"
        )
    ).order_by(Transaction.transaction_at.desc()).all()


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

    return {"message": "Transaction deleted successfully"}
