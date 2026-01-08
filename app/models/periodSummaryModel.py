from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class PeriodSummary(Base):
    __tablename__ = "period_summary"

    id = Column(Integer, primary_key=True, index=True)

    summary_date = Column(Date, nullable=False, index=True)

    user_id_line = Column(String(255), nullable=False, index=True)

    total_income = Column(Numeric(12, 2), nullable=False, default=0)
    total_expense = Column(Numeric(12, 2), nullable=False, default=0)
    total_balance = Column(Numeric(12, 2), nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )
