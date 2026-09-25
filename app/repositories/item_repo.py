from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.user import User
from app.repositories.base import BaseRepository


class ItemRepository(BaseRepository[Item]):
    field_overrides = {
        "full_name": User.full_name,
    }
    search_fields = ("title", "full_name")
    filter_fields = ("title",)
    ordering_fields = ("id", "title", "full_name")

    def __init__(self, db: Session) -> None:
        super().__init__(db, Item)
