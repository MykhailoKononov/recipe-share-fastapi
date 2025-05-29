import uuid

from app.database.models import Recipe
from app.repository.recipe_repo import RecipeRepository, IngredientRepository
from app.schemas.recipe_schema import RecipeCreate, IngredientSchema


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
        return new_recipe


class IngredientService:
    def __init__(self, repository: IngredientRepository):
        self.repository = repository

    async def get_or_create_ingredient(self, ingredients: list[IngredientSchema], new_recipe: Recipe):
        for ingredient in ingredients:
            name = ingredient.name.lower().strip()
            quantity = ingredient.quantity

            # Ищем ингредиент в базе или создаём новый
            ingredient_obj = await self.repository.get_or_create_ingredient(name)

            # Добавляем связь в recipe_ingredients
            await self.repository.add_ingredient_to_recipe(new_recipe.recipe_id, ingredient_obj.ingredient_id, quantity)



