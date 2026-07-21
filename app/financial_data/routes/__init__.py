from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def root():
    return {"message": "Welcome to financial_data API"}
