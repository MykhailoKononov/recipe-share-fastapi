import json

from pydantic import BaseModel, model_validator
from typing import Optional, Dict
import uuid


class RecipeResponse(BaseModel):
    title: str
    description: Optional[str] = None
    ingredients: Dict[str, str]
    image_url: Optional[str] = None
    user_id: uuid.UUID


class RecipeCreate(BaseModel):
    title: str
    description: Optional[str] = None
    ingredients: dict[str, str]

    @model_validator(mode='before')
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value
