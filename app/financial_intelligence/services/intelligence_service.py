from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.financial_data.models.transaction import Transaction
from app.financial_data.repositories.transaction import TransactionRepository
from app.financial_intelligence.models.category import Category
from app.financial_intelligence.models.merchant import Merchant
from app.financial_intelligence.models.rule import CategorizationRule
from app.financial_intelligence.models.history import CategorizationHistory
from app.financial_intelligence.repositories.category import CategoryRepository
from app.financial_intelligence.repositories.merchant import MerchantRepository
from app.financial_intelligence.repositories.rule import RuleRepository
from app.financial_intelligence.repositories.history import HistoryRepository
from app.financial_intelligence.services.merchant_resolver import MerchantResolver
from app.financial_intelligence.services.rule_engine import RuleEngine
from app.platform.events import (
    event_publisher,
    TransactionNeedsCategorization,
    TransactionCategorized,
    MerchantResolved,
    CategoryCorrected
)

logger = logging.getLogger("intelligence_service")

class FinancialIntelligenceService:
    def __init__(
        self,
        db: AsyncSession,
        category_repo: Optional[CategoryRepository] = None,
        merchant_repo: Optional[MerchantRepository] = None,
        rule_repo: Optional[RuleRepository] = None,
        history_repo: Optional[HistoryRepository] = None,
        tx_repo: Optional[TransactionRepository] = None,
        merchant_resolver: Optional[MerchantResolver] = None,
        rule_engine: Optional[RuleEngine] = None
    ):
        self.db = db
        self.category_repo = category_repo or CategoryRepository(db)
        self.merchant_repo = merchant_repo or MerchantRepository(db)
        self.rule_repo = rule_repo or RuleRepository(db)
        self.history_repo = history_repo or HistoryRepository(db)
        self.tx_repo = tx_repo or TransactionRepository(db)
        self.merchant_resolver = merchant_resolver or MerchantResolver()
        self.rule_engine = rule_engine or RuleEngine()

    async def categorize_statement_transactions(self, statement_id: uuid.UUID) -> None:
        """
        Fetch and run the intelligence pipeline on all normalized transactions matching a statement.
        """
        transactions = await self.tx_repo.list_statement_transactions(statement_id)
        if not transactions:
            logger.info(f"No transactions found for statement {statement_id} to categorize.")
            return

        # Pre-load merchants and rules lists to prevent excessive queries inside loop
        merchants = await self.merchant_repo.list_merchants()
        rules = await self.rule_repo.list_rules()
        uncategorized_node = await self.category_repo.get_by_name("Uncategorized")
        uncategorized_id = uncategorized_node.id if uncategorized_node else None

        for tx in transactions:
            await self._categorize_single_transaction(tx, merchants, rules, uncategorized_id)

        await self.db.commit()

    async def correct_transaction_category(
        self,
        transaction_id: uuid.UUID,
        new_category_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> Transaction:
        """
        Handle manual user category overrides, logging corrections inside audit trails.
        """
        # Fetch transaction
        tx = await self.tx_repo.db.get(Transaction, transaction_id)
        if not tx:
            raise ValueError("Transaction not found")

        previous_category_id = tx.category_id
        previous_confidence = tx.confidence

        # Update transaction
        tx.category_id = new_category_id
        tx.confidence = 1.0  # User corrections always carry absolute confidence
        
        # Save to database
        self.db.add(tx)
        
        # Log correction to Audit History
        history = CategorizationHistory(
            id=uuid.uuid4(),
            transaction_id=transaction_id,
            original_category_id=previous_category_id,
            suggested_category_id=previous_category_id,
            final_category_id=new_category_id,
            confidence=1.0,
            source="USER",
            confidence_reasons=["user correction override"],
            correction_timestamp=datetime.now(timezone.utc),
            previous_confidence=previous_confidence,
            correction_reason=reason
        )
        await self.history_repo.create_history(history)
        await self.db.commit()
        await self.db.refresh(tx)

        # Emit corrected event
        await event_publisher.publish(
            CategoryCorrected(
                transaction_id=transaction_id,
                original_category_id=previous_category_id,
                corrected_category_id=new_category_id,
                user_id=uuid.uuid4()  # Mock user id context boundary
            )
        )

        return tx

    async def _categorize_single_transaction(
        self,
        tx: Transaction,
        merchants: List[Merchant],
        rules: List[CategorizationRule],
        uncategorized_id: Optional[uuid.UUID]
    ) -> None:
        """
        Private logic resolving merchant, rule, and confidence boundaries for a single transaction.
        """
        matched_merchant = None
        category_id = None
        confidence = 0.40
        reasons = ["unresolved category fallback"]
        source = "RULE"

        # 1. Merchant Resolution
        merchant, merchant_conf, merchant_reasons = self.merchant_resolver.resolve_merchant(
            tx.description, merchants
        )
        if merchant:
            matched_merchant = merchant
            tx.merchant_id = merchant.id
            reasons.extend(merchant_reasons)
            
            # Emit MerchantResolved event
            await event_publisher.publish(
                MerchantResolved(
                    transaction_id=tx.id,
                    merchant_id=merchant.id,
                    matched_alias=normalize_description_alias(tx.description)
                )
            )

            # Update merchant statistics dynamically (CTO Requirement 2)
            merchant.transaction_count += 1
            merchant.last_seen_at = datetime.now(timezone.utc)
            if merchant.average_transaction_amount:
                # Running average calculation
                merchant.average_transaction_amount = (
                    (merchant.average_transaction_amount * (merchant.transaction_count - 1)) + Decimal(abs(tx.amount))
                ) / merchant.transaction_count
            else:
                merchant.average_transaction_amount = Decimal(abs(tx.amount))

            if merchant.preferred_category_id:
                category_id = merchant.preferred_category_id
                confidence = merchant_conf
                reasons.append("resolved via merchant preferred category mappings")

        # 2. Rule Evaluation (if merchant doesn't lock in a preferred category)
        if not category_id:
            rule_cat_id, rule_conf, matched_rule = self.rule_engine.evaluate_rules(tx.description, rules)
            if rule_cat_id:
                category_id = rule_cat_id
                confidence = rule_conf
                reasons.append(f"matched rule pattern: '{matched_rule.pattern}' (version: {matched_rule.rule_version})")

        # Fallback to Uncategorized if unresolved
        if not category_id:
            category_id = uncategorized_id

        # 3. Confidence Threshold check (0.80)
        if confidence < 0.80:
            # Low confidence -> Publish transaction categorizations event for future AI loop
            tx.category_id = uncategorized_id
            tx.confidence = confidence
            source = "AI" # flagged to AI for classification loop
            
            # Publish event with rich context (CTO Requirement 7)
            await event_publisher.publish(
                TransactionNeedsCategorization(
                    transaction_id=tx.id,
                    user_id=uuid.uuid4(),  # Mock system context user
                    description=tx.description,
                    amount=float(tx.amount),
                    transaction_date=tx.transaction_date,
                    balance=float(tx.balance) if tx.balance is not None else None,
                    partially_resolved_merchant_id=matched_merchant.id if matched_merchant else None,
                    parser_confidence=tx.confidence,
                    normalization_confidence=confidence
                )
            )
        else:
            tx.category_id = category_id
            tx.confidence = confidence
            
            # Publish transaction categorized event
            await event_publisher.publish(
                TransactionCategorized(
                    transaction_id=tx.id,
                    category_id=category_id,
                    merchant_id=matched_merchant.id if matched_merchant else None,
                    confidence=confidence,
                    source=source
                )
            )

        # 4. Save history audit entry (CTO Requirement 4)
        history = CategorizationHistory(
            id=uuid.uuid4(),
            transaction_id=tx.id,
            original_category_id=None,
            suggested_category_id=category_id,
            final_category_id=tx.category_id,
            confidence=confidence,
            source=source,
            confidence_reasons=reasons
        )
        await self.history_repo.create_history(history)
        self.db.add(tx)

def normalize_description_alias(desc: str) -> str:
    """Helper resolution mapping alias details."""
    from app.financial_intelligence.utils.normalizer import normalize_description
    return normalize_description(desc)
