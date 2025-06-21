from logging import getLogger
from typing import Optional

from fastapi import APIRouter, Depends, Response, Request, HTTPException, Query, status, Security
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr

from app.schemas.responses.api_schema_resp import APIResponse
from app.services.auth_services.dependencies import get_current_user
from app.database.models import User
from app.database.session import get_db
from app.repository.user_repo import UserRepository
from app.schemas.responses.user_schema_resp import UserResponse
from app.schemas.requests.user_schema_req import UserUpdate, UserCreate
from app.schemas.responses.token_schema_resp import Token
from app.services.auth_services.auth import (
    signout, signup, authenticate_user, refresh_user, create_access_token, create_refresh_token, verify_token,
    send_verification_email)

from app.services.user_services import UserService
from config import ROLE_SCOPES

user_router = APIRouter(tags=['users'])

logger = getLogger(__name__)


@user_router.delete("/delete-account", status_code=status.HTTP_200_OK)
async def delete_user(
        username: Optional[EmailStr | str] = None,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> dict:
    await UserService(UserRepository(db)).delete_user(current_user, username)
    return {"detail": "User was deleted successfully"}


auth_router = APIRouter(tags=["auth"])


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate, session: AsyncSession = Depends(get_db)) -> dict:
    user = await signup(session, user_create)

    await send_verification_email(user)

    return {
        "msg": "Account created successfully! Check your inbox to verify your email",
    }


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login(form: OAuth2PasswordRequestForm = Depends(),
                db: AsyncSession = Depends(get_db),
                response: Response = None) -> dict:

    if form.grant_type == "password":
        user = await authenticate_user(form.username, form.password, db)

    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported grant_type")

    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials or token")

    user_role = user.role.value
    allowed_scopes = ROLE_SCOPES[user_role]

    if user.is_verified:
        allowed_scopes += ["user:verified"]

    access_token = create_access_token(str(user.user_id), allowed_scopes)
    refresh_token = create_refresh_token(str(user.user_id))

    user.refresh_token = refresh_token
    await db.commit()

    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, secure=True, samesite="strict"
    )

    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/token", status_code=status.HTTP_200_OK, response_model=APIResponse)
async def refresh_access_token(request: Request = None,
                               session: AsyncSession = Depends(get_db),
                               ) -> APIResponse:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token missing")

    user = await refresh_user(refresh_token, session)

    base_scopes = ROLE_SCOPES.get(user.role.value, [])
    allowed_scopes = base_scopes.copy()
    if user.is_verified:
        allowed_scopes.append("user:verified")

    new_access_token = create_access_token(str(user.user_id), allowed_scopes)

    return APIResponse(
        success=True,
        message="Access token refreshed",
        data=Token(access_token=new_access_token, token_type="Bearer").model_dump(exclude_unset=True)
    )


@auth_router.get("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(token: str = Query(...), session: AsyncSession = Depends(get_db)) -> dict:
    user = await verify_token(token, session)

    full_scopes = ["user", "user:verified"]
    access_token = create_access_token(str(user.user_id), full_scopes)
    return {
        "msg": "You successfully verified your email!",
        "access_token": access_token,
        "token_type": "bearer",
        "scopes": full_scopes
    }


@auth_router.post("/sign-out", status_code=status.HTTP_200_OK)
async def logot(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    return await signout(current_user, db)


router = APIRouter(prefix="/profile", tags=["users"])


@router.get(
    "/me",
    response_model=APIResponse,
)
async def read_my_profile(
    current_user: User = Security(get_current_user, scopes=["user", "user:verified"]),
):
    """
    Любой пользователь, у которого в access-токене есть скоуп "read", попадёт в этот контроллер.
    Если у токена нет "read" ― вернётся 401/403 на этапе Security.
    """
    return APIResponse(
        success=True,
        message="User profile fetched",
        data=UserResponse.from_orm(current_user)
    )
