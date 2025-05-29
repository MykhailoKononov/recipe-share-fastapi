import re

from fastapi import HTTPException, status

from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional

LETTER_MATCH_PATTERN = re.compile(r"^[а-яА-Яa-zA-Z\-]+$")
PASSWORD_PATTERN = re.compile(r"((?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,64})")


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str | None = None
    last_name: str | None = None

    @model_validator(mode="before")
    @classmethod
    def check_required_fields(cls, values):
        required_fields = ["email", "username", "password"]
        for field in required_fields:
            if field not in values or values[field] is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"{field.capitalize()} is required!"
                )
            return values

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None):
        if not PASSWORD_PATTERN.match(value):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password should contain at least 8 characters, including one uppercase letter, \
one lowercase letter and one digit."
            )
        return value

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_and_surname(cls, value: str):
        if value and not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Name should contain only letters"
            )
        return value


class UserResponse(BaseModel):
    email: EmailStr
    username: str
    first_name: str | None = None
    last_name: str | None = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birthday: Optional[str] = None
    phone: Optional[str] = None
    about: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_and_surname(cls, value: str):
        if not value and LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Name should contain only letters"
            )


class UserSignIn(BaseModel):
    email: EmailStr
    password: str


class UserIsActive(BaseModel):
    email: EmailStr
    username: str
    is_active: bool


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
