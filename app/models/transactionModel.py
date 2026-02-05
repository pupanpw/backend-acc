from sqlalchemy import Column, Integer, String, Numeric, Enum, DateTime
import enum
from datetime import datetime
from app.config.database import Base


class TransactionTypeEnum(str, enum.Enum):
    income = "income"
    expense = "expense"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    user_id_line = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    type = Column(Enum(TransactionTypeEnum), nullable=False)
    status = Column(String(10), default="active")
    source = Column(String(20), default="line")
    created_at = Column(DateTime, default=datetime.now)
    transaction_at = Column(DateTime, nullable=False)
