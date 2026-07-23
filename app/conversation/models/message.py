from datetime import datetime
import uuid
from typing import Optional
from sqlalchemy import String, DateTime, Text, ForeignKey, JSON, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    sender: Mapped[str] = mapped_column(String(10), nullable=False)  # "USER" or "AI"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Prompt Engineering / AI Tracking Metadata
    model_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    token_usage: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"prompt_tokens": X, "completion_tokens": Y}
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
