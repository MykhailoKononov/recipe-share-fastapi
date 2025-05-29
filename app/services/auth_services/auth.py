import datetime

import settings

from fastapi import status
from passlib.context import CryptContext
from typing import Union
from typing import Optional
from jose import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.repository.user_repo import UserRepository
from app.schemas.user_schema import UserCreate
from app.services.auth_services.hashing import Hasher
from app.database.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


def create_access_token(data: dict, expires_delta: Optional[float] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"iat": datetime.now(), "exp": expire, "scope": "access_token"})
    encoded_access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_access_token


def create_refresh_token(data: dict, expires_delta: Optional[float] = None):
    """
    Create a refresh token for a user.

    This function generates a JWT refresh token with a longer expiry time, typically used for renewing access tokens.

    :param data: A dictionary of data to encode in the token, typically including user information like email.
    :type data: dict
    :param expires_delta: Optional. Time in seconds before the token expires. Defaults to 7 days.
    :type expires_delta: Optional[float]
    :return: Encoded JWT refresh token.
    :rtype: str
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now() + timedelta(days=7)
    to_encode.update({"iat": datetime.now(), "exp": expire, "scope": "refresh_token"})
    encoded_refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_refresh_token


async def authenticate_user(session: AsyncSession, username: str, password: str) -> Union[User, False]:
    result = await session.execute(select(User).where(((User.email == username) | (User.username == username)) & (User.is_active==True)))
    user = result.scalars().first()
    if user is None or not Hasher.verify_password(password, user.hashed_password):
        return False
    return user


async def signup(db: AsyncSession, data: UserCreate) -> User:
    create_params = data.model_dump(exclude_unset=True)
    print(f"2: {create_params}")
    existing_email = await UserRepository(db).get_user_by_email(create_params["email"])
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")
    existing_username = await UserRepository(db).get_user_by_username(create_params["username"])
    if existing_username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this username already exists")
    print(f"3: {create_params}")
    return await UserRepository(db).create_user(create_params)


async def signin(username: str, password: str, session: AsyncSession) -> dict:
    user = await authenticate_user(session, username, password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    if not user.refresh_token:
        user.refresh_token = refresh_token
    try:
        await session.commit()
        await session.refresh(user)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


async def signout(current_user: User, session: AsyncSession) -> dict:
    current_user.refresh_token = None
    await session.commit()
    await session.refresh(current_user)
    return {"msg": "Successfully logged out"}
