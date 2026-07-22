from fastapi import APIRouter
from app.financial_data.routes.statement import router as statement_router

router = APIRouter()
# Include the subrouter with prefix /statements to satisfy FastAPI non-empty route constraints
router.include_router(statement_router, prefix="/statements", tags=["Financial Data"])
