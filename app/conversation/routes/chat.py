from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.identity.models.user import User
from app.identity.routes.auth import get_current_active_user
from app.financial_data.schemas.statement import APIResponseEnvelope
from app.conversation.services.chat_service import ChatService
from app.conversation.schemas.chat import (
    ChatRequest, ChatResponse, ConversationResponse, ConversationDetailResponse, MessageResponse
)

router = APIRouter()

@router.post(
    "/chat",
    response_model=APIResponseEnvelope[ChatResponse],
    summary="Send a chat message to NairaLens AI",
    description="Allows authenticated users to converse with their financial intelligence companion."
)
async def send_chat_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    chat_service = ChatService(db)
    user_msg, ai_msg = await chat_service.send_chat_message(
        user_id=current_user.id,
        content=payload.content,
        conversation_id=payload.conversation_id
    )
    
    return {
        "success": True,
        "message": "Chat response generated successfully.",
        "data": ChatResponse(
            conversation_id=user_msg.conversation_id,
            user_message=MessageResponse.model_validate(user_msg),
            ai_message=MessageResponse.model_validate(ai_msg)
        )
    }

@router.get(
    "/conversations",
    response_model=APIResponseEnvelope[List[ConversationResponse]],
    summary="List chat conversations",
    description="Retrieve all historical chat sessions for the current authenticated user."
)
async def list_conversations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    chat_service = ChatService(db)
    convos = await chat_service.list_conversations(current_user.id)
    return {
        "success": True,
        "message": "Conversations retrieved successfully.",
        "data": [ConversationResponse.model_validate(c) for c in convos]
    }

@router.get(
    "/conversations/{id}",
    response_model=APIResponseEnvelope[ConversationDetailResponse],
    summary="Get conversation detail with messages",
    description="Retrieve conversation metadata and full message log for a specific session."
)
async def get_conversation(
    id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    chat_service = ChatService(db)
    convo = await chat_service.repo.get_conversation(id)
    if not convo:
        raise HTTPException(
            status_code=status.HTTP_444_NOT_RESPONSE_YET if hasattr(status, "HTTP_444_NOT_RESPONSE_YET") else 404,
            detail="Conversation not found."
        )
    if convo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this conversation."
        )
        
    messages = await chat_service.get_conversation_history(convo.id)
    
    detail = ConversationDetailResponse(
        id=convo.id,
        user_id=convo.user_id,
        title=convo.title,
        created_at=convo.created_at,
        messages=[MessageResponse.model_validate(m) for m in messages]
    )
    
    return {
        "success": True,
        "message": "Conversation log retrieved successfully.",
        "data": detail
    }
