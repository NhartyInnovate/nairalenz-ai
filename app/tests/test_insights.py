from datetime import date, timedelta
import uuid
import pytest
from httpx import AsyncClient
from fastapi import status
from app.financial_insights.models.insight import Insight
from app.financial_insights.models.financial_health_snapshot import FinancialHealthSnapshot
from app.financial_insights.models.recurring_payment import RecurringPayment
from app.platform.events import event_publisher

pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
async def setup_worker_and_seeder(db_session):
    """
    Setup fixture to configure worker hooks, database seeds, and mock session.
    """
    from app.platform.workers.parser_worker import init_worker
    from app.financial_intelligence.utils.seeder import seed_data_if_empty
    from contextlib import asynccontextmanager
    from unittest.mock import patch
    
    init_worker()
    
    # Seed categories and rules
    await seed_data_if_empty(db_session)

    @asynccontextmanager
    async def mock_maker():
        yield db_session

    with patch("app.platform.workers.parser_worker.async_session_maker", mock_maker):
        yield
        
    event_publisher.clear_subscribers()

async def register_and_login(client: AsyncClient, email: str) -> str:
    """Helper to register and login a user, returning their access token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test Insights User", "password": "Password123"}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123"}
    )
    return login_res.json()["access_token"]

async def test_financial_insights_pipeline_generation(client: AsyncClient):
    token = await register_and_login(client, "insightpipeline@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Generate mock CSV with:
    # - Salary income
    # - Grocery expenses (Shoprite) recurring over 2 consecutive months (June & July)
    # - A duplicate transaction on the same day (anomaly check)
    # - A recurring Netflix subscription (approx 30 days)
    today = date.today()
    june_1 = date(today.year, today.month - 1, 1)
    june_15 = date(today.year, today.month - 1, 15)
    july_1 = date(today.year, today.month, 1)
    july_15 = date(today.year, today.month, 15)
    
    csv_data = (
        "Date,Description,Amount,Balance\n"
        # June period
        f"{june_1.isoformat()},Salary Payment,300000.00,300000.00\n"
        f"{june_15.isoformat()},Netflix Subscription,-4500.00,295500.00\n"
        f"{june_15.isoformat()},POS SHOPRITE LEKKI,-20000.00,275500.00\n"
        # July period
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

    # Upload duplicate in second statement to bypass intra-file filtering
    csv_data_dup = (
        "Date,Description,Amount,Balance\n"
        f"{july_15.isoformat()},POS SHOPRITE LEKKI,-40000.00,215500.00\n"
    )
    upload_res2 = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement_dup.csv", csv_data_dup.encode("utf-8"), "text/csv")},
        data={
            "bank_name": "Zenith Bank",
            "account_name": "Insights Account 2",
            "statement_period_start": "2026-07-01",
            "statement_period_end": "2026-07-31"
        }
    )
    assert upload_res2.status_code == status.HTTP_201_CREATED
    statement_id_dup = upload_res2.json()["data"]["id"]

    # Poll statement 2 until finished
    for _ in range(30):
        res = await client.get(f"/api/v1/statements/{statement_id_dup}", headers=headers)
        if res.json()["data"]["upload_status"] in ["COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED"]:
            break
        await asyncio.sleep(0.1)
    
    # 1. Verify health snapshot (poll until background insights service finishes second run)
    health_data = {}
    for _ in range(40):
        health_res = await client.get("/api/v1/financial-health", headers=headers)
        if health_res.status_code == status.HTTP_200_OK:
            health_data = health_res.json()["data"]
            if health_data.get("total_expenses") == "84500.00":
                break
        await asyncio.sleep(0.1)
        
    assert health_data.get("total_income") == "300000.00"
    assert health_data.get("total_expenses") == "84500.00"
    assert health_data.get("financial_health_score") > 0
    assert health_data.get("score_version") == "1.0"
    
    # 2. Verify insights generated
    insights_res = await client.get("/api/v1/insights", headers=headers)
    assert insights_res.status_code == status.HTTP_200_OK
    insights = insights_res.json()["data"]
    assert len(insights) >= 2 # should have MoM trend and duplicate anomaly
    
    trends = [i for i in insights if i["insight_type"] == "SPENDING_TREND"]
    assert len(trends) >= 1
    assert "Groceries" in trends[0]["title"] or "Groceries" in trends[0]["description"]
    
    anoms = [i for i in insights if i["insight_type"] == "ANOMALY"]
    assert len(anoms) >= 1
    assert "Duplicate" in anoms[0]["title"]
    
    # 3. Verify recurring payment Netflix subscription detection
    rec_res = await client.get("/api/v1/recurring-payments", headers=headers)
    assert rec_res.status_code == status.HTTP_200_OK
    payments = rec_res.json()["data"]
    assert len(payments) >= 1
    assert "netflix" in payments[0]["merchant"].lower()
    assert payments[0]["frequency"] == "MONTHLY"
    assert payments[0]["status"] == "DETECTED"

import asyncio
