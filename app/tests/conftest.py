import asyncio
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient
from app.main import app
from app.db.session import get_db
from app.db.base import Base

# Reuse the application's engine or create a dedicated connection.
# For simplicity and reliability in testing, we use the same database connection URL
# but run every test inside a transaction that is rolled back at the end.
from app.core.config import settings

# Reuse the application's engine or create a dedicated connection.

@pytest.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture that runs each test in a separate transaction and rolls it back
    after the test finishes.
    """
    connection = await db_engine.connect()
    transaction = await connection.begin()
    
    # Sessionbound class
    async_session = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async with async_session() as session:
        yield session
        await session.close()
        
    await transaction.rollback()
    await connection.close()

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Client fixture overriding the database session dependency with the transactional testing session.
    """
    async def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    # Construct async client
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
        
    app.dependency_overrides.clear()
