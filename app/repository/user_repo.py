import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database.models import User

from app.services.auth_services.hashing import Hasher


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
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def create_user(self, **kwargs) -> User:
        """
        Creates a new user in the database.

        :param kwargs: user data
        :return: User object
        """
        try:
            create_params = {key: value for key, value in kwargs.items() if value is not None}
            if not all(key in create_params for key in ["username", "email", "password"]):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Provide all required fields to create an account")
            existing_user = await self.get_active_user_by_username(create_params["email"])
            if existing_user:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="User with this email or username already exists")
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

    async def get_active_user_by_id(self, user_id: uuid.UUID) -> User:
        """
        Gets user from database by id

        :param user_id: Entered user_id
        :return: User object.
        """
        try:
            user = await self.db.execute(select(User).where((User.user_id == user_id) & (User.is_active == True)))
            return user.scalars().first()
        except Exception as e:
            await self.handle_exception(e)

    async def get_active_user_by_username(self, username: str) -> User:
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

    async def update_user_by_username(self, username: str, **kwargs) -> User:
        """
        Allows to change user params not depending on nulls

        :param username: email or username of the user who's parameters aare going to be changed
        :param kwargs: parameters that need to be changed
        :return: User object with updated parameters
        """
        try:
            update_params = {key: value for key, value in kwargs.items() if value is not None}
            if not update_params:
                raise HTTPException(status_code=400, detail="No fields provided for update")
            updating_query = (update(User)
                              .where((User.email == username) | (User.username == username))
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
