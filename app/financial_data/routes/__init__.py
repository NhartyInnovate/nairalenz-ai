from fastapi import APIRouter
from app.financial_data.routes.statement import router as statement_router
from app.financial_data.routes.transaction import router as transaction_router

router = APIRouter()
# Include subrouters
router.include_router(statement_router, prefix="/statements", tags=["Financial Data"])
router.include_router(transaction_router, prefix="/transactions", tags=["Financial Data"])
