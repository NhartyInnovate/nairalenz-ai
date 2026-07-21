from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db

router = APIRouter()

@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Asynchronous health check to verify server running state and database connectivity.
    """
    db_status = "unhealthy"
    try:
        # Perform a quick database execution
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        # You could log the error here
        pass

    return {
        "status": "ok",
        "database": db_status
    }
