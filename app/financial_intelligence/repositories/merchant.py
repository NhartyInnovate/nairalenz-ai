from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.financial_intelligence.models.merchant import Merchant

class MerchantRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_merchant(self, merchant: Merchant) -> Merchant:
        self.db.add(merchant)
        await self.db.commit()
        await self.db.refresh(merchant)
        return merchant

    async def get_by_name(self, name: str) -> Optional[Merchant]:
        query = select(Merchant).where(Merchant.canonical_name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, merchant_id: uuid.UUID) -> Optional[Merchant]:
        return await self.db.get(Merchant, merchant_id)

    async def list_merchants(self) -> List[Merchant]:
        query = select(Merchant).order_by(Merchant.canonical_name.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_merchant(self, merchant: Merchant) -> Merchant:
        self.db.add(merchant)
        await self.db.commit()
        await self.db.refresh(merchant)
        return merchant
