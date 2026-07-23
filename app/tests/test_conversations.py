import pytest
import asyncio
import uuid
from datetime import date
from httpx import AsyncClient
from fastapi import status
from sqlalchemy import select

from app.identity.models.user import User
from app.conversation.models.conversation import Conversation
from app.conversation.models.message import Message
from app.conversation.repositories.conversation_repository import ConversationRepository

pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
async def setup_worker_and_seeder(db_session):
    from app.platform.workers.parser_worker import init_worker
    from app.financial_intelligence.utils.seeder import seed_data_if_empty
    from contextlib import asynccontextmanager
    from unittest.mock import patch
    
    init_worker()
    await seed_data_if_empty(db_session)

    @asynccontextmanager
    async def mock_maker():
        yield db_session

    with patch("app.platform.workers.parser_worker.async_session_maker", mock_maker):
        yield
        
    from app.platform.events import event_publisher
    event_publisher.clear_subscribers()

async def register_and_login(client: AsyncClient, email: str) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test Chat User", "password": "Password123"}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123"}
    )
    return login_res.json()["access_token"]

async def test_conversational_advisor_flow(client: AsyncClient, db_session):
    email = "advisor_chat@example.com"
    token = await register_and_login(client, email)
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch user ID from DB
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    assert user is not None
    user_id = user.id

    # 1. Upload mock statement first to build financial context
    today = date.today()
    june_1 = date(today.year, today.month - 1, 1)
    june_15 = date(today.year, today.month - 1, 15)
    july_1 = date(today.year, today.month, 1)
    july_15 = date(today.year, today.month, 15)

    csv_data = (
        "Date,Description,Amount,Balance\n"
        f"{june_1.isoformat()},Salary Payment,300000.00,300000.00\n"
        f"{june_15.isoformat()},Netflix Subscription,-4500.00,295500.00\n"
        f"{june_15.isoformat()},POS SHOPRITE LEKKI,-20000.00,275500.00\n"
        f"{july_1.isoformat()},Salary Payment,300000.00,300000.00\n"
        f"{july_15.isoformat()},Netflix Subscription,-4500.00,295500.00\n"
        f"{july_15.isoformat()},POS SHOPRITE LEKKI,-40000.00,255500.00\n"
    )

    upload_res = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.csv", csv_data.encode("utf-8"), "text/csv")},
        data={
            "bank_name": "Zenith Bank",
            "account_name": "Advisor Account",
            "statement_period_start": "2026-06-01",
            "statement_period_end": "2026-07-31"
        }
    )
    assert upload_res.status_code == status.HTTP_201_CREATED
    statement_id = upload_res.json()["data"]["id"]

    # Poll statement 1 until finished
    for _ in range(30):
        res = await client.get(f"/api/v1/statements/{statement_id}", headers=headers)
        if res.json()["data"]["upload_status"] in ["COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED"]:
            break
        await asyncio.sleep(0.1)

    # 2. Trigger Chat request (creates first session)
    chat_res = await client.post(
        "/api/v1/chat",
        headers=headers,
        json={"content": "Where did my salary go?"}
    )
    assert chat_res.status_code == status.HTTP_200_OK
    chat_data = chat_res.json()["data"]
    convo_id = chat_data["conversation_id"]
    
    assert convo_id is not None
    assert chat_data["user_message"]["content"] == "Where did my salary go?"
    assert "income" in chat_data["ai_message"]["content"].lower()
    
    # Assert metadata is tracked on the message
    ai_msg = chat_data["ai_message"]
    assert ai_msg["model_used"] == "mock-gemini-1.5-flash"
    assert ai_msg["prompt_version"] == "v1.0"
    assert ai_msg["latency_ms"] is not None
    assert ai_msg["token_usage"] is not None
    assert ai_msg["token_usage"]["prompt_tokens"] > 0
    assert ai_msg["token_usage"]["completion_tokens"] > 0

    # 3. Retrieve User Conversations list
    list_res = await client.get("/api/v1/conversations", headers=headers)
    assert list_res.status_code == status.HTTP_200_OK
    convos = list_res.json()["data"]
    assert len(convos) >= 1
    assert any(c["id"] == convo_id for c in convos)
    
    # Verify title auto-truncation worked
    matched_convo = next(c for c in convos if c["id"] == convo_id)
    assert "Where did my salary go" in matched_convo["title"]

    # 4. Fetch Conversation detailed history logs
    detail_res = await client.get(f"/api/v1/conversations/{convo_id}", headers=headers)
    assert detail_res.status_code == status.HTTP_200_OK
    detail = detail_res.json()["data"]
    assert detail["id"] == convo_id
    assert len(detail["messages"]) == 2 # USER & AI messages
    assert detail["messages"][0]["sender"] == "USER"
    assert detail["messages"][1]["sender"] == "AI"

    # 5. Verify repository history window limits
    convo_repo = ConversationRepository(db_session)
    # Seed 15 messages manually
    for i in range(15):
        sender = "USER" if i % 2 == 0 else "AI"
        await convo_repo.create_message(
            conversation_id=uuid.UUID(convo_id),
            sender=sender,
            content=f"Message index {i}"
        )
    
    # Fetch log with window limit = 10
    limit_messages = await convo_repo.get_conversation_messages(uuid.UUID(convo_id), limit=10)
    assert len(limit_messages) == 10
    # Chronological ascending assert: last index seeded ("Message index 14") must be at the end of chronologically reversed list
    assert limit_messages[-1].content == "Message index 14"
    assert limit_messages[0].content == "Message index 5"
