from enum import Enum
import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, DateTime, Date, Integer, ForeignKey, Enum as SqlEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class UploadStatus(str, Enum):
    UPLOADED = "UPLOADED"
    QUEUED = "QUEUED"
    PARSING = "PARSING"
    NORMALIZING = "NORMALIZING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"

class Statement(Base):
    __tablename__ = "statements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Financial details
    bank_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    statement_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    statement_period_end: Mapped[date] = mapped_column(Date, nullable=False)

    # Storage details
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    # Lifecycle status
    upload_status: Mapped[UploadStatus] = mapped_column(
        SqlEnum(UploadStatus, name="upload_status_enum"),
        default=UploadStatus.UPLOADED,
        nullable=False
    )
    
    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Future AI parsing integration fields
    parser_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Parsing pipeline metadata
    parsing_duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parser_errors: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    warnings_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
