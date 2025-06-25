from pydantic import BaseModel
from typing import Any, Optional, List


class APIResponse(BaseModel):
    status: str
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None
