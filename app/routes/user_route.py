import uuid

from logging import getLogger

from fastapi import APIRouter, Depends, status, HTTPException

from app.database.models import User
from app.database.session import get_db
from app.repository.users import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


user_router = APIRouter(tags=['users'])

logger = getLogger(__name__)


@user_router.get("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> UserResponse:
    user = await UserRepository(db).get_user_by_id(user_id=user_id)
    return user


@user_router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)) -> UserResponse:
    existing_user = await db.execute(select(User).where((User.username == user.username) | (User.email == user.email)))
    if existing_user.scalars().first():
        raise HTTPException(status_code=400, detail="User with this email or username already exists")

    db_user = await UserRepository(db).create_user(username=user.username, email=user.email)
    return db_user


@user_router.patch("/{user_id}", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def update_user(user_id: uuid.UUID, user_update: UserUpdate, db: AsyncSession = Depends(get_db)) -> UserResponse:
    user = await UserRepository(db).get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=400, detail=f"User with id {user_id} does not exist")
    updated_user = await UserRepository(db).update_user_by_id(user_id=user_id, **user_update.model_dump(exclude_unset=True))
    return updated_user


@user_router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict:
    user = await UserRepository(db).get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=400, detail=f"User does not exist")
    if not user.is_active:
        raise HTTPException(status_code=409, detail=f"User is already deleted")
    await UserRepository(db).delete_user(user_id)

    return {"detail": f"User was deleted successfully"}
