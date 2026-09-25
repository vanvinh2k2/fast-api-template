from uuid import UUID

from pydantic import BaseModel

from app.schemas.base import ORMModel


class ItemBase(BaseModel):
    title: str
    description: str | None = None


class ItemResponse(ItemBase, ORMModel):
    id: UUID
    owner_id: UUID
