from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
import uuid
from pydantic import BaseModel, ConfigDict

class InsightResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str
    insight_type: str
    severity: str
    confidence: float
    provenance: Dict[str, Any]
    status: str
    is_read: bool
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SnapshotResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    period_start: date
    period_end: date
    total_income: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal
    savings_rate: float
    essential_expenses: Decimal
    discretionary_expenses: Decimal
    largest_category: Optional[str] = None
    largest_merchant: Optional[str] = None
    financial_health_score: int
    score_version: str
    component_scores: Dict[str, int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RecurringPaymentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    merchant: str
    frequency: str
    average_amount: Decimal
    next_expected_date: Optional[date] = None
    confidence: float
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
