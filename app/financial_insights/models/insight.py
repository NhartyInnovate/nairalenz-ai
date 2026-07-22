from datetime import datetime
import uuid
from typing import Optional
from sqlalchemy import String, DateTime, Text, Float, ForeignKey, Boolean, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. "SPENDING_TREND", "ANOMALY", "RECURRING_PAYMENT"
    severity: Mapped[str] = mapped_column(String(20), default="INFO", nullable=False) # "INFO", "WARNING", "CRITICAL"
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    
    # Traceability & Explainability Provenance (CTO additions)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Deduplication
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    
    # Lifecycle Tracking
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False) # "ACTIVE", "READ", "DISMISSED", "ARCHIVED"
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
