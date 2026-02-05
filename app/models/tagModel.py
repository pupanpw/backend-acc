from sqlalchemy import Column, BigInteger, Text, DateTime, func, UniqueConstraint, Index
from app.config.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id_line = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    slug = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id_line", "slug", name="uq_tags_user_slug"),
        Index("idx_tags_user", "user_id_line"),
    )
