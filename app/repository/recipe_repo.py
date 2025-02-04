import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Recipe


class RecipeRepository:
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

    async def create_recipe(self,
                            user_id: uuid.UUID,
                            image_url: Optional[str] = None,
                            **kwargs
                            ) -> Recipe:
        params = {key: value for key, value in kwargs.items() if value is not None}

        if not all(key in params for key in ["title", "ingredients"]):
            raise HTTPException(status_code=400, detail="Provide all required fields to create an account")

        try:
            db_recipe = Recipe(
                title=params["title"],
                description=params.get("description"),
                ingredients=params["ingredients"],
                image_url=image_url,
                user_id=user_id
            )

            self.db.add(db_recipe)
            await self.db.commit()
            await self.db.refresh(db_recipe)
            return db_recipe
        except Exception as e:
            await self.handle_exception(e)

