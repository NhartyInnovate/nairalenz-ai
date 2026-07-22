from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.financial_insights.models.insight import Insight

class InsightRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_insight(self, insight: Insight) -> Insight:
        """
        Create a new insight, or update an existing one if the fingerprint matches.
        """
        query = select(Insight).where(Insight.fingerprint == insight.fingerprint)
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.title = insight.title
            existing.description = insight.description
            existing.severity = insight.severity
            existing.confidence = insight.confidence
            existing.provenance = insight.provenance
            existing.status = "ACTIVE"
            existing.expires_at = insight.expires_at
            self.db.add(existing)
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            self.db.add(insight)
            await self.db.commit()
            await self.db.refresh(insight)
            return insight

    async def list_active_for_user(self, user_id: uuid.UUID) -> List[Insight]:
        query = (
            select(Insight)
            .where(
                Insight.user_id == user_id,
                Insight.status == "ACTIVE"
            )
            .order_by(Insight.generated_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
