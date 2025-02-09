from sqlalchemy import select, update

from app.database.models import User, Role
from app.repository.moderator_repo import ModeratorRepository


class AdminRepository(ModeratorRepository):

    async def promote_to_moderator(self, username: str):
        try:
            promoted_user = await self.db.execute(update(User)
                                                  .where(((User.username == username) | (User.email == username)) &
                                                         (User.is_active == True))
                                                  .values(role=Role.moderator)
                                                  .returning(User))
            await self.db.commit()
            return promoted_user.scalars().first()
        except Exception as e:
            await self.handle_exception(e)
