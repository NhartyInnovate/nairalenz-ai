from datetime import datetime, date
from decimal import Decimal
import uuid
from typing import Optional
from sqlalchemy import String, Date, DateTime, Numeric, Integer, Float, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class FinancialHealthSnapshot(Base):
    __tablename__ = "financial_health_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    total_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    total_expenses: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    net_cash_flow: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    
    savings_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    essential_expenses: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    discretionary_expenses: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    
    largest_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    largest_merchant: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    financial_health_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    
    # Store component breakdown scores (savings, consistency, concentration, etc.)
    component_scores: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
