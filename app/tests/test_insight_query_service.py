import pytest
import asyncio
from datetime import date, timedelta
from httpx import AsyncClient
from fastapi import status
from sqlalchemy import select

from app.identity.models.user import User
from app.financial_insights.services.query_service import InsightQueryService

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
        json={"email": email, "full_name": "Test Query User", "password": "Password123"}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123"}
    )
    return login_res.json()["access_token"]

async def test_insight_query_service_facade(client: AsyncClient, db_session):
    email = "query_facade@example.com"
    token = await register_and_login(client, email)
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch user ID from DB
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    assert user is not None
    user_id = user.id

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
            "account_name": "Insights Account",
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

    # Initialize façade service
    query_service = InsightQueryService(db_session)
    
    # Retrieve FinancialIntelligenceContext
    context = await query_service.get_user_financial_context(user_id)
    
    # Assert query service returned a valid context
    assert context is not None
    assert context.snapshot is not None
    assert context.snapshot.total_income == 300000.00
    assert context.snapshot.total_expenses == 44500.00
    assert len(context.active_insights) >= 1
    assert len(context.recurring_payments) >= 1
    
    # Verify transaction summaries
    assert len(context.recent_transactions_summary) >= 1
    groceries_summary = next(s for s in context.recent_transactions_summary if s.category_name == "Groceries")
    assert groceries_summary.total_amount == 40000.00
    assert groceries_summary.transaction_count == 1

    # Verify LLM-extension blocks
    assert hasattr(context, "forecasts")
    assert context.forecasts is None
    assert context.budgets is None
    assert context.goals is None
    assert context.recommendations is None
