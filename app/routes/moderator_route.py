from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.session import get_db
from app.repository.moderator_repo import ModeratorRepository
from app.schemas.user_schema import UserIsActive
from app.services.dependencies import get_current_user
from app.services.moderator_service import ModeratorService

moderator_router = APIRouter(tags=["moderator"])


@moderator_router.patch("/retrieve-user", response_model=UserIsActive, status_code=status.HTTP_201_CREATED)
async def retrieve_user(
        username: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)) -> UserIsActive:
    return await ModeratorService(ModeratorRepository(db)).retrieve_user(current_user, username)
