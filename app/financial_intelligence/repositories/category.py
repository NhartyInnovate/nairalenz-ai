from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.financial_intelligence.models.category import Category

class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_category(self, category: Category) -> Category:
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def get_by_name(self, name: str) -> Optional[Category]:
        query = select(Category).where(Category.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, category_id: uuid.UUID) -> Optional[Category]:
        return await self.db.get(Category, category_id)

    async def list_categories(self) -> List[Category]:
        query = select(Category).order_by(Category.name.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
