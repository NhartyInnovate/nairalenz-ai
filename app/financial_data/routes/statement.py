from datetime import date
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.identity.models.user import User
from app.identity.routes.auth import get_current_active_user
from app.financial_data.repositories.statement import StatementRepository
from app.financial_data.repositories.transaction import TransactionRepository
from app.financial_data.services.statement import StatementService
from app.financial_data.schemas import StatementResponse, APIResponseEnvelope, TransactionResponse

router = APIRouter()

async def get_statement_service(db: AsyncSession = Depends(get_db)) -> StatementService:
    """
    Dependency injection provider for StatementService.
    """
    return StatementService(StatementRepository(db))

@router.post(
    "/upload",
    response_model=APIResponseEnvelope[StatementResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload a bank statement",
    description="Securely upload and validate a PDF or CSV bank statement file. Checks for duplicates and saves metadata."
)
async def upload_statement(
    file: UploadFile = File(..., description="The bank statement file (PDF or CSV) to upload"),
    bank_name: str = Form(..., description="Name of the bank"),
    account_name: str = Form(..., description="Name of the account holder"),
    account_number: Optional[str] = Form(None, description="Account number (optional)"),
    statement_period_start: date = Form(..., description="Start date of the statement period (YYYY-MM-DD)"),
    statement_period_end: date = Form(..., description="End date of the statement period (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    service: StatementService = Depends(get_statement_service)
):
    # Read the file contents as bytes to evaluate size and compute checksum
    file_bytes = await file.read()
    
    try:
        statement = await service.upload_and_process(
            user_id=current_user.id,
            file_bytes=file_bytes,
            original_filename=file.filename or "unknown.pdf",
            content_type=file.content_type or "application/pdf",
            bank_name=bank_name,
            account_name=account_name,
            account_number=account_number,
            statement_period_start=statement_period_start,
            statement_period_end=statement_period_end
        )
        return {
            "success": True,
            "message": "Statement uploaded successfully.",
            "data": statement
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "",
    response_model=APIResponseEnvelope[List[StatementResponse]],
    summary="List statements",
    description="List all active statement records uploaded by the currently authenticated user."
)
async def list_statements(
    current_user: User = Depends(get_current_active_user),
    service: StatementService = Depends(get_statement_service)
):
    statements = await service.list_statements(current_user.id)
    return {
        "success": True,
        "message": "Statements retrieved successfully.",
        "data": statements
    }

@router.get(
    "/{statement_id}",
    response_model=APIResponseEnvelope[StatementResponse],
    summary="Get statement metadata",
    description="Retrieve the metadata details of a single statement uploaded by the user."
)
async def get_statement_details(
    statement_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: StatementService = Depends(get_statement_service)
):
    statement = await service.get_statement(current_user.id, statement_id)
    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )
    return {
        "success": True,
        "message": "Statement metadata retrieved successfully.",
        "data": statement
    }

@router.get(
    "/{statement_id}/transactions",
    response_model=APIResponseEnvelope[List[TransactionResponse]],
    summary="Get statement transactions",
    description="Retrieve the normalized list of transactions associated with this statement."
)
async def list_statement_transactions(
    statement_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    service: StatementService = Depends(get_statement_service),
    db: AsyncSession = Depends(get_db)
):
    # Ensure statement belongs to user
    statement = await service.get_statement(current_user.id, statement_id)
    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )
    
    tx_repo = TransactionRepository(db)
    transactions = await tx_repo.list_statement_transactions(statement_id)
    return {
        "success": True,
        "message": "Transactions retrieved successfully.",
        "data": transactions
    }
