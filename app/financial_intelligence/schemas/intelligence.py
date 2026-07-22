from datetime import datetime
from decimal import Decimal
from typing import Optional, List
import uuid
from pydantic import BaseModel, ConfigDict

class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_system: bool
    parent_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MerchantResponse(BaseModel):
    id: uuid.UUID
    canonical_name: str
    aliases: List[str]
    merchant_type: str
    website: Optional[str] = None
    country: str
    preferred_category_id: Optional[uuid.UUID] = None
    average_transaction_amount: Optional[Decimal] = None
    transaction_count: int
    last_seen_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CategoryCorrectionRequest(BaseModel):
    category_id: uuid.UUID
    reason: Optional[str] = None
