import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, get_user_from_database):
    payload = {"email": "test@user.com", "username": "user", "password": "Test1234", "first_name": "vova", "last_name": "bro"}

    # create account 1st try
    response = await client.post("/auth/signup", json=payload)
    assert response.status_code == 201

    # create account 2nd try with duplicated mail and username
    response_dup = await client.post("/auth/signup", json=payload)
    assert response_dup.status_code == 409

    # check if user is in database
    user = await get_user_from_database(email=payload["email"])
    assert user is not None
    assert user.email == payload["email"]
    assert user.username == payload["username"]
    assert user.is_active is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"username": "testuser", "password": "Test1234"},
        {"email": "test@test", "username": "testuser", "password": "Test1234"},
        {"email": "test@test.com", "username": "testuser", "password": "tes1234"},
        {"email": "test@test.com", "username": "testuser", "password": "Test1234", "first_name": "vova123"},
    ]
)
async def test_validation_create_user(client: AsyncClient, get_user_from_database, payload):
    response = await client.post("/auth/signup", json=payload)
    assert response.status_code == 422

    # check if user is in database
    user = await get_user_from_database(username=payload["username"])
    assert user is None


@pytest.mark.asyncio
async def test_login(client: AsyncClient, get_user_from_database):
    payload_signup = {
        "email": "test@user.com",
        "username": "user",
        "password": "Test1234",
        "first_name": "vova",
        "last_name": "bro"
    }

    response_signup = await client.post("/auth/signup", json=payload_signup)
    assert response_signup.status_code == 201

    payload_signin = {
        "grant_type": "password",
        "username": payload_signup["email"],
        "password": payload_signup["password"],
    }

    response_signin = await client.post("/auth/login", data=payload_signin)
    assert response_signin.status_code == 200
    assert response_signin.json()["access_token"]
    assert response_signin.json()["token_type"] == "bearer"

    user = await get_user_from_database(email=payload_signup["email"])
    assert user is not None
    assert user.refresh_token is not None
