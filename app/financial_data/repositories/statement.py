from typing import List, Optional
import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.financial_data.models.statement import Statement

class StatementRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_statement(self, statement: Statement) -> Statement:
        """
        Persist a new statement metadata record.
        """
        self.db.add(statement)
        await self.db.commit()
        await self.db.refresh(statement)
        return statement

    async def get_statement_by_id(self, statement_id: uuid.UUID) -> Optional[Statement]:
        """
        Retrieve a single statement by ID, excluding soft-deleted ones.
        """
        query = select(Statement).where(
            and_(
                Statement.id == statement_id,
                Statement.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def exists_by_checksum(self, user_id: uuid.UUID, checksum: str) -> bool:
        """
        Verify if this user has already uploaded a statement with this checksum (active statements only).
        """
        query = select(Statement).where(
            and_(
                Statement.user_id == user_id,
                Statement.checksum == checksum,
                Statement.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def list_user_statements(self, user_id: uuid.UUID) -> List[Statement]:
        """
        List all active (non-soft-deleted) statements for a specific user.
        """
        query = select(Statement).where(
            and_(
                Statement.user_id == user_id,
                Statement.deleted_at.is_(None)
            )
        ).order_by(Statement.uploaded_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_statement(self, statement: Statement) -> Statement:
        """
        Commit changes to a statement entity.
        """
        self.db.add(statement)
        await self.db.commit()
        await self.db.refresh(statement)
        return statement
