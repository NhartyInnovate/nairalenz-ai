from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.financial_insights.models.financial_health_snapshot import FinancialHealthSnapshot

class SnapshotRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_snapshot(self, snapshot: FinancialHealthSnapshot) -> FinancialHealthSnapshot:
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    async def get_latest_for_user(self, user_id: uuid.UUID) -> Optional[FinancialHealthSnapshot]:
        query = (
            select(FinancialHealthSnapshot)
            .where(FinancialHealthSnapshot.user_id == user_id)
            .order_by(
                FinancialHealthSnapshot.period_end.desc(),
                FinancialHealthSnapshot.created_at.desc()
            )
            .execution_options(populate_existing=True)
        )
        result = await self.db.execute(query)
        return result.scalars().first()
