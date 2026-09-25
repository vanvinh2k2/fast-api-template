from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_dep
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.user import User
from app.repositories.item_repo import ItemRepository
from app.schemas.base import ListParams, Page
from app.schemas.item import ItemBase, ItemResponse
from app.services.item_service import ItemService

router = APIRouter()


@router.get(
    "",
    response_model=Page[ItemResponse],
    openapi_extra={"parameters": ItemRepository.openapi_filter_parameters()},
)
def list_items(
    request: Request,
    params: Annotated[ListParams, Query()],
    db: Session = Depends(get_db_dep),
):
    service = ItemService()
    try:
        items, count = service.list_items(
            db,
            offset=params.offset,
            limit=params.limit,
            search=params.search,
            ordering=params.ordering,
            query_params=request.query_params,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return Page[ItemResponse].create(items, count, params, request.url)


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
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


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: UUID,
    item_in: ItemBase,
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
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_dep),
):
    service = ItemService()
    try:
        service.delete_item(db, item_id=item_id, actor=current_user)
    except ForbiddenError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return
