from datetime import datetime
import uuid
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class CategorizationRule(Base):
    __tablename__ = "categorization_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False
    )
    
    pattern: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False) # e.g. "uber", "dstv"
    priority: Mapped[int] = mapped_column(Integer, default=10, index=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)
    rule_version: Mapped[str] = mapped_column(String(50), default="1.0", nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
