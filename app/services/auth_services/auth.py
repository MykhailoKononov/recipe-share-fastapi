import datetime
import uuid

from fastapi_mail import MessageSchema, MessageType

from app.services.auth_services.mail import fm
from config import Config

from fastapi import status
from starlette.background import BackgroundTasks
from passlib.context import CryptContext
from typing import Optional, List
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.user_repo import UserRepository
from app.schemas.requests.user_schema_req import UserCreate, ResetPasswordRequest
from app.services.auth_services.hashing import Hasher
from app.database.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(data: dict, expires_delta: timedelta, scope: str) -> str:

    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update(
        {"iat": datetime.now(),
         "exp": expire,
         "scope": scope}
    )
    return jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)


def create_access_token(user_id: str, scopes: List[str]) -> str:

    return create_token(
        data={"sub": user_id, "scopes": scopes},
        expires_delta=timedelta(minutes=Config.ACCESS_TOKEN_EXPIRES_MINUTES),
        scope="access_token",
    )


def create_refresh_token(user_id: str):

    return create_token(
        data={"sub": user_id},
        expires_delta=timedelta(days=Config.REFRESH_TOKEN_EXPIRES_DAYS),
        scope="refresh_token",
    )


def create_email_verification_token(user_id: str):

    return create_token(
        data={"sub": user_id},
        expires_delta=timedelta(days=1),
        scope="email_verification",
    )


def create_reset_password_token(user_id: str):
    return create_token(
        data={"sub": user_id},
        expires_delta=timedelta(minutes=30),
        scope="password_reset",
    )


async def authenticate_user(username: str, password: str, db: AsyncSession) -> Optional[User]:

    user = await UserRepository(db).get_active_user_by_username_or_email(username)
    if not user or not Hasher.verify_password(password, user.hashed_password):
        return None
    return user


async def refresh_user(refresh_token: str, session: AsyncSession,) -> Optional[User]:
    try:
        payload = jwt.decode(refresh_token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        if payload.get("scope") != "refresh_token":
            return None
        user_id = payload.get("sub")
    except JWTError:
        return None
    user = await UserRepository(session).get_active_user_by_user_id(user_id)
    if not user or user.refresh_token != refresh_token:
        return None
    return user


async def signup(session: AsyncSession, data: UserCreate) -> User:
    create_params = data.model_dump(exclude_unset=True)
    existing_email = await UserRepository(session).get_user_by_email(create_params["email"])
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")
    existing_username = await UserRepository(session).get_user_by_username(create_params["username"])
    if existing_username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this username already exists")
    user = await UserRepository(session).create_user(create_params)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    return user


async def send_verification_email(current_user: User):
    if current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You're already verified!")

    email_token = create_email_verification_token(str(current_user.user_id))
    verify_link = f"{Config.BACKEND_URL}/auth/verify-email?token={email_token}"

    body = f"""
        <h1>Verify your email</h1>
        <p>Please click this <a href="http://{verify_link}">link</a> to verify your email</p>
        """

    message = MessageSchema(
        recipients=[current_user.email],
        subject="Verify your email",
        body=body
    )

    fm.send_message(message)


def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wrong or outdated token")

    if payload.get("scope") not in ("email_verification", "password_reset"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wrong token type")

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="There was no user_id provided in token")

    return user_id


async def update_is_verified(token: str, session: AsyncSession):
    user_id = verify_token(token)
    user = await UserRepository(session).get_active_user_by_user_id(uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is verified already")

    user.is_verified = True
    await session.commit()
    await session.refresh(user)
    return user


async def update_user_password(request: ResetPasswordRequest, session: AsyncSession):
    user_id = verify_token(request.token)
    user = await UserRepository(session).get_active_user_by_user_id(uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    hashed_pass = Hasher.get_password_hash(request.password)
    user.hashed_password = hashed_pass
    await session.commit()
    await session.refresh(user)
    return user


async def reset_password(background_tasks: BackgroundTasks, username: str, session: AsyncSession) -> str:
    user = await UserRepository(session).get_active_user_by_username_or_email(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    token = create_reset_password_token(str(user.user_id))
    forget_url_link = f"https://localhost:8000/reset-password/{token}"

    email_body = {"company_name": Config.MAIL_FROM_NAME,
                  "link_expiry_min": Config.FORGET_PASSWORD_LINK_EXPIRE_MINUTES,
                  "reset_link": forget_url_link}

    message = MessageSchema(
        subject="Password Reset Instructions",
        recipients=[user.email],
        template_body=email_body,
        subtype=MessageType.html
    )

    background_tasks.add_task(fm.send_message, message, "password_reset.html")
    return forget_url_link


async def signout(current_user: User, session: AsyncSession) -> dict:
    current_user.refresh_token = None
    await session.commit()
    await session.refresh(current_user)
    return {"msg": "Successfully logged out"}
