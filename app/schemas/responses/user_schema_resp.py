import datetime
import re

from pydantic import BaseModel, EmailStr

LETTER_MATCH_PATTERN = re.compile(r"^[а-яА-Яa-zA-Z\-]+$")
PASSWORD_PATTERN = re.compile(r"((?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,64})")


class UserResponse(BaseModel):
    email: EmailStr
    username: str
    first_name: str | None = None
    last_name: str | None = None
    birthday: datetime.date | None = None
    phone: str | None = None
    about: str | None = None

    class Config:
        from_attributes = True


class UserIsActive(BaseModel):
    email: EmailStr
    username: str
    is_active: bool
