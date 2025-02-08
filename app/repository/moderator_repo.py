from fastapi import HTTPException, status
from sqlalchemy import select, update

from app.database.models import User
from app.repository.user_repo import UserRepository


class ModeratorRepository(UserRepository):

    async def get_user_by_username(self, username: str) -> User:
        """
        Gets user from database by email

        :param username: Entered username or email
        :return: User object.
        """
        try:
            user = await self.db.execute(select(User).where((User.email == username) | (User.username == username)))
            return user.scalars().first()
        except Exception as e:
            await self.handle_exception(e)

    async def retrieve_user(self, username: str) -> User:
        try:
            retrieved_user = await self.db.execute(update(User)
                                         .where((User.email == username) | (User.username == username))
                                         .values(is_active=True)
                                         .returning(User))
            await self.db.commit()
            return retrieved_user.scalars().first()
        except Exception as e:
            await self.handle_exception(e)

