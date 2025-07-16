import uuid
import cloudinary
import cloudinary.uploader

from config import Config
from app.database.models import User
from app.database.session import get_db
from app.repository.recipe_repo import RecipeRepository
from app.repository.user_repo import UserRepository
from app.schemas.requests.recipe_schema_req import RecipeCreate, RecipeUpdate
from app.schemas.requests.user_schema_req import UserUpdate
from app.schemas.responses.api_schema_resp import APIResponse
from app.schemas.responses.recipe_schema_resp import RecipeResponse
from app.schemas.responses.user_schema_resp import UserResponse
from app.services.auth_services.dependencies import get_current_user
from app.services.recipe_service import RecipeService
from app.services.user_services import UserService

from typing import Optional
from fastapi import APIRouter, Security, Depends, status, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession

cloudinary.config(
    cloud_name=Config.CLOUD_NAME,
    api_key=Config.API_KEY,
    api_secret=Config.API_SECRET,
)

profile_router = APIRouter(tags=["profile"])


@profile_router.get("/", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def read_my_profile(current_user: User = Security(get_current_user, scopes=["user"])):
    """
    User can read information about his profile via this endpoint.
    It is protected with "user" scope in access token.
    """
    return APIResponse(
        success=True,
        data=UserResponse.model_validate(current_user),
        message="User profile fetched"
    )


@profile_router.patch("/update", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def update_user(
        user_update: UserUpdate,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> APIResponse:
    user = await UserService(UserRepository(session)).update_user(current_user, user_update)
    return APIResponse(
        success=True,
        data=UserResponse.model_validate(user),
        message="Your profile data was updated successfully"
    )


@profile_router.post("/my-recipes/upload", status_code=status.HTTP_201_CREATED)
async def post_recipe(
        body: RecipeCreate,
        session: AsyncSession = Depends(get_db),
        current_user: User = Security(get_current_user, scopes=["user", "user:verified"])
) -> APIResponse:

    recipe = await RecipeRepository(session).create_recipe(
        user_id=current_user.user_id,
        body=body
    )

    await RecipeRepository(session).add_ingredients(
        recipe=recipe,
        ingredients_data=body.ingredients,
    )

    await session.commit()

    return APIResponse(
        success=True,
        data=RecipeResponse.model_validate(recipe),
        message="Recipe created successfully"
    )


@profile_router.put("/my-recipes/update-photo", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def update_photo(
        file: Optional[UploadFile] = None,
        recipe_id: uuid.UUID = Query(...),
        session: AsyncSession = Depends(get_db),
        current_user: User = Security(get_current_user, scopes=["user", "user:verified"])
):
    recipe, action = await (RecipeService(RecipeRepository(session)).
                            update_recipe_photo(recipe_id, file, current_user, session))

    return APIResponse(
        success=True,
        message=f"Recipe photo successfully {action}",
        data=RecipeResponse.model_validate(recipe)
    )


@profile_router.get("/my-recipes", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def read_my_recipes(
        current_user: User = Security(get_current_user, scopes=["user"]),
        session: AsyncSession = Depends(get_db)
) -> APIResponse:
    recipes = await RecipeRepository(session).fetch_all_user_recipes(current_user.user_id)
    data = [RecipeResponse.model_validate(r) for r in recipes]
    return APIResponse(
        success=True,
        data=data,
        message="User recipes fetched",
    )


@profile_router.patch("/my-recipes/update", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def update_recipe(
        recipe_update: RecipeUpdate,
        recipe_id: uuid.UUID = Query(...),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> APIResponse:

    updated_recipe = await (RecipeService(RecipeRepository(session)).
                            update_recipe(recipe_id, recipe_update, current_user))

    return APIResponse(
        success=True,
        data=RecipeResponse.model_validate(updated_recipe),
        message="Recipe was updated successfully"
    )
