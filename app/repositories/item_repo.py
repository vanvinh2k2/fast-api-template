
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.item import Item


class ItemRepository:
    def list(self, db: Session) -> List[Item]:
        return db.query(Item).order_by(Item.id.desc()).all()

    def get(self, db: Session, item_id: int) -> Optional[Item]:
        return db.query(Item).filter(Item.id == item_id).first()

    def create(self, db: Session, *, title: str, description: str | None, owner_id: int) -> Item:
        obj = Item(title=title, description=description, owner_id=owner_id)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, obj: Item, *, title: str | None, description: str | None) -> Item:
        if title is not None:
            obj.title = title
        if description is not None:
            obj.description = description
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, obj: Item) -> None:
        db.delete(obj)
        db.commit()
