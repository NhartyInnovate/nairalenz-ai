from datetime import date, datetime
from typing import Optional, Generic, TypeVar
import uuid
from pydantic import BaseModel, ConfigDict
from app.financial_data.models.statement import UploadStatus

T = TypeVar("T")

class StatementResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    bank_name: str
    account_name: str
    account_number: Optional[str] = None
    statement_period_start: date
    statement_period_end: date
    original_filename: str
    stored_filename: str
    file_size: int
    mime_type: str
    checksum: str
    upload_status: UploadStatus
    uploaded_at: datetime
    
    # Parsing metadata
    parser_version: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    parsing_duration_ms: Optional[int] = None
    parser_errors: Optional[str] = None
    warnings_count: Optional[int] = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class APIResponseEnvelope(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T
