from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.item import Item
from app.repositories.base import BaseRepository


class ItemRepository(BaseRepository[Item]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Item)

    def list(self, offset: int = 0, limit: int = 100) -> list[Item]:
        return super().list(offset=offset, limit=limit, order_by=Item.id.desc())

    def list_with_count(self, offset: int = 0, limit: int = 100) -> tuple[list[Item], int]:
        return self.list(offset=offset, limit=limit), self.count()

    def create(self, title: str, description: str | None, owner_id: int) -> Item:
        return super().create(title=title, description=description, owner_id=owner_id)

    def update(self, obj: Item, title: str | None, description: str | None) -> Item:
        if title is not None:
            obj.title = title
        if description is not None:
            obj.description = description
        return self.save(obj)
