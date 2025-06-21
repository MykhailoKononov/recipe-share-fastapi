from typing import Dict
import uuid

from app.database.models import Recipe, Ingredient
from app.repository.recipe_repo import RecipeRepository
from app.schemas.responses.recipe_schema_resp import IngredientSchema, RecipeResponse
from app.schemas.requests.recipe_schema_req import RecipeCreate


class RecipeService:
    def __init__(self, repository: RecipeRepository):
        self.repository = repository

    async def create_recipe(self, user_id: uuid.UUID, body: RecipeCreate, image_url: str) -> Recipe:
        data = body.model_dump(exclude_unset=True)
        new_recipe = await self.repository.create_recipe(
            user_id=user_id,
            data=data,
            image_url=image_url
        )
        await self.repository.session.commit()
        await self.repository.session.refresh(new_recipe)
        return new_recipe

    async def add_ingredients(
            self,
            new_recipe: Recipe,
            ingredients_data: list[IngredientSchema]
    ) -> dict[Ingredient, str]:

        names = [ing.name for ing in ingredients_data]
        quantities_map: Dict[str, str] = {ing.name: ing.quantity for ing in ingredients_data}

        existing_ings = await self.repository.get_ingredients_by_name(names)
        existing_names = [ing.name for ing in existing_ings]

        to_create = [name for name in names if name not in existing_names]

        new_ings = []
        if to_create:
            new_ings = await self.repository.create_ingredients_bulk(to_create)

        all_ings = list(existing_ings) + new_ings

        all_ings_map = {ing.ingredient_id: quantities_map[ing.name] for ing in all_ings}
        ings_to_return = {ing: quantities_map[ing.name] for ing in all_ings}

        await self.repository.add_ingredients_to_recipe(
            recipe_id=new_recipe.recipe_id,
            ingredients_map=all_ings_map
        )

        await self.repository.session.commit()
        return ings_to_return

    async def get_user_recipes(self, user_id: uuid.UUID):
        recipes = await self.repository.fetch_all_user_recipes(user_id)

        recipe_responses: list[RecipeResponse] = []
        for recipe in recipes:
            ingr_list = []
            for ri in recipe.ingredients:
                ingr_list.append({
                    "name": ri.ingredient.name,
                    "quantity": ri.quantity
                })

            recipe_responses.append(
                RecipeResponse(
                    recipe_id=recipe.recipe_id,
                    title=recipe.title,
                    description=recipe.description,
                    ingredients=ingr_list,
                    image_url=recipe.image_url,
                    user_id=recipe.user_id
                )
            )
        return recipe_responses

