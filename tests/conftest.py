"""
Comprehensive test suite for AI Accountant API.
Tests all endpoints, authentication, and AI parsing.

Run with: pytest tests/ -v
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from api.main import app
from api.database import Base, get_db
from api.models.user import User
from api.models.category import Category
from api.auth.jwt import get_password_hash

# Test database URL (use separate test database!)
TEST_DATABASE_URL = "postgresql+asyncpg://komrxn@localhost:5432/midas_test_db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,  # Disable pooling for tests
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a clean database for each test."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def auth_headers(client: AsyncClient) -> dict:
    """Get authentication headers for test user."""
    # Register user
    response = await client.post(
        "/auth/register",
        json={
            "username": "authuser",
            "email": "auth@example.com",
            "password": "authpass123"
        }
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
async def default_categories(db_session: AsyncSession) -> list[Category]:
    """Create default categories."""
    categories = [
        Category(name="Питание", slug="food", type="expense", icon="🍔", color="#E74C3C", is_default=True),
        Category(name="Транспорт", slug="transport", type="expense", icon="🚕", color="#3498DB", is_default=True),
        Category(name="Зарплата", slug="salary", type="income", icon="💰", color="#27AE60", is_default=True),
    ]
    
    for cat in categories:
        db_session.add(cat)
    
    await db_session.commit()
    
    for cat in categories:
        await db_session.refresh(cat)
    
    return categories
