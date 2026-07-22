from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.financial_intelligence.models.rule import CategorizationRule

class RuleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_rule(self, rule: CategorizationRule) -> CategorizationRule:
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def get_by_pattern(self, pattern: str) -> Optional[CategorizationRule]:
        query = select(CategorizationRule).where(CategorizationRule.pattern == pattern)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_rules(self) -> List[CategorizationRule]:
        # Ordered by priority descending so high-priority rules are matched first
        query = select(CategorizationRule).order_by(CategorizationRule.priority.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
