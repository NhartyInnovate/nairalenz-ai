from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
import hashlib
import logging
from typing import List, Optional, Dict
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.financial_data.models.transaction import Transaction
from app.financial_data.repositories.transaction import TransactionRepository
from app.financial_intelligence.models.category import Category
from app.financial_intelligence.repositories.category import CategoryRepository
from app.financial_insights.models.financial_health_snapshot import FinancialHealthSnapshot
from app.financial_insights.models.insight import Insight
from app.financial_insights.models.recurring_payment import RecurringPayment
from app.financial_insights.repositories import SnapshotRepository, InsightRepository, RecurringRepository

from app.financial_insights.services.metrics_engine import MetricsEngine
from app.financial_insights.services.trend_engine import TrendEngine
from app.financial_insights.services.recurring_detector import RecurringDetector
from app.financial_insights.services.anomaly_detector import AnomalyDetector
from app.financial_insights.services.health_scorer import HealthScorer

from app.platform.events import (
    event_publisher,
    FinancialHealthUpdated,
    InsightGenerated,
    RecurringPaymentDetected,
    AnomalyDetected,
    SalaryDetected
)

logger = logging.getLogger("insights_service")

class FinancialInsightsService:
    def __init__(
        self,
        db: AsyncSession,
        snapshot_repo: Optional[SnapshotRepository] = None,
        insight_repo: Optional[InsightRepository] = None,
        recurring_repo: Optional[RecurringRepository] = None,
        tx_repo: Optional[TransactionRepository] = None,
        category_repo: Optional[CategoryRepository] = None
    ):
        self.db = db
        self.snapshot_repo = snapshot_repo or SnapshotRepository(db)
        self.insight_repo = insight_repo or InsightRepository(db)
        self.recurring_repo = recurring_repo or RecurringRepository(db)
        self.tx_repo = tx_repo or TransactionRepository(db)
        self.category_repo = category_repo or CategoryRepository(db)

        self.metrics_engine = MetricsEngine()
        self.trend_engine = TrendEngine()
        self.recurring_detector = RecurringDetector()
        self.anomaly_detector = AnomalyDetector()
        self.health_scorer = HealthScorer()

    async def compute_user_insights(self, user_id: uuid.UUID) -> None:
        """
        Run the complete financial insights engine pipeline for a user.
        Generates snapshots, active subscription lists, MoM trends, and anomaly indicators.
        """
        logger.info(f"Running financial insights pipeline for user {user_id}...")
        
        # 1. Load user transactions and categories maps
        transactions = await self.tx_repo.list_user_transactions(user_id)
        if not transactions:
            logger.info("No transaction data available. Insights computation aborted.")
            return

        categories = await self.category_repo.list_categories()
        categories_map = {c.id: c.name for c in categories}

        # 2. Divide transactions chronologically into current vs previous month
        # Use simple date limits (e.g. today is 2026-07-22, current period = July, previous = June)
        today = date.today()
        current_month_start = date(today.year, today.month, 1)
        
        # Calculate previous month boundaries
        if today.month == 1:
            prev_month_start = date(today.year - 1, 12, 1)
            prev_month_end = date(today.year - 1, 12, 31)
        else:
            prev_month_start = date(today.year, today.month - 1, 1)
            # End is current start minus 1 day
            prev_month_end = current_month_start - timedelta(days=1)

        current_txs = [t for t in transactions if t.transaction_date >= current_month_start]
        previous_txs = [t for t in transactions if prev_month_start <= t.transaction_date <= prev_month_end]

        # 3. Calculate current month Metrics and Score
        (
            inc, exp, cash_flow, savings_rate, essential, discretionary,
            largest_cat, largest_merchant
        ) = self.metrics_engine.calculate_metrics(current_txs, categories_map)

        score, component_scores = self.health_scorer.calculate_health_score(
            inc, exp, savings_rate, essential, discretionary
        )

        # 4. Save FinancialHealthSnapshot
        snapshot = FinancialHealthSnapshot(
            id=uuid.uuid4(),
            user_id=user_id,
            period_start=current_month_start,
            period_end=today,
            total_income=inc,
            total_expenses=exp,
            net_cash_flow=cash_flow,
            savings_rate=savings_rate,
            essential_expenses=essential,
            discretionary_expenses=discretionary,
            largest_category=largest_cat,
            largest_merchant=largest_merchant,
            financial_health_score=score,
            score_version="1.0",
            component_scores=component_scores
        )
        await self.snapshot_repo.create_snapshot(snapshot)

        # Emit FinancialHealthUpdated
        await event_publisher.publish(
            FinancialHealthUpdated(
                user_id=user_id,
                score=score,
                snapshot_id=snapshot.id
            )
        )

        # 5. Detect Trends & Create Insights
        trends = self.trend_engine.calculate_trends(current_txs, previous_txs, categories_map)
        comparison_period = f"{prev_month_start.strftime('%B')} vs {current_month_start.strftime('%B')}"

        for trend in trends:
            category = trend["category"]
            delta_pct = trend["delta_percent"]
            
            # We flag trends exceeding +/- 10%
            if abs(delta_pct) >= 10.0:
                direction = "increased" if delta_pct > 0 else "decreased"
                title = f"{category} spending {direction}"
                description = f"Your spending in {category} {direction} by {abs(delta_pct)}% from {trend['previous']} to {trend['current']} this month."
                
                # Fingerprint deduplication key
                fingerprint_str = f"{user_id}:SPENDING_TREND:{comparison_period}:{category}"
                fingerprint = hashlib.sha256(fingerprint_str.encode("utf-8")).hexdigest()

                insight = Insight(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    title=title,
                    description=description,
                    insight_type="SPENDING_TREND",
                    severity="INFO",
                    confidence=0.98,
                    provenance={
                        "engine": "TrendEngine",
                        "engine_version": "1.0.0",
                        "based_on": [t.description for t in current_txs if categories_map.get(t.category_id) == category],
                        "metrics": trend
                    },
                    fingerprint=fingerprint,
                    status="ACTIVE",
                    expires_at=datetime.now(timezone.utc) + timedelta(days=30)
                )
                
                saved_insight = await self.insight_repo.upsert_insight(insight)
                await event_publisher.publish(
                    InsightGenerated(
                        user_id=user_id,
                        insight_id=saved_insight.id,
                        insight_type="SPENDING_TREND"
                    )
                )

        # 6. Detect Recurring Payments
        recurring = self.recurring_detector.detect_recurring(transactions)
        for rec in recurring:
            payment = RecurringPayment(
                id=uuid.uuid4(),
                user_id=user_id,
                merchant=rec["merchant"],
                frequency=rec["frequency"],
                average_amount=rec["average_amount"],
                next_expected_date=rec["next_expected_date"],
                confidence=rec["confidence"],
                status="DETECTED",
                last_transaction_ids=rec["last_transaction_ids"]
            )
            saved_rec = await self.recurring_repo.upsert_recurring_payment(payment)
            await event_publisher.publish(
                RecurringPaymentDetected(
                    user_id=user_id,
                    recurring_payment_id=saved_rec.id,
                    merchant=saved_rec.merchant
                )
            )

        # 7. Detect Anomalies
        anomalies = self.anomaly_detector.detect_anomalies(current_txs, previous_txs, categories_map)
        for anom in anomalies:
            fingerprint_str = f"{user_id}:ANOMALY:{anom['anomaly_type']}:{anom['transaction_id']}"
            fingerprint = hashlib.sha256(fingerprint_str.encode("utf-8")).hexdigest()
            
            insight = Insight(
                id=uuid.uuid4(),
                user_id=user_id,
                title=anom["title"],
                description=anom["description"],
                insight_type="ANOMALY",
                severity=anom["severity"],
                confidence=anom["confidence"],
                provenance=anom["provenance"],
                fingerprint=fingerprint,
                status="ACTIVE",
                expires_at=datetime.now(timezone.utc) + timedelta(days=14)
            )
            saved_insight = await self.insight_repo.upsert_insight(insight)
            
            await event_publisher.publish(
                InsightGenerated(
                    user_id=user_id,
                    insight_id=saved_insight.id,
                    insight_type="ANOMALY"
                )
            )
            await event_publisher.publish(
                AnomalyDetected(
                    user_id=user_id,
                    transaction_id=anom["transaction_id"],
                    anomaly_type=anom["anomaly_type"]
                )
            )

        # 8. Salary Payday checks
        salary_cat = await self.category_repo.get_by_name("Salary")
        if salary_cat:
            salary_txs = [t for t in transactions if t.transaction_type == "CREDIT" and t.category_id == salary_cat.id]
            if salary_txs:
                last_salary = max(salary_txs, key=lambda x: x.transaction_date)
                await event_publisher.publish(
                    SalaryDetected(
                        user_id=user_id,
                        amount=float(last_salary.amount),
                        payday=last_salary.transaction_date
                    )
                )

        await self.db.commit()
