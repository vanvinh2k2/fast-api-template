from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_dep
from app.models.user import User
from app.schemas.item import ItemCreate, ItemPublic, ItemUpdate
from app.services.item_service import ItemNotFoundError, ItemPermissionError, ItemService

router = APIRouter()


@router.get("", response_model=list[ItemPublic])
def list_items(db: Session = Depends(get_db_dep)):
    service = ItemService()
    return service.list_items(db)


@router.post("", response_model=ItemPublic)
def create_item(
    item_in: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dep),
):
    service = ItemService()
    return service.create_item(
        db,
        title=item_in.title,
        description=item_in.description,
        owner_id=current_user.id,
    )


@router.put("/{item_id}", response_model=ItemPublic)
def update_item(
    item_id: int,
    item_in: ItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dep),
):
    service = ItemService()
    try:
        return service.update_item(
            db,
            item_id=item_id,
            title=item_in.title,
            description=item_in.description,
            actor=current_user,
        )
    except ItemNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    except ItemPermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dep),
):
    service = ItemService()
    try:
        service.delete_item(db, item_id=item_id, actor=current_user)
    except ItemPermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return
