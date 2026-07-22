import asyncio
from decimal import Decimal
import pytest
from httpx import AsyncClient
from fastapi import status
from app.core.config import settings
from app.financial_data.models.statement import UploadStatus
from app.platform.events import event_publisher

from contextlib import asynccontextmanager
from unittest.mock import patch
from app.platform.workers.parser_worker import init_worker

pytestmark = pytest.mark.asyncio

# Standard helper to generate a valid mock PDF content
VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
ENCRYPTED_PDF_BYTES = b"%PDF-1.4\nPASSWORD_PROTECTED\n%%EOF"
CORRUPTED_PDF_BYTES = b"%PDF-1.4\nCORRUPTED\n%%EOF"

@pytest.fixture(autouse=True)
def setup_worker(db_session):
    """
    Autouse fixture to register the worker subscription and patch the database session maker
    to run background worker tasks inside the transactional test session.
    """
    init_worker()
    
    @asynccontextmanager
    async def mock_maker():
        yield db_session

    with patch("app.platform.workers.parser_worker.async_session_maker", mock_maker):
        yield
        
    # Reset subscribers after each test to prevent accumulative triggers
    event_publisher.clear_subscribers()

async def register_and_login(client: AsyncClient, email: str) -> str:
    """Helper to register and login a user, returning their access token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test Parser User", "password": "Password123"}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123"}
    )
    return login_res.json()["access_token"]

async def test_pdf_parsing_success_flow(client: AsyncClient):
    token = await register_and_login(client, "pdfparser@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # We include "gtbank" in filename to trigger GTBankParser selection in BankDetector
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("gtbank_statement.pdf", VALID_PDF_BYTES, "application/pdf")},
        data={
            "bank_name": "GTBank",
            "account_name": "John Doe",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    statement_id = response.json()["data"]["id"]
    
    # Wait for the background worker to consume events and complete parsing
    # The subscriber handler is async, so we give it a tiny sleep window to complete
    await asyncio.sleep(0.5)
    
    # Check updated statement status
    status_res = await client.get(f"/api/v1/statements/{statement_id}", headers=headers)
    assert status_res.status_code == status.HTTP_200_OK
    statement_data = status_res.json()["data"]
    
    assert statement_data["upload_status"] in [UploadStatus.COMPLETED, UploadStatus.COMPLETED_WITH_WARNINGS]
    assert statement_data["parser_version"] == "1.0"
    assert statement_data["parsing_duration_ms"] is not None
    
    # Verify normalized transactions
    tx_res = await client.get(f"/api/v1/statements/{statement_id}/transactions", headers=headers)
    assert tx_res.status_code == status.HTTP_200_OK
    tx_data = tx_res.json()["data"]
    
    assert len(tx_data) == 2
    assert tx_data[0]["amount"] == "15000.00"
    assert tx_data[0]["transaction_type"] == "CREDIT"
    assert tx_data[1]["amount"] == "-4500.00"
    assert tx_data[1]["transaction_type"] == "DEBIT"
    assert tx_data[0]["confidence"] < 0.80

async def test_csv_semicolon_and_utf16_parsing(client: AsyncClient):
    token = await register_and_login(client, "csvparser@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # CSV using semicolons delimiter and encoded in UTF-16
    csv_text = "Date;Description;Amount;Balance;Ref\n2026-01-02;Semicolon Tx;3000.00;6000.00;REF-SEM\n"
    csv_bytes = csv_text.encode("utf-16")
    
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.csv", csv_bytes, "text/csv")},
        data={
            "bank_name": "Zenith Bank",
            "account_name": "Zenith User",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    statement_id = response.json()["data"]["id"]
    
    await asyncio.sleep(0.5)
    
    tx_res = await client.get(f"/api/v1/statements/{statement_id}/transactions", headers=headers)
    assert tx_res.status_code == status.HTTP_200_OK
    tx_data = tx_res.json()["data"]
    assert len(tx_data) == 1
    assert tx_data[0]["description"] == "Semicolon Tx"
    assert tx_data[0]["amount"] == "3000.00"
    assert tx_data[0]["reference"] == "REF-SEM"

async def test_password_protected_pdf(client: AsyncClient):
    token = await register_and_login(client, "protected@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("gtbank_secured.pdf", ENCRYPTED_PDF_BYTES, "application/pdf")},
        data={
            "bank_name": "GTBank",
            "account_name": "John Doe",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    statement_id = response.json()["data"]["id"]
    
    await asyncio.sleep(0.5)
    
    status_res = await client.get(f"/api/v1/statements/{statement_id}", headers=headers)
    statement_data = status_res.json()["data"]
    assert statement_data["upload_status"] == UploadStatus.FAILED
    assert "password-protected" in statement_data["parser_errors"]

async def test_corrupted_pdf(client: AsyncClient):
    token = await register_and_login(client, "corrupted@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("gtbank_corrupted.pdf", CORRUPTED_PDF_BYTES, "application/pdf")},
        data={
            "bank_name": "GTBank",
            "account_name": "John Doe",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    statement_id = response.json()["data"]["id"]
    
    await asyncio.sleep(0.5)
    
    status_res = await client.get(f"/api/v1/statements/{statement_id}", headers=headers)
    statement_data = status_res.json()["data"]
    assert statement_data["upload_status"] == UploadStatus.FAILED
    assert "corrupted" in statement_data["parser_errors"]

async def test_csv_missing_headers(client: AsyncClient):
    token = await register_and_login(client, "badheaders@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Missing Date column
    bad_csv = b"Description,Amount\nNo Date Row,200.00\n"
    
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.csv", bad_csv, "text/csv")},
        data={
            "bank_name": "Zenith Bank",
            "account_name": "Zenith User",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    # The validation inside routing/service happens during parse in background worker OR upload_and_process.
    # Wait, the FileValidator validates MIME/Extension/UTF-8 signature checks, but CSV column structures
    # validation happens in the background parsing stage inside CSVParser!
    # Therefore, the upload itself succeeds (creates statement), but background parsing shifts it to FAILED.
    assert response.status_code == status.HTTP_201_CREATED
    statement_id = response.json()["data"]["id"]
    
    await asyncio.sleep(0.5)
    
    status_res = await client.get(f"/api/v1/statements/{statement_id}", headers=headers)
    assert status_res.json()["data"]["upload_status"] == UploadStatus.FAILED
    assert "Missing required columns" in status_res.json()["data"]["parser_errors"]

async def test_empty_statement_parsing(client: AsyncClient):
    token = await register_and_login(client, "empty@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Just headers with zero transactions
    empty_csv = b"Date,Description,Amount,Balance\n"
    
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.csv", empty_csv, "text/csv")},
        data={
            "bank_name": "Zenith Bank",
            "account_name": "Zenith User",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    statement_id = response.json()["data"]["id"]
    
    await asyncio.sleep(0.5)
    
    status_res = await client.get(f"/api/v1/statements/{statement_id}", headers=headers)
    assert status_res.json()["data"]["upload_status"] in [UploadStatus.COMPLETED, UploadStatus.COMPLETED_WITH_WARNINGS]
    
    tx_res = await client.get(f"/api/v1/statements/{statement_id}/transactions", headers=headers)
    assert len(tx_res.json()["data"]) == 0

async def test_duplicate_row_warnings(client: AsyncClient):
    token = await register_and_login(client, "dups@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Duplicate transaction rows
    dup_csv = b"Date,Description,Amount\n2026-01-01,Same Tx,100.00\n2026-01-01,Same Tx,100.00\n"
    
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.csv", dup_csv, "text/csv")},
        data={
            "bank_name": "Zenith Bank",
            "account_name": "Zenith User",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    statement_id = response.json()["data"]["id"]
    
    await asyncio.sleep(0.5)
    
    status_res = await client.get(f"/api/v1/statements/{statement_id}", headers=headers)
    assert status_res.json()["data"]["upload_status"] == UploadStatus.COMPLETED_WITH_WARNINGS
    assert status_res.json()["data"]["warnings_count"] >= 1

async def test_large_statement_performance(client: AsyncClient):
    token = await register_and_login(client, "large@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Generate 500 transaction rows
    csv_rows = [b"Date,Description,Amount"]
    for i in range(500):
        csv_rows.append(f"2026-01-01,Transaction #{i},10.00".encode("utf-8"))
    large_csv = b"\n".join(csv_rows)
    
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.csv", large_csv, "text/csv")},
        data={
            "bank_name": "Zenith Bank",
            "account_name": "Zenith User",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    statement_id = response.json()["data"]["id"]
    
    await asyncio.sleep(1.0) # sleep slightly longer for large files
    
    status_res = await client.get(f"/api/v1/statements/{statement_id}", headers=headers)
    assert status_res.json()["data"]["upload_status"] == UploadStatus.COMPLETED
    
    tx_res = await client.get(f"/api/v1/statements/{statement_id}/transactions", headers=headers)
    assert len(tx_res.json()["data"]) == 500
