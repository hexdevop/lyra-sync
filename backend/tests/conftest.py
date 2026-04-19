"""Shared fixtures for all tests."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.audio_job import AudioJob

# ── In-memory async SQLite engine ────────────────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """HTTP test client with overridden DB dependency."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def sample_job_id():
    return uuid.uuid4()


@pytest_asyncio.fixture
async def done_job(db_session, sample_job_id):
    """A completed AudioJob in the test DB."""
    job = AudioJob(
        id=sample_job_id,
        status="done",
        file_hash="abc123",
        file_url="raw/test.mp3",
        result_url="results/test/result.json",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest_asyncio.fixture
async def pending_job(db_session):
    """A pending AudioJob in the test DB."""
    job = AudioJob(
        id=uuid.uuid4(),
        status="pending",
        file_hash="def456",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job
