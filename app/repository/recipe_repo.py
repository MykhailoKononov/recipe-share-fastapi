from typing import List, Sequence, Dict
import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

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

            self.session.add(db_recipe)
            await self.session.commit()
            await self.session.refresh(db_recipe)
            return db_recipe
        except Exception as e:
            await self.handle_exception(e)

    async def get_ingredients_by_name(self, names: List[str]) -> Sequence[Ingredient]:
        try:
            norm_names = [name.strip().lower() for name in names]

            if not norm_names:
                return []

            stmt = select(Ingredient).filter(Ingredient.name.in_(norm_names))

            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            await self.handle_exception(e)

    async def create_ingredients_bulk(self, names: list[str]) -> list[Ingredient]:
        try:
            ingredients = [Ingredient(name=name) for name in names]
            self.session.add_all(ingredients)
            await self.session.commit()
            for ing in ingredients:
                await self.session.refresh(ing)
            return ingredients

        except Exception as e:
            await self.handle_exception(e)

    async def add_ingredients_to_recipe(
            self,
            recipe_id: uuid.UUID,
            ingredients_map: Dict[int, str]
    ) -> list[RecipeIngredient]:
        try:
            recipe_ingredients = [
                RecipeIngredient(
                    recipe_id=recipe_id,
                    ingredient_id=ingredient_id,
                    quantity=quantity
                )
                for ingredient_id, quantity in ingredients_map.items()
            ]

            self.session.add_all(recipe_ingredients)
            await self.session.commit()

            return recipe_ingredients

        except Exception as e:
            await self.handle_exception(e)

    async def fetch_all_user_recipes(self, user_id: uuid.UUID) -> Sequence[Recipe]:
        try:
            stmt = (select(Recipe).
                    options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
                            selectinload(Recipe.author)).
                    where(Recipe.user_id == user_id)
                    )

            recipes = await self.session.execute(stmt)
            return recipes.scalars().all()

        except Exception as e:
            await self.handle_exception(e)
