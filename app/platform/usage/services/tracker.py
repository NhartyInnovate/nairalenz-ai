from abc import ABC, abstractmethod
import logging
from typing import Any, Dict
import uuid

logger = logging.getLogger("usage_tracker")

class BaseUsageTracker(ABC):
    @abstractmethod
    def increment_counter(self, user_id: uuid.UUID, metric: str, amount: int = 1) -> None:
        """
        Increment a monotonic counter (e.g. API requests, statement count, token counts).
        """
        pass

    @abstractmethod
    def set_gauge(self, user_id: uuid.UUID, metric: str, value: Any) -> None:
        """
        Set a variable gauge (e.g. total storage space, peak storage, active connections).
        """
        pass

    # --- Domain-Specific Helper Wrappers ---
    
    def track_uploaded_statement(self, user_id: uuid.UUID, size_bytes: int, file_type: str) -> None:
        self.increment_counter(user_id, "statements_uploaded", 1)
        self.increment_counter(user_id, "storage_uploaded_bytes", size_bytes)

    def track_transactions(self, user_id: uuid.UUID, count: int, categorized: int) -> None:
        self.increment_counter(user_id, "transactions_extracted", count)
        self.increment_counter(user_id, "transactions_categorized", categorized)

    def track_ai_tokens(self, user_id: uuid.UUID, prompt_tokens: int, completion_tokens: int) -> None:
        self.increment_counter(user_id, "ai_prompt_tokens", prompt_tokens)
        self.increment_counter(user_id, "ai_completion_tokens", completion_tokens)
        self.increment_counter(user_id, "ai_requests", 1)

    def track_chat_message(self, user_id: uuid.UUID) -> None:
        self.increment_counter(user_id, "chat_messages", 1)
        self.increment_counter(user_id, "ai_conversations", 1)

    def track_api_request(self, user_id: uuid.UUID, endpoint: str) -> None:
        self.increment_counter(user_id, f"api_requests:{endpoint}", 1)

    def track_storage_status(self, user_id: uuid.UUID, current_storage: int, peak_storage: int) -> None:
        self.set_gauge(user_id, "current_storage_bytes", current_storage)
        self.set_gauge(user_id, "peak_storage_bytes", peak_storage)

    def track_user_activity(self, user_id: uuid.UUID, login_count: int) -> None:
        self.increment_counter(user_id, "login_count", login_count)


class LoggerUsageTracker(BaseUsageTracker):
    """
    Default structured logging implementation of BaseUsageTracker.
    Feeds analytical logs to tracking infrastructure.
    """
    def increment_counter(self, user_id: uuid.UUID, metric: str, amount: int = 1) -> None:
        logger.info(
            f"[USAGE_COUNTER] User: {user_id} | Metric: {metric} | Increment: {amount}",
            extra={
                "tracker_event": "counter",
                "user_id": str(user_id),
                "metric": metric,
                "amount": amount
            }
        )

    def set_gauge(self, user_id: uuid.UUID, metric: str, value: Any) -> None:
        logger.info(
            f"[USAGE_GAUGE] User: {user_id} | Metric: {metric} | Value: {value}",
            extra={
                "tracker_event": "gauge",
                "user_id": str(user_id),
                "metric": metric,
                "value": value
            }
        )

# Global default tracker
usage_tracker = LoggerUsageTracker()
