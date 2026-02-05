from sqlalchemy import Column, BigInteger, DateTime, ForeignKey, func
from app.config.database import Base


class TransactionTag(Base):
    __tablename__ = "transaction_tags"

    transaction_id = Column(BigInteger, ForeignKey(
        "transactions.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(BigInteger, ForeignKey(
        "tags.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)
