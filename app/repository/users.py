import uuid
from typing import Sequence

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from app.database.models import User
from asyncpg.exceptions import UniqueViolationError


class UserRepository:
    def __init__(self, db: AsyncSession):
        """
        Initializes the repository with a database session.

        :param db: The database session to use for database operations.
        :type db: AsyncSession
        """
        self.db = db

    async def handle_exception(self, e):
        """
        Handles exceptions by printing the error message, rolling back the transaction, and raising an HTTPException.

        :param e: The exception to handle.
        :type e: Exception
        :raises HTTPException: Always raises an HTTPException with a 500 status code.
        """
        print(f"Error: {e}")
        await self.db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

    async def create_user(self, username: str, email: str) -> User:
        """
        Creates a new comment for a post.

        :param username: Wanted username.
        :param email: Wanted email.
        :return: The created User object.
        """
        try:
            db_user = User(
                username=username,
                email=email,
            )
            self.db.add(db_user)
            await self.db.commit()
            await self.db.refresh(db_user)
            return db_user
        except Exception as e:
            await self.handle_exception(e)

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        """
        Gets user from database by id

        :param user_id: Entered user_id
        :return: User object.
        """
        try:
            user = await self.db.execute(select(User).where(User.user_id == user_id))
            return user.scalars().first()
        except Exception as e:
            await self.handle_exception(e)

    async def update_user_by_id(self, user_id: uuid.UUID, **kwargs) -> User:
        """
        Allows to change user params not depending on nulls

        :param user_id: takes the value of user_id who is going to be changed
        :param kwargs: parameters that need to be changed
        :return: User object with updated parameters
        """
        try:
            update_params = {key: value for key, value in kwargs.items() if value is not None}
            if not update_params:
                raise HTTPException(status_code=400, detail="No fields provided for update")
            updating_query = (update(User).where(User.user_id == user_id).values(**update_params).returning(User))
            result = await self.db.execute(updating_query)
            await self.db.commit()
            updated_user = result.scalars().first()
            return updated_user
        except Exception as e:
            await self.handle_exception(e)

    async def delete_user(self, user_id: uuid.UUID) -> User:
        try:
            deleted_user = await self.db.execute(update(User)
                                                 .where(User.user_id == user_id)
                                                 .values(is_active=False)
                                                 .returning(User))
            await self.db.commit()
            return deleted_user.scalars().first()
        except Exception as e:
            await self.handle_exception(e)
