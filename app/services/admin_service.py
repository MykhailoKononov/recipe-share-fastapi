from fastapi import HTTPException, status

from app.database.models import User, Role
from app.repository.admin_repo import AdminRepository


class AdminService:
    def __init__(self, repository: AdminRepository):
        self.repository = repository

    async def promote_to_moderator(self, current_user: User, username: str) -> User:
        if current_user.role != Role.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        user = await self.repository.get_active_user_by_username_or_email(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if current_user.role == user.role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Admin can't make himself a moderator")
        if user.role == Role.moderator:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a moderator")
        return await self.repository.promote_to_moderator(username)
