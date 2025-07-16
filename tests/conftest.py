import io
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
import asyncio
import contextlib

from main import app
from config import Config
from app.services.auth_services.auth import create_refresh_token, create_access_token
from app.services.auth_services.hashing import Hasher
from app.database.models import Base, User, Recipe, RecipeIngredient, Ingredient
from app.database.session import get_db

from PIL import Image
from typing import Any, AsyncGenerator, Callable, Optional, List, Dict
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


@contextlib.asynccontextmanager
async def get_root_engine():
    engine = create_async_engine(Config.TEST_DATABASE_URL, echo=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@contextlib.asynccontextmanager
async def get_root_async_session():
    engine = create_async_engine(Config.TEST_DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with async_session() as session:
            yield session
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clear_database():
    async with get_root_engine() as engine:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    yield


async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_root_async_session() as session:
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


@pytest_asyncio.fixture(scope="function")
def get_recipe_from_database() -> Callable[..., Any]:
    async def _get(recipe_id: uuid.UUID) -> Recipe | None:
        async for session in _get_test_db():
            result = await session.execute(select(Recipe).options(
                selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
                selectinload(Recipe.author)
            ).where(Recipe.recipe_id == recipe_id))
            return result.scalar_one_or_none()
    return _get


@pytest_asyncio.fixture(scope="function")
def create_test_user() -> Callable[..., Any]:
    async def _create(
        username: str = "johndoe",
        email: str = "john@example.com",
        role: str = "user",
        is_verified: bool = False,
        with_refresh: bool = False
    ) -> User:
        hashed_pass = Hasher.get_password_hash("Test1234")
        user = User(
            user_id=uuid.uuid4(),
            username=username,
            email=email,
            first_name="john",
            last_name="doe",
            hashed_password=hashed_pass,
            role=role,
            is_verified=is_verified,
        )
        async for session in _get_test_db():
            session.add(user)
            await session.commit()
            await session.refresh(user)

            if with_refresh:
                token = create_refresh_token(str(user.user_id))
                user.refresh_token = token
                session.add(user)
                await session.commit()
                await session.refresh(user)

            return user
    return _create


@pytest_asyncio.fixture(scope="function")
def create_test_recipe() -> Callable[..., Any]:
    async def _create(
        user_id: uuid.UUID,
        title: str = "title",
        description: Optional[str] = None,
        ingredients: Optional[List[Dict[str, Any]]] = None,
    ) -> Recipe:
        if ingredients is None:
            ingredients = [
                {"name": "test1", "quantity": "2"},
                {"name": "test2", "quantity": "2"},
            ]

        async for session in _get_test_db():
            recipe = Recipe(
                title=title,
                description=description,
                user_id=user_id
            )
            session.add(recipe)
            await session.flush()

            result = await session.execute(
                select(Recipe)
                .options(
                    selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
                    selectinload(Recipe.author),
                )
                .where(Recipe.recipe_id == recipe.recipe_id)
            )
            full_recipe = result.scalar_one()

            for ing in ingredients:
                q = await session.execute(
                    select(Ingredient).where(Ingredient.name == ing["name"])
                )
                ingr_obj = q.scalar_one_or_none()
                if not ingr_obj:
                    ingr_obj = Ingredient(name=ing["name"])
                    session.add(ingr_obj)
                    await session.flush()

                full_recipe.ingredients.append(
                    RecipeIngredient(
                        ingredient=ingr_obj,
                        quantity=ing["quantity"],
                    )
                )

            await session.commit()
            return full_recipe

    return _create


def create_test_auth_headers_for_user(user_id: str, scopes: Optional[List[str]] = None) -> dict[str, str]:
    access_token = create_access_token(user_id, scopes)
    return {"Authorization": f"Bearer {access_token}"}


def image_file(filename: str) -> io.BytesIO:
    path = Path(__file__).parent / "data" / filename
    data = path.read_bytes()
    bio = io.BytesIO(data)
    bio.name = filename
    return bio
