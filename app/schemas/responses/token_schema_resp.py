from typing import Optional, List

from pydantic import BaseModel


class Token(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    scopes: Optional[List[str]] = None
