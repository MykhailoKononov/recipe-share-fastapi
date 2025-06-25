import re
from datetime import datetime, date
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, field_validator, EmailStr, model_validator
from starlette import status

from app.schemas.responses.user_schema_resp import LETTER_MATCH_PATTERN, PASSWORD_PATTERN


DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birthday: Optional[str] = None
    phone: Optional[str] = None
    about: Optional[str] = None

    @model_validator(mode="before")
    def at_least_one_field(cls, values):
        if not values or all(v is None for v in values.values()):
            raise ValueError("at least one field must be provided")
        return values

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_and_surname(cls, value: str):
        if not LETTER_MATCH_PATTERN.match(value):
            raise ValueError("must contain only letters")

    @field_validator("birthday")
    @classmethod
    def validate_birthday_format(cls, v):
        if v is None:
            return v
        if not DATE_PATTERN.match(v):
            raise ValueError("Must be in YYYY-MM-DD format")
        try:
            parsed = datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date")

        today = date.today()
        if parsed >= today:
            raise ValueError("Birthday must be before today")

        return v


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
                raise ValueError(f"{field.capitalize()} is required!")
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
