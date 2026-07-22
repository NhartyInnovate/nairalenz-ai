from typing import List
import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.financial_data.models.transaction import Transaction
from app.financial_data.models.statement import Statement

class TransactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_transactions(self, transactions: List[Transaction]) -> List[Transaction]:
        """
        Bulk persist a list of normalized transactions.
        """
        self.db.add_all(transactions)
        await self.db.commit()
        return transactions

    async def list_statement_transactions(self, statement_id: uuid.UUID) -> List[Transaction]:
        """
        List all transactions matching a specific statement ID.
        """
        query = select(Transaction).where(Transaction.statement_id == statement_id).order_by(Transaction.transaction_date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_user_transactions(self, user_id: uuid.UUID) -> List[Transaction]:
        """
        List all transactions across all statements uploaded by the user.
        """
        query = (
            select(Transaction)
            .join(Statement, Statement.id == Transaction.statement_id)
            .where(
                and_(
                    Statement.user_id == user_id,
                    Statement.deleted_at.is_(None)
                )
            )
            .order_by(Transaction.transaction_date.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def exists_by_fingerprint(self, statement_id: uuid.UUID, fingerprint: str) -> bool:
        """
        Check if a transaction with the same fingerprint already exists in the statement.
        """
        query = select(Transaction).where(
            and_(
                Transaction.statement_id == statement_id,
                Transaction.fingerprint == fingerprint
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
