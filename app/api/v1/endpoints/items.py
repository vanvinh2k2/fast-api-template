
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_dep
from app.models.item import Item
from app.repositories.item_repo import ItemRepository
from app.schemas.item import ItemCreate, ItemPublic, ItemUpdate

router = APIRouter()


@router.get("", response_model=list[ItemPublic])
def list_items(db: Session = Depends(get_db_dep)):
    repo = ItemRepository()
    return repo.list(db)


@router.post("", response_model=ItemPublic)
def create_item(
    item_in: ItemCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_dep),
):
    repo = ItemRepository()
    return repo.create(db, title=item_in.title, description=item_in.description, owner_id=current_user.id)


@router.put("/{item_id}", response_model=ItemPublic)
def update_item(
    item_id: int,
    item_in: ItemUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_dep),
):
    repo = ItemRepository()
    obj = repo.get(db, item_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    if obj.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return repo.update(db, obj, title=item_in.title, description=item_in.description)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_dep),
):
    repo = ItemRepository()
    obj = repo.get(db, item_id)
    if not obj:
        return
    if obj.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    repo.delete(db, obj)
    return
