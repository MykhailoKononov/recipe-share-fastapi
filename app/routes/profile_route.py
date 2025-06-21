from fastapi import APIRouter, Security, Depends, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.session import get_db
from app.repository.recipe_repo import RecipeRepository
from app.repository.user_repo import UserRepository
from app.schemas.requests.user_schema_req import UserUpdate
from app.schemas.responses.api_schema_resp import APIResponse
from app.schemas.responses.user_schema_resp import UserResponse
from app.services.auth_services.dependencies import get_current_user
from app.services.recipe_service import RecipeService
from app.services.user_services import UserService

profile_router = APIRouter(tags=["profile"])


@profile_router.get("/", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def read_my_profile(current_user: User = Security(get_current_user, scopes=["user"])):
    """
    User can read information about his profile via this endpoint.
    It is protected with "user" scope in access token.
    """
    return APIResponse(
        success=True,
        message="User profile fetched",
        data=UserResponse.model_validate(current_user)
    )


@profile_router.patch("/update-profile", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def update_user(
        user_update: UserUpdate,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> UserResponse:
    return await UserService(UserRepository(session)).update_user(current_user, user_update)


@profile_router.get("/my-recipes", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def read_my_recipes(
        current_user: User = Security(get_current_user, scopes=["user"]),
        session: AsyncSession = Depends(get_db)
) -> APIResponse:
    """
    Get current user's recipes
    """
    recipe_responses = await RecipeService(RecipeRepository(session)).get_user_recipes(current_user.user_id)

    return APIResponse(
        success=True,
        message="User recipes fetched",
        data=recipe_responses,
    )

