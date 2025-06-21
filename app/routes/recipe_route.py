import os
from typing import Optional, List

import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import APIRouter, UploadFile, Security, status, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.session import get_db
from app.repository.recipe_repo import RecipeRepository
from app.schemas.responses.recipe_schema_resp import RecipeResponse
from app.schemas.requests.recipe_schema_req import RecipeCreate
from app.services.auth_services.dependencies import get_current_user
from app.services.recipe_service import RecipeService

recipe_router = APIRouter(tags=['recipes'])

cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("API_KEY"),
    api_secret=os.environ.get("API_SECRET"),
)


@recipe_router.post("/upload", status_code=status.HTTP_201_CREATED)
async def post_recipe(body: RecipeCreate = Body(...),
                      file: Optional[UploadFile] = None,
                      session: AsyncSession = Depends(get_db),
                      current_user: User = Security(get_current_user, scopes=["user", "user:verified"])
                      ) -> RecipeResponse:
    image_url = None
    if file:
        result = cloudinary.uploader.upload(file.file)
        image_url = result['secure_url']

    new_recipe = await RecipeService(RecipeRepository(session)).create_recipe(
        user_id=current_user.user_id,
        body=body,
        image_url=image_url
    )

    ingredients = await RecipeService(RecipeRepository(session)).add_ingredients(
        new_recipe=new_recipe,
        ingredients_data=body.ingredients,
    )

    return RecipeResponse(
        recipe_id=new_recipe.recipe_id,
        title=new_recipe.title,
        description=new_recipe.description,
        ingredients=[{"name": ing.name, "quantity": quantity} for ing, quantity in ingredients.items()],
        image_url=new_recipe.image_url,
        user_id=new_recipe.user_id
    )


@recipe_router.get("/feed", status_code=status.HTTP_200_OK)
async def show_feed() -> List[RecipeResponse]:
    pass
