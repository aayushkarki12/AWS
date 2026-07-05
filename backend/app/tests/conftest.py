"""Shared pytest fixtures: async DB session against a real Postgres test schema."""
import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.rate_limit import limiter
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.employee import Employee
from app.models.user import Role, RoleName, User

limiter.enabled = False

TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://ams_user:ams_password@localhost:5433/ams_test_db"
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        for role_name in RoleName:
            session.add(Role(name=role_name.value, description=role_name.value))
        await session.commit()
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def create_user_with_role(
    db_session: AsyncSession, email: str, role_name: str, password: str = "Str0ng!Passw0rd"
) -> User:
    result = await db_session.execute(select(Role).where(Role.name == role_name))
    role = result.scalar_one()
    user = User(
        email=email, hashed_password=hash_password(password), role_id=role.id, is_active=True
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    return user


async def create_employee_for_user(
    db_session: AsyncSession, user: User, employee_code: str, first_name: str, last_name: str
) -> Employee:
    employee = Employee(
        user_id=user.id, employee_code=employee_code, first_name=first_name, last_name=last_name
    )
    db_session.add(employee)
    await db_session.flush()
    await db_session.commit()
    return employee


def authed_client_for(client: AsyncClient, user: User, role_name: str) -> AsyncClient:
    access_token, _ = create_access_token(str(user.id), role_name)
    client.cookies.set("ams_access_token", access_token)
    return client
