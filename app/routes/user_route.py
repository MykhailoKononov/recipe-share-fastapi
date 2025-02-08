from logging import getLogger
from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

from app.services.dependencies import get_current_user, moderate_required

from app.database.models import User, Role
from app.database.session import get_db
from app.repository.user_repo import UserRepository
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate, UserIsActive
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth import signin, signup, signout
from app.services.roles import check_access

user_router = APIRouter(tags=['users'])

logger = getLogger(__name__)


@user_router.get("/get-info", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(
        username: Optional[EmailStr | str] = None,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> UserResponse:
    if check_access(current_user, username):
        return await UserRepository(session).get_user_by_username(username)
    user = await UserRepository(session).get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if current_user.role == Role.moderator and user.role == Role.admin:
        raise HTTPException(status_code=403, detail="Access denied")
    return user


@user_router.post("/user-create", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
        user_create: UserCreate,
        session: AsyncSession = Depends(get_db)
) -> UserResponse:
    db_user = await UserRepository(session).create_user(**user_create.model_dump(exclude_unset=True))
    return db_user


@user_router.patch("/update", response_model=UserResponse, status_code=status.HTTP_201_CREATED, )
async def update_user(
        user_update: UserUpdate,
        username: Optional[EmailStr | str] = None,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> UserResponse:
    if check_access(current_user, username):
        return await UserRepository(session).update_user_by_username(
            username=current_user.username,
            **user_update.model_dump(exclude_unset=True)
        )
    user = await UserRepository(session).get_user_by_username(username=username)
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found")
    if current_user.role == Role.moderator and user.role == Role.admin:
        raise HTTPException(status_code=403, detail="Access denied")
    updated_user = await UserRepository(session).update_user_by_username(
        username=username,
        **user_update.model_dump(exclude_unset=True)
    )
    return updated_user


@user_router.delete("/delete-account", status_code=status.HTTP_200_OK)
async def delete_user(
        username: Optional[EmailStr | str] = None,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> dict:
    if not username or username in {current_user.username, current_user.email}:
        if current_user.role == Role.admin:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admin cannot delete himself")
        await UserRepository(session).delete_user(current_user.username)
        return {"detail": "User was deleted successfully"}

    user = await UserRepository(session).get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=400, detail="User does not exist")

    if current_user.role == Role.user:
        raise HTTPException(status_code=403, detail="Access denied")

    if current_user.role == Role.moderator and user.role in {Role.admin, Role.moderator}:
        raise HTTPException(status_code=403, detail="Access denied")

    await UserRepository(session).delete_user(username)
    return {"detail": "User was deleted successfully"}


auth_router = APIRouter(tags=["auth"])


@auth_router.post("/sign-up", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate, session: AsyncSession = Depends(get_db)) -> dict:
    return await signup(session, **user_create.model_dump(exclude_unset=True))


@auth_router.post("/sign-in", status_code=status.HTTP_200_OK)
async def login(form: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db)) -> dict:
    return await signin(form.username, form.password, session)


@auth_router.post("/sign-out", status_code=status.HTTP_200_OK)
async def logot(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> dict:
    return await signout(current_user, session)
