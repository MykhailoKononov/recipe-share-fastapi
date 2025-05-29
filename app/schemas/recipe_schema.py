import json

from pydantic import BaseModel, model_validator
from typing import Optional, Dict, List
import uuid


class IngredientSchema(BaseModel):
    name: str
    quantity: str


class RecipeCreate(BaseModel):
    title: str
    description: Optional[str] = None
    ingredients: List[IngredientSchema]

    @model_validator(mode='before')
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class RecipeResponse(BaseModel):
    title: str
    description: Optional[str] = None
    ingredients: List[IngredientSchema]
    image_url: Optional[str] = None
    user_id: uuid.UUID
