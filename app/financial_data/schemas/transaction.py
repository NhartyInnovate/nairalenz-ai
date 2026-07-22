from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict

class TransactionResponse(BaseModel):
    id: uuid.UUID
    statement_id: uuid.UUID
    transaction_date: date
    description: str
    amount: Decimal
    transaction_type: str
    currency: str
    balance: Optional[Decimal] = None
    reference: Optional[str] = None
    merchant_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    confidence: float
    fingerprint: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
