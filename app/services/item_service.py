from sqlalchemy.orm import Session

from app.core.error_codes import ErrorCode
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.item import Item
from app.models.user import User
from app.repositories.item_repo import ItemRepository


class ItemService:
    def list_items(self, db: Session, offset: int = 0, limit: int = 100) -> tuple[list[Item], int]:
        return ItemRepository(db).list_with_count(offset=offset, limit=limit)

    def create_item(
        self,
        db: Session,
        title: str,
        description: str | None,
        owner_id: int,
    ) -> Item:
        return ItemRepository(db).create(
            title=title,
            description=description,
            owner_id=owner_id,
        )

    def update_item(
        self,
        db: Session,
        item_id: int,
        title: str | None,
        description: str | None,
        actor: User,
    ) -> Item:
        item_repo = ItemRepository(db)
        item = item_repo.get(item_id)
        if not item:
            raise NotFoundError("Item not found", code=ErrorCode.ITEM_NOT_FOUND)
        self._ensure_can_modify(item, actor)
        return item_repo.update(item, title=title, description=description)

    def delete_item(self, db: Session, item_id: int, actor: User) -> None:
        item_repo = ItemRepository(db)
        item = item_repo.get(item_id)
        if not item:
            return
        self._ensure_can_modify(item, actor)
        item_repo.delete(item)

    def _ensure_can_modify(self, item: Item, actor: User) -> None:
        if item.owner_id != actor.id and not actor.is_superuser:
            raise ForbiddenError("Not allowed")
