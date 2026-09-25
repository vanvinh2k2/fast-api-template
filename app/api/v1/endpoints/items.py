from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_dep
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.user import User
from app.schemas.base import Page, PageParams
from app.schemas.item import ItemBase, ItemPublic, ItemUpdate
from app.services.item_service import ItemService

router = APIRouter()


@router.get("", response_model=Page[ItemPublic])
def list_items(
    request: Request,
    params: Annotated[PageParams, Query()],
    db: Session = Depends(get_db_dep),
):
    service = ItemService()
    items, count = service.list_items(db, offset=params.offset, limit=params.limit)
    return Page[ItemPublic].create(items, count, params, request.url)


@router.post("", response_model=ItemPublic, status_code=status.HTTP_201_CREATED)
def create_item(
    item_in: ItemBase,
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
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    except ForbiddenError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dep),
):
    service = ItemService()
    try:
        service.delete_item(db, item_id=item_id, actor=current_user)
    except ForbiddenError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return
