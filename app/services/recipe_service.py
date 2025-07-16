import uuid
import filetype
import cloudinary
import cloudinary.uploader

from typing import Optional, IO
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Recipe, User
from app.repository.recipe_repo import RecipeRepository
from app.schemas.requests.recipe_schema_req import RecipeUpdate


class RecipeService:
    def __init__(self, repository: RecipeRepository):
        self.repository = repository

    async def update_recipe(self, recipe_id: uuid.UUID, payload: RecipeUpdate, current_user: User) -> Recipe:
        recipe = await self.repository.get_recipe_by_id(recipe_id)

        if not recipe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe does not exist")

        if recipe.user_id != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You can't modify others' recipes")

        if "title" in payload.model_fields_set and payload.title is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Title cannot be null"
            )

        if "ingredients" in payload.model_fields_set:
            if payload.ingredients is None or len(payload.ingredients) == 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Recipe must contain at least one ingredient"
                )

        simple_data = payload.model_dump(exclude_unset=True, exclude={"ingredients", "recipe_id"})
        for field, val in simple_data.items():
            setattr(recipe, field, val)

        if "ingredients" in payload.model_fields_set:
            await self.repository.update_ingredients(recipe, payload.ingredients)

        self.repository.session.add(recipe)
        await self.repository.session.commit()
        await self.repository.session.refresh(recipe)
        return recipe

    async def update_recipe_photo(
            self,
            recipe_id: uuid.UUID,
            file: Optional[UploadFile],
            current_user: User,
            session: AsyncSession
    ) -> (Recipe, str):
        recipe = await self.repository.get_recipe_by_id(recipe_id)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        if recipe.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="You can't modify others' recipes")

        if file:
            validate_file_size_type(file)
            file.file.seek(0)
            # Загружаем в Cloudinary
            print(file)
            result = cloudinary.uploader.upload(file.file)
            image_url = result["secure_url"]
            recipe.image_url = image_url
            action = "updated"
        else:
            # Удаляем фото
            recipe.image_url = None
            action = "removed"

        session.add(recipe)
        await session.commit()
        await session.refresh(recipe)
        return recipe, action


def validate_file_size_type(file: UploadFile):
    FILE_SIZE = 2097152  # 2MB

    accepted_file_types = ["image/png", "image/jpeg", "image/jpg", "image/heic", "image/heif", "image/heics", "png",
                           "jpeg", "jpg", "heic", "heif", "heics"
                           ]
    file_info = filetype.guess(file.file)
    if file_info is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unable to determine file type",
        )

    detected_content_type = file_info.extension.lower()

    if (
            file.content_type not in accepted_file_types
            or detected_content_type not in accepted_file_types
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type",
        )

    real_file_size = 0
    for chunk in file.file:
        real_file_size += len(chunk)
        if real_file_size > FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Too large")
