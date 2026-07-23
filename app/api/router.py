from fastapi import APIRouter
from app.identity.routes import router as identity_router
from app.financial_data.routes import router as financial_data_router
from app.financial_intelligence.routes import router as financial_intelligence_router
from app.financial_insights.routes import router as financial_insights_router
from app.conversation.routes import chat_router
from app.platform.routes import router as platform_router

api_router = APIRouter()

# Include routes for all configured domains
api_router.include_router(identity_router, prefix="/auth", tags=["Identity"])
api_router.include_router(financial_data_router)
api_router.include_router(financial_intelligence_router, prefix="", tags=["Financial Intelligence"])
api_router.include_router(financial_insights_router, prefix="", tags=["Financial Insights"])
api_router.include_router(chat_router, prefix="", tags=["Conversation"])
api_router.include_router(platform_router, prefix="/platform", tags=["Platform"])
