import os
from typing import Optional, List

import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import APIRouter, UploadFile, status, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.session import get_db
from app.repository.recipe_repo import RecipeRepository, IngredientRepository
from app.schemas.recipe_schema import RecipeResponse, RecipeCreate
from app.services.auth_services.dependencies import get_current_user
from app.services.recipe_service import RecipeService, IngredientService

recipe_router = APIRouter(tags=['recipes'])

cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("API_KEY"),
    api_secret=os.environ.get("API_SECRET"),
)


@recipe_router.post("/upload", status_code=status.HTTP_201_CREATED)
async def post_recipe(body: RecipeCreate = Body(...),
                      file: Optional[UploadFile | None] = None,
                      db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)
                      ) -> RecipeResponse:
    image_url = None
    if file:
        result = cloudinary.uploader.upload(file.file)
        image_url = result['secure_url']

    new_recipe = await RecipeService(RecipeRepository(db)).create_recipe(
        user_id=current_user.user_id,
        body=body,
        image_url=image_url
    )

    await IngredientService(IngredientRepository(db)).get_or_create_ingredient(
        ingredients=body.ingredients,
        new_recipe=new_recipe
    )

    return RecipeResponse(
        recipe_id=new_recipe.recipe_id,
        title=new_recipe.title,
        description=new_recipe.description,
        image_url=new_recipe.image_url,
        ingredients=[{"name": ing.name, "quantity": ing.quantity} for ing in new_recipe.ingredients]
    )


@recipe_router.get("/feed", status_code=status.HTTP_200_OK)
async def show_feed() -> List[RecipeResponse]:
    pass
