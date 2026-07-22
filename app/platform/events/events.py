from datetime import datetime, date
from typing import Optional
import uuid
from pydantic import Field
from app.platform.events.base import Event

class StatementUploaded(Event):
    """
    Fired when a user successfully uploads a statement document.
    """
    statement_id: uuid.UUID
    user_id: uuid.UUID
    bank_name: str
    checksum: str
    file_type: str  # "PDF" or "CSV"
    file_size: int
    uploaded_at: datetime
    event_name: str = "StatementUploaded"

class TransactionsNormalized(Event):
    """
    Fired when raw statement lines are successfully normalized.
    """
    statement_id: uuid.UUID
    user_id: uuid.UUID
    transaction_count: int
    warnings_count: int
    event_name: str = "TransactionsNormalized"

class TransactionNeedsCategorization(Event):
    """
    Fired when transaction categorization confidence falls below the accepted threshold.
    """
    transaction_id: uuid.UUID
    user_id: uuid.UUID
    description: str
    amount: float
    transaction_date: date  # date type
    balance: Optional[float] = None
    partially_resolved_merchant_id: Optional[uuid.UUID] = None
    parser_confidence: float
    normalization_confidence: float
    event_name: str = "TransactionNeedsCategorization"

class TransactionCategorized(Event):
    """
    Fired when a transaction is successfully categorized via rule or preferred mapping.
    """
    transaction_id: uuid.UUID
    category_id: uuid.UUID
    merchant_id: Optional[uuid.UUID] = None
    confidence: float
    source: str
    event_name: str = "TransactionCategorized"

class MerchantResolved(Event):
    """
    Fired when description matches canonical names or alias entries.
    """
    transaction_id: uuid.UUID
    merchant_id: uuid.UUID
    matched_alias: str
    event_name: str = "MerchantResolved"

class CategoryCorrected(Event):
    """
    Fired when a user manually overrides transaction category mapping.
    """
    transaction_id: uuid.UUID
    original_category_id: Optional[uuid.UUID] = None
    corrected_category_id: uuid.UUID
    user_id: uuid.UUID
    event_name: str = "CategoryCorrected"

class FinancialHealthUpdated(Event):
    user_id: uuid.UUID
    score: int
    snapshot_id: uuid.UUID
    event_name: str = "FinancialHealthUpdated"

class InsightGenerated(Event):
    user_id: uuid.UUID
    insight_id: uuid.UUID
    insight_type: str
    event_name: str = "InsightGenerated"

class RecurringPaymentDetected(Event):
    user_id: uuid.UUID
    recurring_payment_id: uuid.UUID
    merchant: str
    event_name: str = "RecurringPaymentDetected"

class AnomalyDetected(Event):
    user_id: uuid.UUID
    transaction_id: uuid.UUID
    anomaly_type: str
    event_name: str = "AnomalyDetected"

class SalaryDetected(Event):
    user_id: uuid.UUID
    amount: float
    payday: date
    event_name: str = "SalaryDetected"
