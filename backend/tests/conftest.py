"""Shared test fixtures for EsportsForge backend."""
import pytest
import pytest_asyncio

try:
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from app.db.base import Base, get_db
    from app.main import app
    _FULL_APP_AVAILABLE = True
except BaseException:  # pyo3_runtime.PanicException is not a subclass of Exception
    _FULL_APP_AVAILABLE = False

TEST_DB_URL = "sqlite+aiosqlite:///./test_esportsforge.db"


@pytest_asyncio.fixture
async def test_db():
    if not _FULL_APP_AVAILABLE:
        pytest.skip("Full app dependencies unavailable (aiosqlite/jose/cryptography)")
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db):
    if not _FULL_APP_AVAILABLE:
        pytest.skip("Full app dependencies unavailable")

    async def override_get_db():
        yield test_db
    app.dependency_overrides[get_db] = override_get_db  # type: ignore[union-attr]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
