import logging
from app.db.session import async_session_maker
from app.platform.events import event_publisher, StatementUploaded, TransactionsNormalized
from app.financial_data.models.statement import UploadStatus
from app.financial_data.repositories.statement import StatementRepository
from app.financial_data.repositories.transaction import TransactionRepository
from app.parsing.repositories.raw_transaction import RawTransactionRepository
from app.parsing.services.parsing_service import ParsingService
from app.financial_intelligence.services.intelligence_service import FinancialIntelligenceService

logger = logging.getLogger("parser_worker")

async def handle_statement_uploaded(event: StatementUploaded) -> None:
    """
    Background subscriber callback. Triggered asynchronously on statement upload event.
    """
    logger.info(f"[WORKER] Triggered background processing loop for Statement {event.statement_id}")
    
    async with async_session_maker() as db_session:
        statement_repo = StatementRepository(db_session)
        
        # 1. Update status: UPLOADED -> QUEUED
        statement = await statement_repo.get_statement_by_id(event.statement_id)
        if not statement:
            logger.error(f"[WORKER] Statement {event.statement_id} not found in database. Aborting.")
            return

        statement.upload_status = UploadStatus.QUEUED
        await statement_repo.update_statement(statement)
        
        # Initialize parsing coordinators
        raw_tx_repo = RawTransactionRepository(db_session)
        tx_repo = TransactionRepository(db_session)
        
        parsing_service = ParsingService(
            statement_repo=statement_repo,
            raw_tx_repo=raw_tx_repo,
            tx_repo=tx_repo
        )
        
        # 2. Run parsing pipeline
        await parsing_service.parse_and_normalize_statement(event.statement_id)

async def handle_transactions_normalized(event: TransactionsNormalized) -> None:
    """
    Background subscriber callback. Triggered when transaction rows have successfully normalized.
    """
    logger.info(f"[WORKER] Triggered categorization loop for Statement {event.statement_id}")
    
    async with async_session_maker() as db_session:
        # 1. Run Intelligence Categorization
        intelligence_service = FinancialIntelligenceService(db_session)
        await intelligence_service.categorize_statement_transactions(event.statement_id)
        
        # 2. Run Financial Insights Pipeline
        from app.financial_insights.services.insights_service import FinancialInsightsService as InsightsService
        insights_service = InsightsService(db_session)
        await insights_service.compute_user_insights(event.user_id)

def init_worker() -> None:
    """
    Register background subscriptions on event bus startup.
    """
    event_publisher.subscribe("StatementUploaded", handle_statement_uploaded)
    event_publisher.subscribe("TransactionsNormalized", handle_transactions_normalized)
    logger.info("[WORKER] Statement processing subscriptions initialized.")
