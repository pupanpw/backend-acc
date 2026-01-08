from enum import Enum
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


# =========================
# Summary Type
# =========================
class SummaryType(str, Enum):
    daily = "daily"
    monthly = "monthly"
    yearly = "yearly"


# =========================
# FILTER PAYLOAD
# =========================
class SummaryFilterPayload(BaseModel):
    type: SummaryType
    user_id_line: str

    # daily (between)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # monthly / yearly
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = Field(None, ge=1900)

    @model_validator(mode="after")
    def validate_by_type(self):
        if self.type == SummaryType.daily:
            if not self.start_date or not self.end_date:
                raise ValueError("daily requires start_date and end_date")
            if self.start_date > self.end_date:
                raise ValueError("start_date must be <= end_date")

            self.month = None
            self.year = None

        elif self.type == SummaryType.monthly:
            if not self.month or not self.year:
                raise ValueError("monthly requires month and year")

            self.start_date = None
            self.end_date = None

        elif self.type == SummaryType.yearly:
            if not self.year:
                raise ValueError("yearly requires year")

            self.start_date = None
            self.end_date = None
            self.month = None

        return self


# =========================
# AGGREGATE RESPONSE
# =========================
class SummaryAggregateResponse(BaseModel):
    user_id_line: str

    total_income: Decimal
    total_expense: Decimal
    total_balance: Decimal

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    month: Optional[int] = None
    year: Optional[int] = None

    model_config = {
        "from_attributes": True
    }
