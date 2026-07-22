from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any
import uuid
from pydantic import BaseModel, ConfigDict
from app.financial_insights.schemas.insights import InsightResponse, SnapshotResponse, RecurringPaymentResponse

class TransactionSummary(BaseModel):
    category_name: str
    total_amount: Decimal
    transaction_count: int

    model_config = ConfigDict(from_attributes=True)

class FinancialIntelligenceContext(BaseModel):
    snapshot: Optional[SnapshotResponse] = None
    active_insights: List[InsightResponse] = []
    recurring_payments: List[RecurringPaymentResponse] = []
    recent_transactions_summary: List[TransactionSummary] = []
    
    # Future extensibility blocks
    forecasts: Optional[Dict[str, Any]] = None
    budgets: Optional[Dict[str, Any]] = None
    goals: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
