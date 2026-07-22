from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.identity.models.user import User
from app.identity.routes.auth import get_current_active_user
from app.financial_data.repositories.transaction import TransactionRepository
from app.financial_data.repositories.statement import StatementRepository
from app.financial_data.schemas.transaction import TransactionResponse
from app.financial_data.schemas.statement import APIResponseEnvelope

router = APIRouter()

@router.get(
    "",
    response_model=APIResponseEnvelope[List[TransactionResponse]],
    summary="List user transactions",
    description="Retrieve a list of all normalized transactions across all active statements uploaded by the user."
)
async def list_user_transactions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    repo = TransactionRepository(db)
    transactions = await repo.list_user_transactions(current_user.id)
    return {
        "success": True,
        "message": "User transactions retrieved successfully.",
        "data": transactions
    }

@router.get(
    "/{transaction_id}",
    response_model=APIResponseEnvelope[TransactionResponse],
    summary="Get transaction details",
    description="Retrieve details of a specific transaction owned by the user."
)
async def get_transaction_details(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    tx_repo = TransactionRepository(db)
    statement_repo = StatementRepository(db)
    
    # Load transaction
    from app.financial_data.models.transaction import Transaction
    tx = await db.get(Transaction, transaction_id)
    
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
        
    # Ensure statement belongs to user
    statement = await statement_repo.get_statement_by_id(tx.statement_id)
    if not statement or statement.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
        
    return {
        "success": True,
        "message": "Transaction retrieved successfully.",
        "data": tx
    }
