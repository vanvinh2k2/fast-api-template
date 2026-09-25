from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.user import User
from app.repositories.base import BaseRepository


class ItemRepository(BaseRepository[Item]):
    related_fields = {
        "owner": (User, Item.owner_id == User.id),
    }
    field_overrides = {
        "full_name": User.full_name,
    }
    search_fields = ("title", "full_name")
    filter_fields = ("title",)
    ordering_fields = ("id", "title", "full_name")

    def __init__(self, db: Session) -> None:
        super().__init__(db, Item)

    def list(
        self,
        offset: int = 0,
        limit: int = 100,
        search: str | None = None,
        filters: Mapping[str, Any] | None = None,
        ordering: str | None = None,
    ) -> list[Item]:
        return self.list_filtered(
            offset=offset,
            limit=limit,
            search=search,
            filters=filters,
            ordering=ordering,
        )

    def list_with_count(
        self,
        offset: int = 0,
        limit: int = 100,
        search: str | None = None,
        filters: Mapping[str, Any] | None = None,
        ordering: str | None = None,
    ) -> tuple[list[Item], int]:
        return self.list_with_count_filtered(
            offset=offset,
            limit=limit,
            search=search,
            filters=filters,
            ordering=ordering,
        )

    def count(
        self,
        search: str | None = None,
        filters: Mapping[str, Any] | None = None,
        ordering: str | None = None,
    ) -> int:
        return self.count_filtered(
            search=search,
            filters=filters,
            ordering=ordering,
        )

    def create(self, title: str, description: str | None, owner_id: UUID) -> Item:
        return super().create(title=title, description=description, owner_id=owner_id)

    def update(self, obj: Item, title: str | None, description: str | None) -> Item:
        if title is not None:
            obj.title = title
        if description is not None:
            obj.description = description
        return self.save(obj)
