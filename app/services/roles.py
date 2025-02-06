from typing import Optional, Union

from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, Role
from app.repository.user_repo import UserRepository


def check_access(current_user: User,
                 target_username: Optional[EmailStr | str] = None
                 ) -> bool:
    if target_username is None or current_user.username == target_username or current_user.email == target_username:
        return True

    if current_user.role == Role.user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return False

