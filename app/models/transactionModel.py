# app/models/transaction.py
from sqlalchemy import Column, Integer, String, Float, Enum, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import enum
from datetime import datetime

Base = declarative_base()


class TransactionTypeEnum(str, enum.Enum):
    income = "income"
    expense = "expense"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionTypeEnum), nullable=False)
    status = Column(String, default="active")
    user_id = Column(UUID(as_uuid=True), nullable=False)
    source = Column(String, default="web")
    created_at = Column(DateTime, default=datetime.utcnow)
