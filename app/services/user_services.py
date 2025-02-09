from fastapi import HTTPException, status

from app.database.models import User, Role
from app.repository.user_repo import UserRepository
from app.schemas.user_schema import UserUpdate, UserCreate


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_account(self, create_params: UserCreate) -> User:
        dict_params = create_params.model_dump(exclude_unset=True)
        existing_username = await self.repository.get_user_by_username(dict_params["username"])
        if existing_username:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="User with this username already exists")
        existing_email = await self.repository.get_user_by_username(dict_params["email"])
        if existing_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="User with this username email exists")
        return await self.repository.create_user(dict_params)

    async def get_user_info(self, current_user: User, username: str) -> User:
        if not username or username in {current_user.username, current_user.email}:
            return current_user
        if current_user.role == Role.user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        user = await self.repository.get_active_user_by_username_or_email(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if current_user.role == Role.moderator and user.role == Role.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return user

    async def update_user(self, current_user: User, username: str, user_update: UserUpdate) -> User:
        dict_params = user_update.model_dump(exclude_unset=True)
        if not dict_params:
            raise HTTPException(status_code=400, detail="No fields provided for update")
        if not username or username in {current_user.username, current_user.email}:
            return await self.repository.update_active_user_by_username_or_email(current_user.username, dict_params)
        if current_user.role == Role.user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        user = await self.repository.get_active_user_by_username_or_email(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found")
        if current_user.role == Role.moderator and user.role == Role.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        updated_user = await self.repository.update_active_user_by_username_or_email(username, dict_params)
        return updated_user

    async def delete_user(self, current_user: User, username: str):
        if not username or username in {current_user.username, current_user.email}:
            if current_user.role == Role.admin:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admin cannot delete himself")
            await self.repository.delete_user(current_user.username)
            return {"detail": "User was deleted successfully"}

        user = await self.repository.get_active_user_by_username_or_email(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

        if current_user.role == Role.user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if current_user.role == Role.moderator and user.role in {Role.admin, Role.moderator}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        await self.repository.delete_user(username)
