from datetime import datetime, timezone
from typing import Optional
import uuid
from pydantic import BaseModel, Field

class Event(BaseModel):
    """
    Base Event representing a system change or domain event.
    """
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_version: str = "1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_name: str
