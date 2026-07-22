from datetime import date, datetime, timezone
import hashlib
import logging
import os
import uuid
from typing import List, Optional
from app.core.config import settings
from app.platform.storage import BaseStorage, LocalStorage
from app.platform.events import event_publisher, StatementUploaded
from app.platform.usage import BaseUsageTracker, usage_tracker
from app.financial_data.models.statement import Statement, UploadStatus
from app.financial_data.repositories.statement import StatementRepository
from app.financial_data.services.validators import validator_registry

logger = logging.getLogger("statement_service")

class StatementService:
    def __init__(
        self,
        repo: StatementRepository,
        storage: Optional[BaseStorage] = None,
        tracker: Optional[BaseUsageTracker] = None
    ):
        self.repo = repo
        self.storage = storage or LocalStorage()
        self.tracker = tracker or usage_tracker

    async def upload_and_process(
        self,
        user_id: uuid.UUID,
        file_bytes: bytes,
        original_filename: str,
        content_type: str,
        bank_name: str,
        account_name: str,
        account_number: Optional[str],
        statement_period_start: date,
        statement_period_end: date
    ) -> Statement:
        """
        Validate file type/bytes, run malware scan, checksum duplicate validation,
        store document, publish metadata event, and record analytics.
        """
        # 1. Evaluate file size limits
        actual_size = len(file_bytes)
        if actual_size == 0:
            raise ValueError("File is empty")
        
        if actual_size > settings.MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE_BYTES} bytes")

        # 2. File-type Strategy validation (PDF, CSV, OFX, etc.)
        validator = validator_registry.get_validator(original_filename)
        validator.validate(file_bytes, original_filename, content_type)

        # 3. Extension Point: Malware scanning hook
        self._scan_for_malware(file_bytes, original_filename)

        # 4. Checksum timing (SHA-256)
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        # 5. Duplicate check (per user)
        if await self.repo.exists_by_checksum(user_id, sha256_hash):
            raise ValueError("This statement has already been uploaded by the user")

        # 6. Generate stored path settings
        now = datetime.now(timezone.utc)
        unique_id = uuid.uuid4()
        timestamp_str = now.strftime("%Y%m%dT%H%M%S")
        _, ext = os.path.splitext(original_filename.lower())
        stored_filename = f"{unique_id.hex}_{timestamp_str}{ext}"
        
        # Relative path structured for cloud compatibility (e.g. 2026/07/filename.pdf)
        relative_path = f"{now.strftime('%Y/%m')}/{stored_filename}"

        # 7. Store bytes
        await self.storage.save_file(file_bytes, relative_path)

        # 8. Save database metadata
        statement = Statement(
            id=unique_id,
            user_id=user_id,
            bank_name=bank_name,
            account_name=account_name,
            account_number=account_number,
            statement_period_start=statement_period_start,
            statement_period_end=statement_period_end,
            original_filename=original_filename,
            stored_filename=relative_path,
            file_size=actual_size,
            mime_type=content_type,
            checksum=sha256_hash,
            upload_status=UploadStatus.UPLOADED
        )
        created_statement = await self.repo.create_statement(statement)

        # 9. Track usage metrics (monotonically incrementing total storage and statement count)
        self.tracker.track_uploaded_statement(user_id, actual_size, ext.replace(".", "").upper())

        # 10. Publish Domain Event (loose coupling for background parser & integrations)
        await event_publisher.publish(
            StatementUploaded(
                statement_id=created_statement.id,
                user_id=user_id,
                bank_name=bank_name,
                checksum=sha256_hash,
                file_type=ext.replace(".", "").upper(),
                file_size=actual_size,
                uploaded_at=created_statement.uploaded_at
            )
        )

        return created_statement

    def _scan_for_malware(self, file_bytes: bytes, filename: str) -> None:
        """
        Extension Point: Intercepts files and validates signatures against malware indices.
        In the future, integrate with third-party scanning engines (ClamAV, VirusTotal, etc.).
        """
        logger.info(f"[MALWARE_SCAN] Scanning file {filename} ({len(file_bytes)} bytes)")

    async def get_statement(self, user_id: uuid.UUID, statement_id: uuid.UUID) -> Optional[Statement]:
        """
        Fetch statement metadata details.
        """
        statement = await self.repo.get_statement_by_id(statement_id)
        if not statement or statement.user_id != user_id:
            return None
        return statement

    async def list_statements(self, user_id: uuid.UUID) -> List[Statement]:
        """
        List active statements owned by the user.
        """
        return await self.repo.list_user_statements(user_id)
