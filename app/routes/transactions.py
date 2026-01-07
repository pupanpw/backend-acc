from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.dto.transactions import TransactionPayload, TransactionResponse
from app.config.database import SessionLocal
from datetime import datetime
from app import models

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=TransactionResponse)
def create_transaction(payload: TransactionPayload, db: Session = Depends(get_db)):
    try:
        transaction = models.Transaction(
            title=payload.title,
            amount=payload.amount,
            type=payload.type.value,
            user_id=payload.userId,
            created_at=datetime.fromisoformat(payload.date)
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return {"id": transaction.id, "message": "Transaction created successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
