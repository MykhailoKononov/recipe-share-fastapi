from fastapi import HTTPException, status
from sqlalchemy import select

from app.database.models import User, Role
from app.repository.user_repo import UserRepository
from app.schemas.user_schema import UserUpdate, UserCreate
from app.services.auth_services.hashing import Hasher


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_user(self, current_user: User, username: str) -> User:
        if not username or username in {current_user.username, current_user.email}:
            return current_user
        if current_user.role == Role.user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        user = await self.repository.get_active_user_by_username(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if current_user.role == Role.moderator and user.role == Role.admin:
            raise HTTPException(status_code=403, detail="Access denied")
        return user

    async def update_user(self, current_user: User, username: str, user_update: UserUpdate) -> User:
        if not username or username in {current_user.username, current_user.email}:
            return await self.repository.update_user_by_username(
                username=current_user.username,
                **user_update.model_dump(exclude_unset=True)
            )
        if current_user.role == Role.user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        user = await self.repository.get_active_user_by_username(username=username)
        if not user:
            raise HTTPException(status_code=404, detail=f"User not found")
        if current_user.role == Role.moderator and user.role == Role.admin:
            raise HTTPException(status_code=403, detail="Access denied")
        updated_user = await self.repository.update_user_by_username(
            username=username,
            **user_update.model_dump(exclude_unset=True)
        )
        return updated_user

    async def delete_user(self, current_user: User, username: str):
        if not username or username in {current_user.username, current_user.email}:
            if current_user.role == Role.admin:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admin cannot delete himself")
            await self.repository.delete_user(current_user.username)
            return {"detail": "User was deleted successfully"}

        user = await self.repository.get_active_user_by_username(username)
        if not user:
            raise HTTPException(status_code=400, detail="User does not exist")

        if current_user.role == Role.user:
            raise HTTPException(status_code=403, detail="Access denied")

        if current_user.role == Role.moderator and user.role in {Role.admin, Role.moderator}:
            raise HTTPException(status_code=403, detail="Access denied")

        await self.repository.delete_user(username)
