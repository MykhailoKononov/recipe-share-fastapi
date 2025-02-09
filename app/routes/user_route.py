from logging import getLogger
from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

from app.services.auth_services.dependencies import get_current_user

from app.database.models import User
from app.database.session import get_db
from app.repository.user_repo import UserRepository
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_services.auth import signin, signout

from app.services.user_services import UserService

user_router = APIRouter(tags=['users'])

logger = getLogger(__name__)


@user_router.get("/get-info", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(
        username: Optional[EmailStr | str] = None,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> UserResponse:
    return await UserService(UserRepository(db)).get_user_info(current_user, username)


@user_router.patch("/update", response_model=UserResponse, status_code=status.HTTP_201_CREATED, )
async def update_user(
        user_update: UserUpdate,
        username: Optional[EmailStr | str] = None,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> UserResponse:
    return await UserService(UserRepository(db)).update_user(current_user, username, user_update)


@user_router.delete("/delete-account", status_code=status.HTTP_200_OK)
async def delete_user(
        username: Optional[EmailStr | str] = None,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> dict:
    await UserService(UserRepository(db)).delete_user(current_user, username)
    return {"detail": "User was deleted successfully"}


auth_router = APIRouter(tags=["auth"])


@auth_router.post("/sign-up", status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate, db: AsyncSession = Depends(get_db)) -> dict:
    await UserService(UserRepository(db)).create_account(user_create)
    return {"msg": "Account successfully created"}


@auth_router.post("/sign-in", status_code=status.HTTP_200_OK)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)) -> dict:
    return await signin(form.username, form.password, db)


@auth_router.post("/sign-out", status_code=status.HTTP_200_OK)
async def logot(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    return await signout(current_user, db)
