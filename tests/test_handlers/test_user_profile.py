import pytest
from httpx import AsyncClient

from app.schemas.responses.user_schema_resp import UserResponse
from tests.conftest import create_test_auth_headers_for_user


@pytest.mark.asyncio
async def test_fetch_profile(client: AsyncClient, create_test_user, get_user_from_database):
    user = await create_test_user(with_refresh=True)
    headers = create_test_auth_headers_for_user(str(user.user_id), ["user"])

    response = await client.get("/profile/", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "User profile fetched"
    assert payload["data"] == UserResponse.model_validate(user).model_dump()


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, create_test_user, get_user_from_database):
    user = await create_test_user(with_refresh=True)
    headers = create_test_auth_headers_for_user(str(user.user_id), ["user"])

    response = await client.get("/profile/", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "User profile fetched"
    assert payload["data"] == UserResponse.model_validate(user).model_dump()