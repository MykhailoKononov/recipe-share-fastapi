from typing import List, Sequence, Dict, Optional
import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.database.models import Recipe, Ingredient, RecipeIngredient
from app.repository.user_repo import BaseRepository
from app.schemas.requests.recipe_schema_req import RecipeCreate
from app.schemas.responses.recipe_schema_resp import IngredientSchema


class RecipeRepository(BaseRepository):

    async def create_recipe(self, user_id: uuid.UUID, body: RecipeCreate) -> Recipe:
        try:
            db_recipe = Recipe(
                title=body.title,
                description=body.description,
                user_id=user_id
            )

            self.session.add(db_recipe)
            await self.session.flush()
            return await self.get_recipe_by_id(db_recipe.recipe_id)
        except Exception as e:
            await self.handle_exception(e)

    async def add_ingredients(
            self,
            recipe: Recipe,
            ingredients_data: List[IngredientSchema]
    ) -> None:
        for ing in ingredients_data:
            q = await self.session.execute(
                select(Ingredient).where(Ingredient.name == ing.name)
            )
            ingr_obj = q.scalar_one_or_none()
            if not ingr_obj:
                ingr_obj = Ingredient(name=ing.name)
                self.session.add(ingr_obj)
                await self.session.flush()
            recipe.ingredients.append(
                RecipeIngredient(ingredient=ingr_obj, quantity=ing.quantity)
            )

    async def get_recipe_by_id(self, recipe_id: uuid.UUID) -> Optional[Recipe]:
        try:
            stmt = (select(Recipe).options(
                selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
                selectinload(Recipe.author)
            ).where(Recipe.recipe_id == recipe_id)
                    )
            recipe = await self.session.execute(stmt)
            return recipe.scalar_one_or_none()
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

    async def update_ingredients(
            self,
            recipe: Recipe,
            new_ings: List[IngredientSchema]
    ) -> None:

        existing_map = {ri.name: ri for ri in recipe.ingredients}

        new_names = {ing.name for ing in new_ings}

        for name, ri in list(existing_map.items()):
            if name not in new_names:
                recipe.ingredients.remove(ri)

        for ing in new_ings:
            if ing.name in existing_map:
                existing_map[ing.name].quantity = ing.quantity
            else:
                q = await self.session.execute(
                    select(Ingredient).where(Ingredient.name == ing.name)
                )

                ingr_obj = q.scalar_one_or_none()
                if not ingr_obj:
                    ingr_obj = Ingredient(name=ing.name)
                    self.session.add(ingr_obj)
                    await self.session.flush()

                recipe.ingredients.append(
                    RecipeIngredient(ingredient=ingr_obj, quantity=ing.quantity)
                )
