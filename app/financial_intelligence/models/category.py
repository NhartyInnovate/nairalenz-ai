from datetime import datetime
import uuid
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Hierarchical Categories support
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Self-referential relationship for parent category
    parent = relationship("Category", remote_side=[id], backref="children")
