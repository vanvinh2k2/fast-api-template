from collections.abc import Mapping

from uuid import UUID

from app.core.error_codes import ErrorCode
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.item import Item
from app.models.user import User
from app.repositories.item_repo import ItemRepository


class ItemService:
    def __init__(self, item_repo: ItemRepository) -> None:
        self.item_repo = item_repo

    def list_items(
        self,
        offset: int = 0,
        limit: int = 100,
        search: str | None = None,
        ordering: str | None = None,
        query_params: Mapping[str, str] | None = None,
    ) -> tuple[list[Item], int]:
        return self.item_repo.list_with_count(
            offset=offset,
            limit=limit,
            search=search,
            filters=self.item_repo.extract_filters(query_params or {}),
            ordering=ordering,
        )

    def create_item(
        self,
        title: str,
        description: str | None,
        owner_id: UUID,
    ) -> Item:
        return self.item_repo.create(
            title=title,
            description=description,
            owner_id=owner_id,
        )

    def get_item(self, item_id: UUID) -> Item:
        item = self.item_repo.get(item_id)
        if not item:
            raise NotFoundError("Item not found", code=ErrorCode.ITEM_NOT_FOUND)
        return item

    def update_item(
        self,
        item_id: UUID,
        title: str | None,
        description: str | None,
        actor: User,
    ) -> Item:
        item = self.item_repo.get(item_id)
        if not item:
            raise NotFoundError("Item not found", code=ErrorCode.ITEM_NOT_FOUND)
        self._ensure_can_modify(item, actor)
        return self.item_repo.update(item, title=title, description=description)

    def delete_item(self, item_id: UUID, actor: User) -> None:
        item = self.item_repo.get(item_id)
        if not item:
            return
        self._ensure_can_modify(item, actor)
        self.item_repo.delete(item)

    def _ensure_can_modify(self, item: Item, actor: User) -> None:
        if item.owner_id != actor.id and not actor.is_superuser:
            raise ForbiddenError("Not allowed")
