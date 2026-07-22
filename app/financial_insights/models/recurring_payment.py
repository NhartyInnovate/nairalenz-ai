from datetime import datetime, date
from decimal import Decimal
import uuid
from typing import Optional, List
from sqlalchemy import String, Date, DateTime, Numeric, Float, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class RecurringPayment(Base):
    __tablename__ = "recurring_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    merchant: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(50), default="MONTHLY", nullable=False) # "WEEKLY", "MONTHLY", "DAILY"
    average_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    next_expected_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    
    # State lifecycle
    status: Mapped[str] = mapped_column(String(30), default="DETECTED", nullable=False) # "DETECTED", "CONFIRMED", "CANCELLED", "INACTIVE"
    
    # List of transaction UUIDs forming the recurring pattern
    last_transaction_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
