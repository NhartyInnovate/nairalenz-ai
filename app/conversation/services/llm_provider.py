from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any

class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        chat_history: List[dict]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a text response given a system prompt, user query, and conversation message history.
        Returns:
            Tuple[response_text, metadata]
            where metadata contains: {"model_used": str, "token_usage": dict, "latency_ms": int}
        """
        pass
