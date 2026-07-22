from fastapi import APIRouter
from app.financial_intelligence.routes.intelligence import router as intelligence_router

router = APIRouter()
router.include_router(intelligence_router)
