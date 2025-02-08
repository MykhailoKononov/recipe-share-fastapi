from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str | None = None
    last_name: str | None = None


class UserResponse(BaseModel):
    user_id: uuid.UUID
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


class UserSignIn(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserIsActive(BaseModel):
    email: EmailStr
    username: str
    is_active: bool
