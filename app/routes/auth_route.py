from logging import getLogger

from fastapi import APIRouter, Depends, Response, Request, HTTPException, Query, status, Security
from fastapi.security import OAuth2PasswordRequestForm
from starlette.background import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession


from app.schemas.responses.api_schema_resp import APIResponse
from app.services.auth_services.dependencies import get_current_user
from app.database.models import User
from app.database.session import get_db
from app.schemas.responses.user_schema_resp import UserResponse
from app.schemas.requests.user_schema_req import UserCreate, ForgetPasswordRequest, ResetPasswordRequest
from app.schemas.responses.token_schema_resp import Token
from app.services.auth_services.auth import (
    signout, signup, authenticate_user, refresh_user, create_access_token, create_refresh_token,send_verification_email,
    reset_password, update_is_verified, update_user_password)

from config import ROLE_SCOPES

user_router = APIRouter(tags=['users'])

logger = getLogger(__name__)


auth_router = APIRouter(tags=["auth"])


@auth_router.post("/signup", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def register(
        background_tasks: BackgroundTasks,
        user_create: UserCreate,
        session: AsyncSession = Depends(get_db)
) -> APIResponse:
    user = await signup(session, user_create)

    await send_verification_email(background_tasks, user)

    return APIResponse(
        success=True,
        data=UserResponse.model_validate(user),
        message="Account created successfully! Check your inbox to verify your email",
    )


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login(
        form: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db),
        response: Response = None
) -> dict:

    if form.grant_type == "password":
        user = await authenticate_user(form.username, form.password, db)

    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported grant_type")

    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

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
async def refresh_access_token(
        request: Request = None,
        session: AsyncSession = Depends(get_db),
) -> APIResponse:
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token missing")

    user = await refresh_user(refresh_token, session)

    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized")

    base_scopes = ROLE_SCOPES.get(user.role.value, [])
    allowed_scopes = base_scopes.copy()
    if user.is_verified:
        allowed_scopes.append("user:verified")

    new_access_token = create_access_token(str(user.user_id), allowed_scopes)

    return APIResponse(
        success=True,
        data=Token(access_token=new_access_token, token_type="bearer").model_dump(exclude_unset=True),
        message="Access token refreshed"
    )


@auth_router.get("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(token: str = Query(...), session: AsyncSession = Depends(get_db)) -> APIResponse:
    user = await update_is_verified(token, session)

    full_scopes = ["user", "user:verified"]
    access_token = create_access_token(str(user.user_id), full_scopes)
    return APIResponse(
        success=True,
        data=Token(
            access_token=access_token,
            scopes=full_scopes,
            token_type="bearer"
        ).model_dump(exclude_unset=True),
        message="You successfully verified your email!"
    )


@auth_router.post("/forget-password", status_code=status.HTTP_200_OK, response_model=APIResponse)
async def forget_password(
        background_tasks: BackgroundTasks,
        fpr: ForgetPasswordRequest,
        session: AsyncSession = Depends(get_db)
) -> APIResponse:
    await reset_password(background_tasks, fpr.username, session)
    return APIResponse(
        success=True,
        message="Reset link was sent to your email"
    )


@auth_router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_user_password(
        request: ResetPasswordRequest,
        token: str = Query(...),
        session: AsyncSession = Depends(get_db)
) -> APIResponse:
    await update_user_password(request, token, session)

    return APIResponse(
        success=True,
        message="You successfully updated your password!"
    )


@auth_router.post("/sign-out", status_code=status.HTTP_200_OK)
async def logot(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> APIResponse:
    await signout(current_user, db)
    return APIResponse(
        success=True,
        message="You successfully logged out!"
    )
