from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.session import get_db
from app.repository.user_repo import AdminRepository
from app.services.auth_services.dependencies import get_current_user
from app.services.admin_service import AdminService

admin_router = APIRouter(tags=["admin"])


@admin_router.patch("/give-moderator-privileges",
                    status_code=status.HTTP_200_OK)
async def grant_privileges(
        username: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)) -> dict:
    await AdminService(AdminRepository(db)).promote_to_moderator(current_user, username)
    return {"msg": f"User {username} was promoted to moderator"}
