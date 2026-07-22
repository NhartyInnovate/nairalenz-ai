from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router

from contextlib import asynccontextmanager
from app.platform.workers.parser_worker import init_worker
from app.db.session import async_session_maker
from app.financial_intelligence.utils.seeder import seed_data_if_empty

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register subscribers to platform event bus
    init_worker()
    
    # Auto-seed standard categories, rules, and merchants on startup
    async with async_session_maker() as session:
        await seed_data_if_empty(session)
        
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="NairaLens AI - Financial Intelligence Platform Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Default open CORS for dev environment if not specified
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include core API routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root_redirect():
    """
    Root route welcoming users or developers to the API
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs"
    }
