import os
from typing import Optional

import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import APIRouter, UploadFile, status, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.session import get_db
from app.repository.recipe_repo import RecipeRepository
from app.schemas.recipe_schema import RecipeResponse, RecipeCreate
from app.services.auth_services.dependencies import get_current_user

recipe_router = APIRouter(tags=['recipes'])

cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("API_KEY"),
    api_secret=os.environ.get("API_SECRET"),
)


@recipe_router.post("/upload", status_code=status.HTTP_201_CREATED)
async def post_recipe(data: RecipeCreate = Body(...),
                      file: Optional[UploadFile | None] = None,
                      session: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)
                      ) -> RecipeResponse:
    if file:
        result = cloudinary.uploader.upload(file.file)
        image_url = result['secure_url']
    else:
        image_url = None

    return await RecipeRepository(session).create_recipe(
        current_user.user_id,
        image_url,
        **data.model_dump(exclude_unset=True)
    )
