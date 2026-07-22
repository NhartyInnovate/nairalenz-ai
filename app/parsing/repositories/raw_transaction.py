from typing import List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.parsing.models.raw_transaction import RawTransaction

class RawTransactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_raw_transactions(self, raw_transactions: List[RawTransaction]) -> List[RawTransaction]:
        """
        Persist a list of raw transaction mappings.
        """
        self.db.add_all(raw_transactions)
        await self.db.commit()
        return raw_transactions

    async def list_statement_raw_transactions(self, statement_id: uuid.UUID) -> List[RawTransaction]:
        """
        List all raw transactions for a statement.
        """
        query = select(RawTransaction).where(RawTransaction.statement_id == statement_id).order_by(RawTransaction.row_index.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
