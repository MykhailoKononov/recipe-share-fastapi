from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, field_validator, EmailStr, model_validator
from starlette import status

from app.schemas.responses.user_schema_resp import LETTER_MATCH_PATTERN, PASSWORD_PATTERN


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
                detail="Password must contain at least 8 characters, including one uppercase letter, \
one lowercase letter and one digit."
            )
        return value

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_and_surname(cls, value: str):
        if value and not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Name and surname must contain only letters"
            )
        return value
