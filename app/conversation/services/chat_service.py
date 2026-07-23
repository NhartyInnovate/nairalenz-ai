import uuid
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.conversation.repositories.conversation_repository import ConversationRepository
from app.financial_insights.services.query_service import InsightQueryService
from app.conversation.services.prompt_builder import PromptBuilder
from app.conversation.services.gemini_provider import GeminiProvider
from app.conversation.models.conversation import Conversation
from app.conversation.models.message import Message

class ChatService:
    def __init__(
        self,
        db: AsyncSession,
        history_window: int = 10,
        prompt_version: str = "v1.0"
    ):
        self.db = db
        self.history_window = history_window
        self.repo = ConversationRepository(db)
        self.query_service = InsightQueryService(db)
        self.prompt_builder = PromptBuilder(version=prompt_version)
        self.provider = GeminiProvider()

    async def get_or_create_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: Optional[uuid.UUID] = None,
        title: Optional[str] = None
    ) -> Conversation:
        if conversation_id:
            convo = await self.repo.get_conversation(conversation_id)
            if convo:
                return convo
        
        t = title or "New Conversation"
        return await self.repo.create_conversation(user_id, t)

    async def list_conversations(self, user_id: uuid.UUID) -> List[Conversation]:
        return await self.repo.list_user_conversations(user_id)

    async def get_conversation_history(self, conversation_id: uuid.UUID) -> List[Message]:
        return await self.repo.get_conversation_messages(conversation_id, limit=self.history_window)

    async def send_chat_message(
        self,
        user_id: uuid.UUID,
        content: str,
        conversation_id: Optional[uuid.UUID] = None
    ) -> Tuple[Message, Message]:
        """
        Sends a user chat message, gathers financial context, calls the LLM,
        and saves both messages to the database.
        """
        conversation = await self.get_or_create_conversation(user_id, conversation_id)
        
        history_records = await self.get_conversation_history(conversation.id)
        
        financial_context = await self.query_service.get_user_financial_context(user_id)
        
        system_prompt = self.prompt_builder.build_system_prompt(financial_context)
        prompt_ver = self.prompt_builder.get_prompt_version()
        
        history_list = [{"sender": m.sender, "content": m.content} for m in history_records]
        
        user_message_record = await self.repo.create_message(
            conversation_id=conversation.id,
            sender="USER",
            content=content
        )
        
        ai_text, metadata = await self.provider.generate_response(
            system_prompt=system_prompt,
            user_message=content,
            chat_history=history_list
        )
        
        ai_message_record = await self.repo.create_message(
            conversation_id=conversation.id,
            sender="AI",
            content=ai_text,
            model_used=metadata.get("model_used"),
            token_usage=metadata.get("token_usage"),
            latency_ms=metadata.get("latency_ms"),
            prompt_version=prompt_ver
        )
        
        if conversation.title == "New Conversation" and len(content) > 0:
            title_truncated = content[:50] + "..." if len(content) > 50 else content
            conversation.title = title_truncated

        await self.db.commit()
        return user_message_record, ai_message_record
