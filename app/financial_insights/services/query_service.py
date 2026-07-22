import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from app.financial_data.repositories.transaction import TransactionRepository
from app.financial_intelligence.repositories.category import CategoryRepository
from app.financial_insights.repositories import SnapshotRepository, InsightRepository, RecurringRepository
from app.financial_insights.schemas.query_schemas import FinancialIntelligenceContext, TransactionSummary
from app.financial_insights.schemas.insights import SnapshotResponse, InsightResponse, RecurringPaymentResponse

class InsightQueryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.snapshot_repo = SnapshotRepository(db)
        self.insight_repo = InsightRepository(db)
        self.recurring_repo = RecurringRepository(db)
        self.tx_repo = TransactionRepository(db)
        self.category_repo = CategoryRepository(db)

    async def get_user_financial_context(self, user_id: uuid.UUID) -> FinancialIntelligenceContext:
        """
        Gathers user's financial snapshot, active insights, subscriptions, and transaction summary,
        returning a read-only FinancialIntelligenceContext optimized for Conversational AI consumption.
        """
        # 1. Fetch latest health snapshot
        snapshot_model = await self.snapshot_repo.get_latest_for_user(user_id)
        snapshot = SnapshotResponse.model_validate(snapshot_model) if snapshot_model else None

        # 2. Fetch active insights
        insight_models = await self.insight_repo.list_active_for_user(user_id)
        active_insights = [InsightResponse.model_validate(i) for i in insight_models]

        # 3. Fetch recurring payments
        payment_models = await self.recurring_repo.list_for_user(user_id)
        recurring_payments = [RecurringPaymentResponse.model_validate(p) for p in payment_models]

        # 4. Fetch category translation maps
        categories = await self.category_repo.list_categories()
        categories_map = {c.id: c.name for c in categories}

        # 5. Fetch recent transactions & group by category for prompt summary
        transactions = await self.tx_repo.list_user_transactions(user_id)
        
        # Aggregate spending per category over past 30 days
        category_spending: Dict[str, Dict[str, Any]] = {}
        cutoff_date = date.today() - timedelta(days=30)
        
        for tx in transactions:
            if tx.transaction_date >= cutoff_date:
                cat_name = categories_map.get(tx.category_id, "Uncategorized")
                if cat_name not in category_spending:
                    category_spending[cat_name] = {"total": 0, "count": 0}
                if tx.transaction_type == "DEBIT":
                    category_spending[cat_name]["total"] += abs(tx.amount)
                category_spending[cat_name]["count"] += 1

        recent_summaries = []
        for cat_name, stats in category_spending.items():
            recent_summaries.append(
                TransactionSummary(
                    category_name=cat_name,
                    total_amount=stats["total"],
                    transaction_count=stats["count"]
                )
            )

        return FinancialIntelligenceContext(
            snapshot=snapshot,
            active_insights=active_insights,
            recurring_payments=recurring_payments,
            recent_transactions_summary=recent_summaries
        )
