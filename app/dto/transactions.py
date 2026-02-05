from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


class FilterMode(str, Enum):
    day = "day"
    month = "month"
    year = "year"


class TransactionPayload(BaseModel):
    title: str
    amount: float
    type: TransactionType
    userIdLine: str
    transactionAt: datetime
    tags: Optional[List[str]] = []   # << เพิ่ม


class TransactionUpdatePayload(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    type: Optional[TransactionType] = None
    transactionAt: Optional[datetime] = None


class TransactionResponse(BaseModel):
    id: int
    message: str
