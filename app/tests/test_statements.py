import pytest
from httpx import AsyncClient
from fastapi import status
from app.core.config import settings

# Force pytest-asyncio to execute async tests
pytestmark = pytest.mark.asyncio

# Standard helper to generate a valid mock PDF content
VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"

async def register_and_login(client: AsyncClient, email: str) -> str:
    """Helper to register and login a user, returning their access token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": "Password123"}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123"}
    )
    return login_res.json()["access_token"]

async def test_successful_upload(client: AsyncClient):
    token = await register_and_login(client, "user1@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Upload statement
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.pdf", VALID_PDF_BYTES, "application/pdf")},
        data={
            "bank_name": "GTBank",
            "account_name": "John Doe",
            "account_number": "1234567890",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Statement uploaded successfully."
    assert "data" in body
    assert body["data"]["bank_name"] == "GTBank"
    assert body["data"]["account_name"] == "John Doe"
    assert body["data"]["original_filename"] == "statement.pdf"
    assert "id" in body["data"]

async def test_invalid_mime_type(client: AsyncClient):
    token = await register_and_login(client, "user2@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Upload statement with csv mime type
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.pdf", VALID_PDF_BYTES, "text/csv")},
        data={
            "bank_name": "GTBank",
            "account_name": "John Doe",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "MIME type must be application/pdf" in response.json()["detail"]

async def test_invalid_extension(client: AsyncClient):
    token = await register_and_login(client, "user_ext@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Upload statement with invalid extensions (e.g. .pdf.exe)
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.pdf.exe", VALID_PDF_BYTES, "application/pdf")},
        data={
            "bank_name": "GTBank",
            "account_name": "John Doe",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported file format" in response.json()["detail"]

async def test_empty_file_upload(client: AsyncClient):
    token = await register_and_login(client, "user3@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.pdf", b"", "application/pdf")},
        data={
            "bank_name": "GTBank",
            "account_name": "John Doe",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "File is empty" in response.json()["detail"]

async def test_oversized_file_upload(client: AsyncClient):
    token = await register_and_login(client, "user4@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Temporarily override setting to mock small boundary limit
    original_limit = settings.MAX_FILE_SIZE_BYTES
    settings.MAX_FILE_SIZE_BYTES = 10
    
    try:
        response = await client.post(
            "/api/v1/statements/upload",
            headers=headers,
            files={"file": ("statement.pdf", VALID_PDF_BYTES, "application/pdf")},
            data={
                "bank_name": "GTBank",
                "account_name": "John Doe",
                "statement_period_start": "2026-01-01",
                "statement_period_end": "2026-01-31"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceeds maximum limit" in response.json()["detail"]
    finally:
        # Restore configuration
        settings.MAX_FILE_SIZE_BYTES = original_limit

async def test_duplicate_upload_rejection(client: AsyncClient):
    token = await register_and_login(client, "user5@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "bank_name": "GTBank",
        "account_name": "John Doe",
        "statement_period_start": "2026-01-01",
        "statement_period_end": "2026-01-31"
    }
    
    # First upload
    res1 = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.pdf", VALID_PDF_BYTES, "application/pdf")},
        data=payload
    )
    assert res1.status_code == status.HTTP_201_CREATED
    
    # Second duplicate upload
    res2 = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.pdf", VALID_PDF_BYTES, "application/pdf")},
        data=payload
    )
    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already been uploaded by the user" in res2.json()["detail"]

async def test_cross_user_duplicate_success(client: AsyncClient):
    token_a = await register_and_login(client, "usera@example.com")
    token_b = await register_and_login(client, "userb@example.com")
    
    payload = {
        "bank_name": "GTBank",
        "account_name": "John Doe",
        "statement_period_start": "2026-01-01",
        "statement_period_end": "2026-01-31"
    }
    
    # User A uploads statement
    res_a = await client.post(
        "/api/v1/statements/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("statement.pdf", VALID_PDF_BYTES, "application/pdf")},
        data=payload
    )
    assert res_a.status_code == status.HTTP_201_CREATED
    
    # User B uploads SAME statement -> Should succeed since duplicate detection is per-user
    res_b = await client.post(
        "/api/v1/statements/upload",
        headers={"Authorization": f"Bearer {token_b}"},
        files={"file": ("statement.pdf", VALID_PDF_BYTES, "application/pdf")},
        data=payload
    )
    assert res_b.status_code == status.HTTP_201_CREATED

async def test_invalid_pdf_signature(client: AsyncClient):
    token = await register_and_login(client, "user6@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # FAKE PDF containing normal plain text instead of starting with %PDF-
    fake_pdf = b"Hello, this is actually a text file disguised as a PDF"
    
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.pdf", fake_pdf, "application/pdf")},
        data={
            "bank_name": "GTBank",
            "account_name": "John Doe",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "magic bytes signature mismatch" in response.json()["detail"]

async def test_unauthorized_upload(client: AsyncClient):
    response = await client.post(
        "/api/v1/statements/upload",
        files={"file": ("statement.pdf", VALID_PDF_BYTES, "application/pdf")},
        data={
            "bank_name": "GTBank",
            "account_name": "John Doe",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_list_and_get_user_statements(client: AsyncClient):
    token = await register_and_login(client, "user7@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Upload first
    upload_res = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement1.pdf", VALID_PDF_BYTES, "application/pdf")},
        data={
            "bank_name": "Access Bank",
            "account_name": "Jane Doe",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    statement_id = upload_res.json()["data"]["id"]
    
    # 1. Test listing
    list_res = await client.get("/api/v1/statements", headers=headers)
    assert list_res.status_code == status.HTTP_200_OK
    list_body = list_res.json()
    assert list_body["success"] is True
    assert len(list_body["data"]) == 1
    assert list_body["data"][0]["bank_name"] == "Access Bank"
    assert list_body["data"][0]["original_filename"] == "statement1.pdf"
    
    # 2. Test fetching single metadata details
    detail_res = await client.get(f"/api/v1/statements/{statement_id}", headers=headers)
    assert detail_res.status_code == status.HTTP_200_OK
    detail_body = detail_res.json()
    assert detail_body["success"] is True
    assert detail_body["data"]["bank_name"] == "Access Bank"
    assert detail_body["data"]["id"] == statement_id

async def test_successful_csv_upload(client: AsyncClient):
    token = await register_and_login(client, "csvuser@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    csv_bytes = b"Date,Description,Amount,Balance\n2026-01-01,Salary,5000,5000\n"
    
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.csv", csv_bytes, "text/csv")},
        data={
            "bank_name": "Zenith Bank",
            "account_name": "CSV Account",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["success"] is True
    assert body["data"]["original_filename"] == "statement.csv"

async def test_invalid_csv_encoding(client: AsyncClient):
    token = await register_and_login(client, "csvuser2@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Send binary files disguised as CSV (fails utf-8 decode validation check)
    binary_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.csv", binary_data, "text/csv")},
        data={
            "bank_name": "Zenith Bank",
            "account_name": "CSV Account",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid CSV encoding" in response.json()["detail"]

from app.platform.events import event_publisher

async def test_statement_uploaded_event_dispatched(client: AsyncClient):
    token = await register_and_login(client, "eventcheck@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    captured_events = []
    
    async def capture_callback(event):
        captured_events.append(event)
        
    event_publisher.subscribe("StatementUploaded", capture_callback)
    
    response = await client.post(
        "/api/v1/statements/upload",
        headers=headers,
        files={"file": ("statement.pdf", VALID_PDF_BYTES, "application/pdf")},
        data={
            "bank_name": "GTBank",
            "account_name": "Event Account",
            "statement_period_start": "2026-01-01",
            "statement_period_end": "2026-01-31"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    
    # Assert event loop captured the published event
    assert len(captured_events) == 1
    event = captured_events[0]
    assert event.bank_name == "GTBank"
    assert event.file_type == "PDF"
    assert event.file_size == len(VALID_PDF_BYTES)
    assert event.event_version == "1.0"
    assert event.event_id is not None

