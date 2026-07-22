import pytest
from httpx import AsyncClient
from fastapi import status

# Make pytest-asyncio run functions as async tests
pytestmark = pytest.mark.asyncio

async def test_successful_registration(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "full_name": "Test User",
            "password": "Password123"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["message"] == "Registration successful."
    assert "user" in data
    assert data["user"]["email"] == "testuser@example.com"
    assert data["user"]["full_name"] == "Test User"
    assert "id" in data["user"]

async def test_duplicate_email_registration(client: AsyncClient):
    # Register first user
    response1 = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "full_name": "First User",
            "password": "Password123"
        }
    )
    assert response1.status_code == status.HTTP_201_CREATED

    # Register second user with same email
    response2 = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "full_name": "Second User",
            "password": "Password123"
        }
    )
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert "detail" in response2.json()

@pytest.mark.parametrize(
    "email,full_name,password",
    [
        ("badpass@example.com", "Bad Pass", "short"),             # too short
        ("badpass@example.com", "Bad Pass", "NoNumberHere"),       # no digit
        ("badpass@example.com", "Bad Pass", "lowercase123"),       # no uppercase
        ("badpass@example.com", "Bad Pass", "UPPERCASE123"),       # no lowercase
    ]
)
async def test_invalid_password_format(client: AsyncClient, email, full_name, password):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": full_name,
            "password": password
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_successful_login(client: AsyncClient):
    # Register
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "loginuser@example.com",
            "full_name": "Login User",
            "password": "Password123"
        }
    )
    assert reg_response.status_code == status.HTTP_201_CREATED

    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "loginuser@example.com",
            "password": "Password123"
        }
    )
    assert login_response.status_code == status.HTTP_200_OK
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data

async def test_invalid_login_credentials(client: AsyncClient):
    # Login with non-existent email
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "Password123"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # Verify generic message
    assert response.json()["detail"] == "Incorrect email or password"

async def test_unauthorized_access_to_me(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_authorized_access_to_me(client: AsyncClient):
    # Register
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "meuser@example.com",
            "full_name": "Me User",
            "password": "Password123"
        }
    )
    assert reg_response.status_code == status.HTTP_201_CREATED

    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "meuser@example.com",
            "password": "Password123"
        }
    )
    assert login_response.status_code == status.HTTP_200_OK
    token = login_response.json()["access_token"]

    # Access /me with token
    headers = {"Authorization": f"Bearer {token}"}
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == status.HTTP_200_OK
    
    data = me_response.json()
    assert data["email"] == "meuser@example.com"
    assert data["full_name"] == "Me User"
    assert "id" in data

async def test_case_insensitive_login(client: AsyncClient):
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "caseinsensitive@example.com",
            "full_name": "Case User",
            "password": "Password123"
        }
    )
    # Login with uppercase email
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "CASEINSENSITIVE@EXAMPLE.COM",
            "password": "Password123"
        }
    )
    assert login_response.status_code == status.HTTP_200_OK
    assert "access_token" in login_response.json()

from sqlalchemy import select
from app.identity.models.user import User

async def test_inactive_user_token_rejected(client: AsyncClient, db_session):
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "deactivated@example.com",
            "full_name": "Deactivated User",
            "password": "Password123"
        }
    )
    # Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "deactivated@example.com",
            "password": "Password123"
        }
    )
    token = login_response.json()["access_token"]

    # Deactivate the user directly in database
    result = await db_session.execute(
        select(User).where(User.email == "deactivated@example.com")
    )
    db_user = result.scalar_one()
    db_user.is_active = False
    await db_session.commit()

    # Try to access protected endpoint with the token
    headers = {"Authorization": f"Bearer {token}"}
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == status.HTTP_401_UNAUTHORIZED

