from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.financial_intelligence.models.history import CategorizationHistory

class HistoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_history(self, history: CategorizationHistory) -> CategorizationHistory:
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(history)
        return history

    async def get_latest_for_transaction(self, transaction_id: uuid.UUID) -> Optional[CategorizationHistory]:
        query = select(CategorizationHistory).where(
            CategorizationHistory.transaction_id == transaction_id
        ).order_by(CategorizationHistory.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_history_for_transaction(self, transaction_id: uuid.UUID) -> List[CategorizationHistory]:
        query = select(CategorizationHistory).where(
            CategorizationHistory.transaction_id == transaction_id
        ).order_by(CategorizationHistory.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
