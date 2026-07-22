from datetime import datetime
import uuid
from sqlalchemy import String, DateTime, Integer, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class RawTransaction(Base):
    __tablename__ = "raw_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    statement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("statements.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Store dynamic raw row key-values (e.g. Credit, Debit, Date, Balance, Description)
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    confidence_score: Mapped[float] = mapped_column(nullable=False, default=1.0)
    parser_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
