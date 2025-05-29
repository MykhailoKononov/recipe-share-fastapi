import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Recipe, Ingredient, RecipeIngredient
from app.repository.user_repo import BaseRepository


class RecipeRepository(BaseRepository):

    async def create_recipe(self, user_id: uuid.UUID, data: dict, image_url: str) -> Recipe:
        try:
            db_recipe = Recipe(
                title=data["title"],
                description=data.get("description"),
                image_url=image_url,
                user_id=user_id
            )

            self.db.add(db_recipe)
            await self.db.commit()
            await self.db.refresh(db_recipe)
            return db_recipe
        except Exception as e:
            await self.handle_exception(e)


class IngredientRepository(BaseRepository):

    async def get_ingredient(self, name: str) -> Ingredient:
        try:
            clear_name = name.lower().strip()

            query = select(Ingredient).where(Ingredient.name == clear_name)
            result = await self.db.execute(query)
            ingredient = result.scalars().first()
            return ingredient
        except Exception as e:
            await self.handle_exception(e)

    async def create_ingredient(self, name: str) -> Ingredient:
        try:
            clear_name = name.lower().strip()

            ingredient = Ingredient(name=clear_name)
            self.db.add(ingredient)
            await self.db.commit()
            await self.db.refresh(ingredient)
            return ingredient
        except Exception as e:
            await self.handle_exception(e)

    async def get_or_create_ingredient(self, name: str):
        try:
            clear_name = name.lower().strip()

            query = select(Ingredient).where(Ingredient.name == clear_name)
            result = await self.db.execute(query)
            ingredient = result.scalars().first()

            if not ingredient:
                ingredient = Ingredient(name=name)
                self.db.add(ingredient)
                await self.db.commit()
                await self.db.refresh(ingredient)

            return ingredient
        except Exception as e:
            await self.handle_exception(e)

    async def add_ingredient_to_recipe(self, recipe_id: uuid.UUID, ingredient_id: int, quantity: str):
        try:
            recipe_ingredient = RecipeIngredient(
                recipe_id=recipe_id,
                ingredient_id=ingredient_id,
                quantity=quantity
            )
            self.db.add(recipe_ingredient)
            await self.db.commit()
        except Exception as e:
            await self.handle_exception(e)
