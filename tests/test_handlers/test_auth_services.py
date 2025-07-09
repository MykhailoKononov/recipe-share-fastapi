import re

import pytest
from httpx import AsyncClient

from app.services.auth_services.auth import verify_token, create_email_verification_token, create_reset_password_token
from app.services.auth_services.hashing import Hasher
from app.services.auth_services.mail import fm
from config import Config
from tests.conftest import create_test_auth_headers_for_user


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, get_user_from_database):
    payload = {
        "email": "kononomisha@gmail.com",
        "username": "user",
        "password": "Test1234",
        "first_name": "vova",
        "last_name": "bro"
    }

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
async def test_signup_sends_email(monkeypatch, client, get_user_from_database):
    sent = {}

    async def fake_send_message(mes, *args, **kwargs):
        sent['message'] = mes
        sent['args'] = args
        sent['kwargs'] = kwargs

    monkeypatch.setattr(fm, "send_message", fake_send_message)

    body = {"username": "test", "email": "kononomisha@gmail.com", "password": "Secret1234"}
    response = await client.post("/auth/signup", json=body)
    assert response.status_code == 201

    assert 'message' in sent
    message = sent['message']

    assert message.recipients == [body["email"]]
    assert "Verify your email" in message.subject

    html = message.body
    pattern = re.compile(rf"{re.escape(Config.BACKEND_URL)}/auth/verify-email\?token=(?P<token>[\w\-_\.]+)")
    m = pattern.search(html)
    assert m
    token = m.group("token")

    user = await get_user_from_database(email=body["email"])
    assert verify_token(token) == str(user.user_id)


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
async def test_login(client: AsyncClient, create_test_user, get_user_from_database):
    user = await create_test_user()

    # sign in via email
    payload_signin_email = {
        "grant_type": "password",
        "username": user.email,
        "password": "Test1234",
    }

    # signin in username email
    payload_signin_username = {
        "grant_type": "password",
        "username": user.username,
        "password": "Test1234",
    }

    # assert response from login via email from body and cookies (to find tokens)
    response_signin_email = await client.post("/auth/login", data=payload_signin_email)
    response_signin_email_token = response_signin_email.cookies.get("refresh_token")
    assert response_signin_email_token is not None
    assert response_signin_email.status_code == 200
    assert response_signin_email.json()["access_token"]
    assert response_signin_email.json()["token_type"] == "bearer"

    # checking if we updated refresh token in DB
    user_email = await get_user_from_database(email=user.email)
    assert user_email.refresh_token is not None

    # assert response from login via username from body and cookies (to find tokens)
    response_signin_username = await client.post("/auth/login", data=payload_signin_username)
    assert response_signin_username.cookies.get("refresh_token") is not None
    assert response_signin_username.status_code == 200
    assert response_signin_username.json()["access_token"]
    assert response_signin_username.json()["token_type"] == "bearer"

    # checking if refresh token is not changed during all manipulations
    user_username = await get_user_from_database(username=user.username)
    assert user_username is not None
    assert user_username.refresh_token is not None
    assert user_username.refresh_token == response_signin_username.cookies.get("refresh_token")


@pytest.mark.asyncio
async def test_invalid_login(client: AsyncClient, get_user_from_database):
    payload_signup = {
        "email": "kononomisha@gmail.com",
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
        "password": "wrong_password",
    }

    response = await client.post("/auth/login", data=payload_signin)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

    user = await get_user_from_database(email=payload_signup["email"])
    assert user.refresh_token is None


@pytest.mark.asyncio
async def test_access_token(client: AsyncClient, get_user_from_database, create_test_user):
    test_user = await create_test_user(with_refresh=True)

    client.cookies.set("refresh_token", test_user.refresh_token)

    response = await client.post("/auth/token")
    assert response.status_code == 200
    assert response.json()["data"]["access_token"] is not None
    assert response.json()["data"]["token_type"] == "bearer"
    assert response.json()["message"] == "Access token refreshed"


@pytest.mark.asyncio
async def test_verify_email(client, create_test_user, get_user_from_database):
    user = await create_test_user()
    token = create_email_verification_token(str(user.user_id))

    params = {
        "token": token
    }

    response = await client.get("/auth/verify-email", params=params)
    assert response.status_code == 200
    assert response.json()["data"]["access_token"]
    assert response.json()["data"]["scopes"] == ["user", "user:verified"]
    assert response.json()["message"] == "You successfully verified your email!"

    db_user = await get_user_from_database(user_id=user.user_id)
    assert db_user.is_verified


@pytest.mark.asyncio
async def test_forgot_password(monkeypatch, client, create_test_user):
    user = await create_test_user()

    sent = {}

    async def fake_send_message(mes, *args, **kwargs):
        sent['message'] = mes
        sent['args'] = args
        sent['kwargs'] = kwargs

    monkeypatch.setattr(fm, "send_message", fake_send_message)

    response = await client.post("/auth/forget-password", json={"username": user.email})
    assert response.status_code == 200

    assert 'message' in sent
    message = sent['message']

    assert message.recipients == [user.email]
    assert "Password Reset Instructions" in message.subject

    reset_link: str = message.template_body["reset_link"]
    token = reset_link.split("?token=")[1]

    user_id = verify_token(token)
    assert str(user.user_id) == user_id


@pytest.mark.asyncio
async def test_reset_password(monkeypatch, client, create_test_user, get_user_from_database):
    user = await create_test_user()

    params = {"token": create_reset_password_token(str(user.user_id))}

    payload = {
        "password": "NewPassword1234",
        "confirm_password": "NewPassword1234"
    }

    response = await client.post("/auth/reset-password", params=params, json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "You successfully updated your password!"

    updated_user = await get_user_from_database(user_id=user.user_id)
    assert user.hashed_password != updated_user.hashed_password
    assert Hasher.verify_password(payload["password"], updated_user.hashed_password)


@pytest.mark.asyncio
async def test_signout(client, create_test_user, get_user_from_database):
    user = await create_test_user(with_refresh=True)
    headers = create_test_auth_headers_for_user(str(user.user_id))

    response = await client.post("/auth/sign-out", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "You successfully logged out!"

    logged_out_user = await get_user_from_database(user_id=user.user_id)
    assert logged_out_user.refresh_token is None
