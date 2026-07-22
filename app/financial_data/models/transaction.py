from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid
from sqlalchemy import String, DateTime, Date, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    statement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("statements.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "DEBIT" or "CREDIT"
    currency: Mapped[str] = mapped_column(String(10), default="NGN", nullable=False)
    balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Placeholders for future enrichment
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="SET NULL"), nullable=True)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    
    confidence: Mapped[float] = mapped_column(nullable=False, default=1.0)
    
    # Hash fingerprint for duplicate detection (date + description + amount + reference)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
