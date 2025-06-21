import uuid

from app.database.models import User
from config import Config
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import SecurityScopes
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.repository.user_repo import UserRepository
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    scopes={
        "user": "Read access",
        "user:verified": "Verified user access",
        "moderator": "Write access",
        "admin": "User verified email"
    },
)


async def get_current_user(
        security_scopes: SecurityScopes,
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_db)) -> User:
    if security_scopes.scopes:
        authenticate_value = f"Bearer scope=\"{security_scopes.scope_str}\""
    else:
        authenticate_value = f"Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
    except JWTError:
        raise credentials_exception
    token_scope = payload.get("scope")
    if token_scope != "access_token":
        raise credentials_exception
    user_id: uuid.UUID = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = await UserRepository(session).get_active_user_by_user_id(user_id)
    if user is None:
        raise credentials_exception

    token_scopes: List[str] = payload.get("scopes", [])

    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return user
