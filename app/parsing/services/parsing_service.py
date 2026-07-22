from datetime import datetime, timezone
import logging
import time
import uuid
from typing import List, Optional
from app.core.config import settings
from app.platform.storage import BaseStorage, LocalStorage
from app.platform.events import event_publisher, TransactionsNormalized
from app.financial_data.models.statement import UploadStatus, Statement
from app.financial_data.repositories.statement import StatementRepository
from app.financial_data.repositories.transaction import TransactionRepository
from app.parsing.models.raw_transaction import RawTransaction
from app.parsing.repositories.raw_transaction import RawTransactionRepository
from app.parsing.services.bank_detector import BankDetector, BankType
from app.parsing.services.parsers import parser_registry
from app.parsing.services.normalizer import NormalizerService

logger = logging.getLogger("parsing_service")

class ParsingService:
    def __init__(
        self,
        statement_repo: StatementRepository,
        raw_tx_repo: RawTransactionRepository,
        tx_repo: TransactionRepository,
        storage: Optional[BaseStorage] = None,
        bank_detector: Optional[BankDetector] = None,
        normalizer: Optional[NormalizerService] = None
    ):
        self.statement_repo = statement_repo
        self.raw_tx_repo = raw_tx_repo
        self.tx_repo = tx_repo
        self.storage = storage or LocalStorage()
        self.bank_detector = bank_detector or BankDetector()
        self.normalizer = normalizer or NormalizerService()

    async def parse_and_normalize_statement(self, statement_id: uuid.UUID) -> None:
        """
        Coordinates the entire data parsing, raw persistence, and normalization mapping loop.
        """
        statement = await self.statement_repo.get_statement_by_id(statement_id)
        if not statement:
            logger.error(f"Statement {statement_id} not found in database. Aborting parsing.")
            return

        # 1. Update status to QUEUED -> PARSING
        statement.upload_status = UploadStatus.PARSING
        statement.processing_started_at = datetime.now(timezone.utc)
        await self.statement_repo.update_statement(statement)

        start_time_ns = time.perf_counter_ns()
        raw_rows = []
        parser_name = "UnknownParser"
        parser_version = "1.0"
        
        try:
            # 2. Retrieve file bytes from storage
            # Resolve stored relative path
            # Wait, our LocalStorage.resolve_path takes care of turning this into absolute path.
            # Let's read the bytes synchronously in executor or directly using Python open if needed.
            # Since our storage service has resolve_path, we can just read using resolved path:
            abs_path = self.storage.resolve_path(statement.stored_filename)
            with open(abs_path, "rb") as f:
                file_bytes = f.read()

            # 3. Bank Detection
            bank_type = self.bank_detector.detect_bank(file_bytes, statement.original_filename)
            
            # Determine file format (PDF / CSV)
            file_ext = "PDF" if statement.original_filename.lower().endswith(".pdf") else "CSV"

            # 4. Resolve parser strategy
            parser = parser_registry.get_parser(file_ext, bank_type)
            parser_name = parser.name
            parser_version = parser.version
            statement.parser_version = parser_version

            # 5. Extract raw records
            raw_rows = await parser.parse(file_bytes)

            # Transition to NORMALIZING
            statement.upload_status = UploadStatus.NORMALIZING
            await self.statement_repo.update_statement(statement)

        except Exception as e:
            logger.error(f"Parser error for statement {statement_id}: {e}", exc_info=True)
            end_time_ns = time.perf_counter_ns()
            statement.upload_status = UploadStatus.FAILED
            statement.parser_errors = str(e)
            statement.processing_completed_at = datetime.now(timezone.utc)
            statement.parsing_duration_ms = (end_time_ns - start_time_ns) // 1_000_000
            await self.statement_repo.update_statement(statement)
            return

        # 6. Normalize and save records
        warnings_count = 0
        raw_db_records = []
        normalized_tx_records = []
        fingerprints_seen = set()

        for idx, raw_row in enumerate(raw_rows):
            # Persist raw mapping first
            raw_record = RawTransaction(
                id=uuid.uuid4(),
                statement_id=statement_id,
                row_index=idx,
                raw_data=raw_row,
                confidence_score=1.0,  # Default, gets overwritten by normalizer score
                parser_name=parser_name,
                parser_version=parser_version
            )
            
            # Call normalization strategy
            tx, confidence, warning = self.normalizer.normalize_row(
                raw_row=raw_row,
                statement_id=statement_id,
                default_date=statement.statement_period_start
            )

            raw_record.confidence_score = confidence
            raw_db_records.append(raw_record)

            if tx:
                # Deduplicate matching transaction fingerprints *within* this statement processing run
                if tx.fingerprint in fingerprints_seen:
                    warnings_count += 1
                    logger.warning(f"Internal duplicate row detected at index {idx} in statement {statement_id}")
                    continue
                fingerprints_seen.add(tx.fingerprint)
                
                if warning:
                    warnings_count += 1
                    logger.warning(f"Normalization warning for row {idx}: {warning}")

                # Set dynamic confidence score
                tx.confidence = confidence
                normalized_tx_records.append(tx)
            else:
                warnings_count += 1

        # Save all Raw & Normalized transactions
        try:
            if raw_db_records:
                await self.raw_tx_repo.create_raw_transactions(raw_db_records)
            if normalized_tx_records:
                await self.tx_repo.create_transactions(normalized_tx_records)
        except Exception as persist_error:
            logger.error(f"Persistence error mapping transaction records: {persist_error}", exc_info=True)
            end_time_ns = time.perf_counter_ns()
            statement.upload_status = UploadStatus.FAILED
            statement.parser_errors = f"Database save error: {str(persist_error)}"
            statement.processing_completed_at = datetime.now(timezone.utc)
            statement.parsing_duration_ms = (end_time_ns - start_time_ns) // 1_000_000
            await self.statement_repo.update_statement(statement)
            return

        # 7. Update status and duration metadata
        end_time_ns = time.perf_counter_ns()
        statement.parsing_duration_ms = (end_time_ns - start_time_ns) // 1_000_000
        statement.warnings_count = warnings_count
        statement.processing_completed_at = datetime.now(timezone.utc)

        if warnings_count > 0:
            statement.upload_status = UploadStatus.COMPLETED_WITH_WARNINGS
        else:
            statement.upload_status = UploadStatus.COMPLETED

        await self.statement_repo.update_statement(statement)

        # 8. Publish decoupling domain event
        await event_publisher.publish(
            TransactionsNormalized(
                statement_id=statement_id,
                user_id=statement.user_id,
                transaction_count=len(normalized_tx_records),
                warnings_count=warnings_count
            )
        )

        logger.info(f"Ingestion successful for statement {statement_id}. Status: {statement.upload_status}")
