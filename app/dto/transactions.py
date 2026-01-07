from pydantic import BaseModel
from enum import Enum


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


class TransactionPayload(BaseModel):
    title: str
    amount: float
    type: TransactionType
    userIdLine: str


class TransactionResponse(BaseModel):
    id: int
    message: str
