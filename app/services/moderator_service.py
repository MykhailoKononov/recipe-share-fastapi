from fastapi import HTTPException, status

from app.database.models import User, Role
from app.repository.moderator_repo import ModeratorRepository


class ModeratorService:
    def __init__(self, repository: ModeratorRepository):
        self.repository = repository

    async def retrieve_user(self, current_user: User, username: str) -> User:
        if current_user.role == Role.user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        existing_user = await self.repository.get_user_by_username(username)
        if current_user.role == Role.moderator == existing_user.role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Moderator can't retrieve other moderators")
        if not existing_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if existing_user.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You can't retrieve active user")
        return await self.repository.retrieve_user(username)
