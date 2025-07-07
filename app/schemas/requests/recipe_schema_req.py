import json
import uuid
from typing import Optional, List

from pydantic import BaseModel, model_validator

from app.schemas.responses.recipe_schema_resp import IngredientSchema


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


class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[IngredientSchema]] = None
