import asyncio
from decimal import Decimal
import pytest
from httpx import AsyncClient
from fastapi import status
from app.financial_intelligence.models.category import Category
from app.financial_intelligence.models.merchant import Merchant
from app.financial_intelligence.models.rule import CategorizationRule
from app.financial_intelligence.models.history import CategorizationHistory
from app.financial_intelligence.services.intelligence_service import FinancialIntelligenceService
from app.platform.events import event_publisher

pytestmark = pytest.mark.asyncio

# Standard helper to generate a valid mock PDF content
VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"

@pytest.fixture(autouse=True)
async def setup_worker_and_seeder(db_session):
    """
    Autouse fixture to register the worker subscription, run database seeder,
    and mock the session maker for background processing.
    """
    from app.platform.workers.parser_worker import init_worker
    from app.financial_intelligence.utils.seeder import seed_data_if_empty
    from contextlib import asynccontextmanager
    from unittest.mock import patch
    
    init_worker()
    
    # Run DB seeder for standard category rules
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
        json={"email": email, "full_name": "Test Intel User", "password": "Password123"}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123"}
    )
    return login_res.json()["access_token"]

async def test_merchant_resolution_and_rules_categorization(client: AsyncClient):
    token = await register_and_login(client, "intel@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Test CSV upload with distinct keywords matching merchants/rules
    # Rows feature:
    # - Shoprite (MTN is partial match / Shoprite exact)
    # - Uber matching rules
    # - Unknown item triggering needs categorization AI flow
    csv_data = (
        "Date,Description,Amount,Balance\n"
        "2026-01-01,POS SHOPRITE LEKKI,4000.00,10000.00\n"
        "2026-01-02,UBER TRIP RIDE,2500.00,7500.00\n"
        "2026-01-03,UNKNOWN TRANSACTION CORNER,500.00,7000.00\n"
    )
    
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.csv", csv_data.encode("utf-8"), "text/csv")},
        data={
            "bank_name": "Zenith Bank",
            "account_name": "Intel Account",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    statement_id = response.json()["data"]["id"]
    
    # Wait for the background worker to execute parsing -> normalization -> categorization
    await asyncio.sleep(0.8)
    
    # Verify categories and merchant IDs updated on transaction models
    tx_res = await client.get(f"/api/v1/statements/{statement_id}/transactions", headers=headers)
    assert tx_res.status_code == status.HTTP_200_OK
    txs = tx_res.json()["data"]
    
    assert len(txs) == 3
    
    # POS SHOPRITE LEKKI matches Shoprite merchant, maps to preferred category "Groceries"
    shoprite_tx = [t for t in txs if "shoprite" in t["description"].lower()][0]
    assert shoprite_tx["merchant_id"] is not None
    assert shoprite_tx["confidence"] >= 0.80
    
    # UBER TRIP RIDE matches pattern rule "uber" or partial merchant, maps to "Transport" (confidence >= 0.80)
    uber_tx = [t for t in txs if "uber" in t["description"].lower()][0]
    assert uber_tx["confidence"] >= 0.80
    
    # UNKNOWN TRANSACTION CORNER gets uncategorized, triggers AI fallback (confidence < 0.80)
    unknown_tx = [t for t in txs if "unknown" in t["description"].lower()][0]
    assert unknown_tx["confidence"] < 0.80

async def test_user_category_correction_loop(client: AsyncClient):
    token = await register_and_login(client, "correction@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    csv_data = "Date,Description,Amount,Balance\n2026-01-01,POS SHOPRITE LEKKI,4000.00,10000.00\n"
    
    upload_res = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.csv", csv_data.encode("utf-8"), "text/csv")},
        data={
            "bank_name": "Zenith Bank",
            "account_name": "Intel Account",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    statement_id = upload_res.json()["data"]["id"]
    await asyncio.sleep(0.5)
    
    tx_res = await client.get(f"/api/v1/statements/{statement_id}/transactions", headers=headers)
    tx_id = tx_res.json()["data"][0]["id"]
    
    # Get standard system categories to select replacement category id
    cats_res = await client.get("/api/v1/categories", headers=headers)
    categories = cats_res.json()["data"]
    shopping_cat = [c for c in categories if c["name"] == "Shopping"][0]
    
    # Manual update transaction category override PATCH
    patch_res = await client.patch(
        f"/api/v1/transactions/{tx_id}/category",
        headers=headers,
        json={"category_id": shopping_cat["id"], "reason": "Purchased clothing items at the outlet"}
    )
    assert patch_res.status_code == status.HTTP_200_OK
    body = patch_res.json()
    assert body["success"] is True
    assert body["data"]["category_id"] == shopping_cat["id"]
    assert body["data"]["confidence"] == 1.0
