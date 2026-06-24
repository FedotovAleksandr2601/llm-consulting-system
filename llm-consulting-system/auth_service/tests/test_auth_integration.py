from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.api.deps import get_db
from app.db.base import Base
from app.main import app


TEST_DB_PATH = Path("test_auth.db")
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    test_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.anyio
async def test_register_login_me_flow(client: AsyncClient):
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "ivanov@example.com",
            "password": "secret123",
        },
    )
    assert register_response.status_code == 201
    register_data = register_response.json()
    assert register_data["email"] == "ivanov@example.com"
    assert register_data["role"] == "user"
    assert "password_hash" not in register_data

    login_response = await client.post(
        "/auth/login",
        data={
            "username": "ivanov@example.com",
            "password": "secret123",
        },
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"

    token = login_data["access_token"]

    me_response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == "ivanov@example.com"
    assert me_data["role"] == "user"


@pytest.mark.anyio
async def test_duplicate_registration_returns_409(client: AsyncClient):
    payload = {
        "email": "petrov@example.com",
        "password": "secret123",
    }

    first_response = await client.post("/auth/register", json=payload)
    assert first_response.status_code == 201

    second_response = await client.post("/auth/register", json=payload)
    assert second_response.status_code == 409


@pytest.mark.anyio
async def test_login_with_wrong_password_returns_401(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={
            "email": "sidorov@example.com",
            "password": "secret123",
        },
    )

    response = await client.post(
        "/auth/login",
        data={
            "username": "sidorov@example.com",
            "password": "wrong-password",
        },
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_me_without_token_returns_401(client: AsyncClient):
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_me_with_invalid_token_returns_401(client: AsyncClient):
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401