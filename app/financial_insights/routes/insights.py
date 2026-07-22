from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.identity.models.user import User
from app.identity.routes.auth import get_current_active_user
from app.financial_data.schemas.statement import APIResponseEnvelope
from app.financial_insights.repositories import InsightRepository, SnapshotRepository, RecurringRepository
from app.financial_insights.schemas.insights import InsightResponse, SnapshotResponse, RecurringPaymentResponse

router = APIRouter()

@router.get(
    "/insights",
    response_model=APIResponseEnvelope[List[InsightResponse]],
    summary="List active financial insights",
    description="Retrieve all active system-generated spending trends, anomalies, and financial alerts."
)
async def list_user_insights(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    repo = InsightRepository(db)
    insights = await repo.list_active_for_user(current_user.id)
    return {
        "success": True,
        "message": "Active insights retrieved successfully.",
        "data": insights
    }

@router.get(
    "/financial-health",
    response_model=APIResponseEnvelope[SnapshotResponse],
    summary="Get financial health snapshot",
    description="Retrieve the latest monthly financial health summary snapshot score and component breakdowns."
)
async def get_financial_health_snapshot(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    repo = SnapshotRepository(db)
    snapshot = await repo.get_latest_for_user(current_user.id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_444_NOT_RESPONSE_YET if hasattr(status, "HTTP_444_NOT_RESPONSE_YET") else 404,
            detail="No financial health snapshot found for this user."
        )
    return {
        "success": True,
        "message": "Financial health snapshot retrieved successfully.",
        "data": snapshot
    }

@router.get(
    "/recurring-payments",
    response_model=APIResponseEnvelope[List[RecurringPaymentResponse]],
    summary="List detected recurring payments",
    description="Retrieve list of all active recurring subscription payments (e.g., Netflix, DSTV, Rent)."
)
async def list_recurring_payments(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    repo = RecurringRepository(db)
    payments = await repo.list_for_user(current_user.id)
    return {
        "success": True,
        "message": "Recurring payments retrieved successfully.",
        "data": payments
    }
