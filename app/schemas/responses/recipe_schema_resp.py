from pydantic import BaseModel
from typing import Optional, List
import uuid


class IngredientSchema(BaseModel):
    name: str
    quantity: str

    class Config:
        from_attributes = True


class RecipeResponse(BaseModel):
    recipe_id: uuid.UUID
    title: str
    description: Optional[str] = None
    ingredients: List[IngredientSchema]
    image_url: Optional[str] = None
    user_id: uuid.UUID

    class Config:
        from_attributes = True
