import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database.models import User, Role
from app.services.auth_services.hashing import Hasher


class BaseRepository:
    def __init__(self, db: AsyncSession):
        """
        Initializes the repository with a database session.

        :param db: The database session to use for database operations.
        :type db: AsyncSession
        """
        self.db = db

    async def handle_exception(self, e: Exception):
        """
        Handles exceptions by printing the error message, rolling back the transaction, and raising an HTTPException.

        :param e: The exception to handle.
        :type e: Exception
        :raises HTTPException: Always raises an HTTPException with a 500 status code.
        """
        print(f"Database Error: {e}")
        await self.db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


class UserRepository(BaseRepository):

    async def create_user(self, create_params: dict) -> User:
        """
        Creates a new user in the database.

        :param create_params: user data
        :return: User object
        """
        try:
            create_params["hashed_password"] = Hasher.get_password_hash(create_params["password"])
            db_user = User(
                email=create_params["email"],
                username=create_params["username"],
                hashed_password=create_params["hashed_password"],
                first_name=create_params.get("first_name"),
                last_name=create_params.get("last_name")
            )
            self.db.add(db_user)
            await self.db.commit()
            await self.db.refresh(db_user)
            return db_user

        except Exception as e:
            await self.handle_exception(e)

    async def get_user_by_email(self, email: str) -> User:
        """
        Gets user from database by id

        :param email: Entered email
        :return: User object.
        """
        try:
            user = await self.db.execute(select(User).where(User.email == email))
            return user.scalars().first()
        except Exception as e:
            await self.handle_exception(e)

    async def get_user_by_username(self, username: str) -> User:
        """
        Gets user from database by id

        :param username: Entered user_id
        :return: User object.
        """
        try:
            user = await self.db.execute(select(User).where(User.username == username))
            return user.scalars().first()
        except Exception as e:
            await self.handle_exception(e)

    async def get_active_user_by_username_or_email(self, username: str) -> User:
        """
        Gets user from database by email

        :param username: Entered username or email
        :return: User object.
        """
        try:
            user = await self.db.execute(select(User).where(((User.email == username) | (User.username == username))
                                                            & (User.is_active == True)))
            return user.scalars().first()
        except Exception as e:
            await self.handle_exception(e)

    async def update_active_user_by_username_or_email(self, username: str, update_params: dict) -> User:
        """
        Allows to change user params not depending on nulls

        :param username: email or username of the user whose parameters are going to be changed
        :param update_params: parameters that need to be changed
        :return: User object with updated parameters
        """
        try:
            updating_query = (update(User)
                              .where(((User.email == username) | (User.username == username)) & User.is_active == True)
                              .values(**update_params)
                              .returning(User))
            updated_user = await self.db.execute(updating_query)
            await self.db.commit()
            return updated_user.scalars().first()
        except Exception as e:
            await self.handle_exception(e)

    async def delete_user(self, username: str) -> User:
        try:
            deleted_user = await self.db.execute(update(User)
                                                 .where((User.email == username) | (User.username == username))
                                                 .values(is_active=False, refresh_token=None)
                                                 .returning(User))
            await self.db.commit()
            return deleted_user.scalars().first()
        except Exception as e:
            await self.handle_exception(e)


class ModeratorRepository(UserRepository):

    async def get_user_by_username_or_email(self, username: str) -> User:
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
