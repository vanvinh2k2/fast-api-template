from pydantic import BaseModel
from app.schemas.base import ORMModel


class ItemBase(BaseModel):
    title: str
    description: str | None = None


class ItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class ItemPublic(ItemBase, ORMModel):
    id: int
    owner_id: int
