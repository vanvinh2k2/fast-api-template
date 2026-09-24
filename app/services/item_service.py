from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.user import User
from app.repositories.item_repo import ItemRepository


class ItemNotFoundError(Exception):
    pass


class ItemPermissionError(Exception):
    pass


class ItemService:
    def __init__(self, item_repo: ItemRepository | None = None) -> None:
        self.item_repo = item_repo or ItemRepository()

    def list_items(self, db: Session) -> list[Item]:
        return self.item_repo.list(db)

    def create_item(
        self,
        db: Session,
        *,
        title: str,
        description: str | None,
        owner_id: int,
    ) -> Item:
        return self.item_repo.create(
            db,
            title=title,
            description=description,
            owner_id=owner_id,
        )

    def update_item(
        self,
        db: Session,
        *,
        item_id: int,
        title: str | None,
        description: str | None,
        actor: User,
    ) -> Item:
        item = self.item_repo.get(db, item_id)
        if not item:
            raise ItemNotFoundError
        self._ensure_can_modify(item, actor)
        return self.item_repo.update(db, item, title=title, description=description)

    def delete_item(self, db: Session, *, item_id: int, actor: User) -> None:
        item = self.item_repo.get(db, item_id)
        if not item:
            return
        self._ensure_can_modify(item, actor)
        self.item_repo.delete(db, item)

    def _ensure_can_modify(self, item: Item, actor: User) -> None:
        if item.owner_id != actor.id and not actor.is_superuser:
            raise ItemPermissionError
