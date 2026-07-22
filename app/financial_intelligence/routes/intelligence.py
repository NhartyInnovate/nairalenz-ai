from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.identity.models.user import User
from app.identity.routes.auth import get_current_active_user
from app.financial_data.schemas.transaction import TransactionResponse
from app.financial_data.schemas.statement import APIResponseEnvelope
from app.financial_intelligence.repositories import CategoryRepository, MerchantRepository
from app.financial_intelligence.services.intelligence_service import FinancialIntelligenceService
from app.financial_intelligence.schemas.intelligence import CategoryResponse, MerchantResponse, CategoryCorrectionRequest

router = APIRouter()

@router.get(
    "/categories",
    response_model=APIResponseEnvelope[List[CategoryResponse]],
    summary="List transaction categories",
    description="Retrieve all system-defined and custom categories."
)
async def list_categories(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    repo = CategoryRepository(db)
    categories = await repo.list_categories()
    return {
        "success": True,
        "message": "Categories retrieved successfully.",
        "data": categories
    }

@router.get(
    "/merchants",
    response_model=APIResponseEnvelope[List[MerchantResponse]],
    summary="List resolved merchants",
    description="Retrieve list of all active registered merchants and statistical alias counters."
)
async def list_merchants(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    repo = MerchantRepository(db)
    merchants = await repo.list_merchants()
    return {
        "success": True,
        "message": "Merchants retrieved successfully.",
        "data": merchants
    }

@router.patch(
    "/transactions/{transaction_id}/category",
    response_model=APIResponseEnvelope[TransactionResponse],
    summary="Correct transaction category",
    description="Manually update the category of a transaction. Records audit data in categorization history."
)
async def correct_transaction_category(
    transaction_id: uuid.UUID,
    payload: CategoryCorrectionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = FinancialIntelligenceService(db)
    try:
        updated_tx = await service.correct_transaction_category(
            transaction_id=transaction_id,
            new_category_id=payload.category_id,
            reason=payload.reason
        )
        return {
            "success": True,
            "message": "Transaction category updated successfully.",
            "data": updated_tx
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
