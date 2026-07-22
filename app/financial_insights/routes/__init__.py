from fastapi import APIRouter
from app.financial_insights.routes.insights import router as insights_router

router = APIRouter()
router.include_router(insights_router)
