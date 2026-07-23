from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.conversation.models.conversation import Conversation
from app.conversation.models.message import Message

class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(self, user_id: uuid.UUID, title: str) -> Conversation:
        conversation = Conversation(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    async def get_conversation(self, conversation_id: uuid.UUID) -> Optional[Conversation]:
        query = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_user_conversations(self, user_id: uuid.UUID) -> List[Conversation]:
        query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_message(
        self,
        conversation_id: uuid.UUID,
        sender: str,
        content: str,
        model_used: Optional[str] = None,
        token_usage: Optional[dict] = None,
        latency_ms: Optional[int] = None,
        prompt_version: Optional[str] = None
    ) -> Message:
        message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            sender=sender,
            content=content,
            model_used=model_used,
            token_usage=token_usage,
            latency_ms=latency_ms,
            prompt_version=prompt_version,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def get_conversation_messages(self, conversation_id: uuid.UUID, limit: int = 10) -> List[Message]:
        """
        Fetch the most recent 'limit' messages for a conversation, ordered chronologically.
        """
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        recent_messages = list(result.scalars().all())
        # Reverse to restore chronological order (older messages first)
        recent_messages.reverse()
        return recent_messages
