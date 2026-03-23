"""Test configuration for EsportsForge backend tests."""

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.db.base import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_db():
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def test_client():
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(test_client: AsyncClient):
    """Register a test user and return auth headers."""
    await test_client.post("/api/v1/auth/register", json={
        "email": "test@esportsforge.com",
        "username": "testplayer",
        "password": "TestPass123!",
    })
    response = await test_client.post("/api/v1/auth/login", json={
        "email": "test@esportsforge.com",
        "password": "TestPass123!",
    })
    if response.status_code == 200:
        token = response.json().get("access_token", "")
        return {"Authorization": f"Bearer {token}"}
    return {}
