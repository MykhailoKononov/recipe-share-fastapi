import uuid

from enum import StrEnum

from sqlalchemy import String, Date, Boolean, Text, ForeignKey, DateTime, func, Enum, Integer
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID


Base = declarative_base()


class Role(StrEnum):
    admin = "admin"
    moderator = "moderator"
    user = "user"


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(225), nullable=True)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    birthday: Mapped[Date] = mapped_column(Date, nullable=True)
    phone: Mapped[str] = mapped_column(String(14), nullable=True)
    role: Mapped[Role] = mapped_column(Enum(Role, name="role"), default=Role.user, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    about: Mapped[str] = mapped_column(Text, nullable=True)

    recipes = relationship("Recipe", back_populates="author")


class Recipe(Base):
    __tablename__ = "recipes"

    recipe_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[Text] = mapped_column(Text, nullable=True)
    image_url: Mapped[str] = mapped_column(String(255), nullable=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"))

    author = relationship("User", back_populates="recipes")
    ingredients = relationship("RecipeIngredient", back_populates="recipe")


class Ingredient(Base):
    __tablename__ = "ingredients"

    ingredient_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    recipe_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recipes.recipe_id"), primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(Integer, ForeignKey("ingredients.ingredient_id"), primary_key=True)
    quantity: Mapped[str] = mapped_column(String(50))

    recipe = relationship("Recipe", back_populates="ingredients")
