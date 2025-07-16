import pytest
from httpx import AsyncClient

from app.schemas.responses.recipe_schema_resp import RecipeResponse
from app.schemas.responses.user_schema_resp import UserResponse
from tests.conftest import create_test_auth_headers_for_user, image_file


@pytest.mark.asyncio
async def test_fetch_profile(client: AsyncClient, create_test_user):
    user = await create_test_user(with_refresh=True)
    headers = create_test_auth_headers_for_user(str(user.user_id), ["user"])

    response = await client.get("/profile/", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "User profile fetched"
    assert payload["data"] == UserResponse.model_validate(user).model_dump()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "expected_status", "expected_message", "expected_error"),
    [
        (
            {"first_name": "testA", "last_name": "testA", "birthday": "2000-01-01", "phone": "111", "about": "testA"},
            201,
            "Your profile data was updated successfully",
            None,

        ),
        (
            {"first_name": None, "last_name": None, "birthday": None, "phone": None, "about": None},
            201,
            "Your profile data was updated successfully",
            None
        ),
        (
            {},
            422,
            "Validation failed",
            ["body: Value error, at least one field must be provided"]
        ),
        (
            {"first_name": None, "birthday": "2000-01-01", "phone": "444"},
            201,
            "Your profile data was updated successfully",
            None
        ),
        (
            {"first_name": "Hello World", "birthday": "2000/01/01"},
            422,
            "Validation failed",
            ['first_name: Value error, must contain only letters',
             'birthday: Input should be a valid date or datetime, invalid date separator, expected `-`']
        )
    ]
)
async def test_update_profile(
        client: AsyncClient,
        create_test_user,
        get_user_from_database,
        payload,
        expected_status,
        expected_message,
        expected_error
):
    user = await create_test_user(with_refresh=True)
    headers = create_test_auth_headers_for_user(str(user.user_id), ["user"])

    response = await client.patch("/profile/update", json=payload, headers=headers)
    print(f"PRINT {response.json()}")
    payload = response.json()
    assert response.status_code == expected_status
    assert payload["message"] == expected_message

    if payload.get("data"):
        updated_user = await get_user_from_database(username=user.username)
        assert payload["data"] == UserResponse.model_validate(updated_user).model_dump(mode="json")

    assert payload["errors"] == expected_error


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "expected_status", "expected_errors"),
    [
        (
            {
                "title": "Test Title",
                "description": "Very tasty dish",
                "ingredients": [
                    {"name": "milk", "quantity": "test"},
                    {"name": "Milky Way", "quantity": "2132132132132"},
                    {"name": "@#$$%", "quantity": "q21343@#$##@"}
                ]
            },
            201,
            None
        ),
        (
            {
                "title": None,
                "ingredients": [
                    {"name": "milk", "quantity": None},
                    {"name": "Milky Way", "quantity": 2132132132132},
                    {"name": "@#$$%   ", "quantity": ""}
                ]
            },
            422,
            ['title: Input should be a valid string', 'ingredients.0.quantity: Input should be a valid string',
             'ingredients.1.quantity: Input should be a valid string']
        )
    ]
)
async def test_post_recipe(
        client: AsyncClient,
        get_recipe_from_database,
        create_test_user,
        payload,
        expected_status,
        expected_errors
):
    user = await create_test_user(with_refresh=True)
    headers = create_test_auth_headers_for_user(str(user.user_id), ["user", "user:verified"])

    response = await client.post("/profile/my-recipes/upload", json=payload, headers=headers)
    assert response.status_code == expected_status
    res = response.json()
    if expected_status == 201:
        recipe_id = res["data"]["recipe_id"]
        recipe = await get_recipe_from_database(recipe_id)
        assert res["data"] == RecipeResponse.model_validate(recipe).model_dump(mode="json")

    assert res["errors"] == expected_errors


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("files", "expected_status", "expected_message", "expected_error"),
    [
        (
            [("file", ("ok.jpeg", image_file("test_ok.jpeg"), "image/jpeg"))],
            201,
            "Recipe photo successfully updated",
            None
        ),
        (
            [("file", ("big.jpg", image_file("test_too_large.jpg"), "image/jpeg"))],
            413,
            "File upload error",
            ['Too large']
        ),
        (
            [("file", ("big.jpg", image_file("test_wrong_type.csv"), "text/csv"))],
            415,
            "File upload error",
            ["Unable to determine file type"]
        ),
    ]
)
async def test_fetch_profile(
        client: AsyncClient,
        create_test_user,
        create_test_recipe,
        get_recipe_from_database,
        files,
        expected_status,
        expected_message,
        expected_error
):
    user = await create_test_user(with_refresh=True)
    headers = create_test_auth_headers_for_user(str(user.user_id), ["user", "user:verified"])
    recipe = await create_test_recipe(user_id=user.user_id)

    params = {"recipe_id": recipe.recipe_id}
    response = await client.put("/profile/my-recipes/update-photo", params=params, files=files, headers=headers)
    print(f"PRINT {response.json()}")

    assert response.status_code == expected_status
    res = response.json()

    assert res["message"] == expected_message

    if res.get("data"):
        updated_recipe = await get_recipe_from_database(recipe.recipe_id)
        assert res["data"] == RecipeResponse.model_validate(updated_recipe).model_dump(mode="json")

    assert res["errors"] == expected_error
