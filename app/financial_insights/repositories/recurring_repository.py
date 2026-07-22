from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.financial_insights.models.recurring_payment import RecurringPayment

class RecurringRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_recurring_payment(self, payment: RecurringPayment) -> RecurringPayment:
        query = select(RecurringPayment).where(
            RecurringPayment.user_id == payment.user_id,
            RecurringPayment.merchant == payment.merchant
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.frequency = payment.frequency
            existing.average_amount = payment.average_amount
            existing.next_expected_date = payment.next_expected_date
            existing.confidence = payment.confidence
            existing.last_transaction_ids = payment.last_transaction_ids
            existing.status = payment.status
            self.db.add(existing)
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            self.db.add(payment)
            await self.db.commit()
            await self.db.refresh(payment)
            return payment

    async def list_for_user(self, user_id: uuid.UUID) -> List[RecurringPayment]:
        query = (
            select(RecurringPayment)
            .where(RecurringPayment.user_id == user_id)
            .order_by(RecurringPayment.next_expected_date.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
