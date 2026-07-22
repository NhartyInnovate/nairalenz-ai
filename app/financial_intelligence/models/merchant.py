from datetime import datetime
from decimal import Decimal
import uuid
from typing import Optional, List
from sqlalchemy import String, DateTime, Numeric, Integer, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    aliases: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # Lowercase alias strings list
    merchant_type: Mapped[str] = mapped_column(String(50), default="Retail", nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[str] = mapped_column(String(10), default="NG", nullable=False)
    
    # Statistical intelligence mappings
    preferred_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True
    )
    average_transaction_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    transaction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
