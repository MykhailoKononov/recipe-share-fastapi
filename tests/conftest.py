import sys
from asyncio import WindowsSelectorEventLoopPolicy

import pytest
import pytest_asyncio
import asyncio
import contextlib

from typing import Any, AsyncGenerator, Callable

from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from sqlalchemy import select

from main import app
from app.database.models import Base, User
from app.database.session import get_db
from config import Config

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())


class TestDatabase:
    def __init__(self):
        self._engine: AsyncEngine = create_async_engine(Config.TEST_DATABASE_URL, future=True, echo=True)
        self._session_maker = sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @contextlib.asynccontextmanager
    async def session(self):
        async with self._session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def get_engine(self):
        return self._engine

    def get_session_maker(self):
        return self._session_maker


@pytest.fixture(scope="function")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


test_db = TestDatabase()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clear_database():
    engine = test_db.get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_db.session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
def override_get_db():
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(override_get_db) -> AsyncGenerator[AsyncClient, Any]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
def get_user_from_database() -> Callable[..., Any]:
    async def _get(**filters) -> User | None:
        async for session in _get_test_db():
            result = await session.execute(select(User).filter_by(**filters))
            return result.scalar_one_or_none()
    return _get
