import uuid

from logging import getLogger

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.services.dependencies import get_current_user

from app.database.models import User
from app.database.session import get_db
from app.repository.user_repo import UserRepository
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth import signin, signup, signout

user_router = APIRouter(tags=['users'])

logger = getLogger(__name__)


@user_router.get("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> UserResponse:
    user = await UserRepository(db).get_user_by_id(user_id=user_id)
    return user


@user_router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_create: UserCreate, session: AsyncSession = Depends(get_db)) -> UserResponse:
    db_user = await UserRepository(session).create_user(**user_create.model_dump(exclude_unset=True))
    return db_user


@user_router.patch("/{user_id}", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def update_user(
        user_id: uuid.UUID,
        user_update: UserUpdate,
        session: AsyncSession = Depends(get_db)
) -> UserResponse:
    user = await UserRepository(session).get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=400, detail=f"User with id {user_id} does not exist")
    updated_user = await UserRepository(session).update_user_by_id(
        user_id=user_id,
        **user_update.model_dump(exclude_unset=True)
    )
    return updated_user


@user_router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_db)) -> dict:
    user = await UserRepository(session).get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=400, detail=f"User does not exist")
    if not user.is_active:
        raise HTTPException(status_code=409, detail=f"User is already deleted")
    await UserRepository(session).delete_user(user_id)

    return {"detail": f"User was deleted successfully"}


auth_router = APIRouter(tags=["auth"])


@auth_router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate, session: AsyncSession = Depends(get_db)) -> dict:
    return await signup(session, **user_create.model_dump(exclude_unset=True))


@auth_router.post("/signin", status_code=status.HTTP_200_OK)
async def login(form: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db)) -> dict:
    return await signin(form.username, form.password, session)


@auth_router.post("/signout", status_code=status.HTTP_200_OK)
async def logot(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> dict:
    return await signout(current_user, session)
