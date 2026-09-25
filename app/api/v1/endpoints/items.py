from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.deps import CurrentUser, ItemServiceDep
from app.core.exceptions import ForbiddenError, NotFoundError
from app.repositories.item_repo import ItemRepository
from app.schemas.base import ListParams, Page
from app.schemas.item import ItemBase, ItemResponse

router = APIRouter()


@router.get(
    "",
    response_model=Page[ItemResponse],
    openapi_extra={"parameters": ItemRepository.openapi_filter_parameters()},
)
def list_items(
    request: Request,
    params: Annotated[ListParams, Query()],
    current_user: CurrentUser,
    service: ItemServiceDep,
):
    try:
        items, count = service.list_items(
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
    payload: ItemBase,
    current_user: CurrentUser,
    service: ItemServiceDep,
):
    return service.create_item(
        title=payload.title,
        description=payload.description,
        owner_id=current_user.id,
    )


@router.get("/{id}", response_model=ItemResponse)
def get_item(
    id: UUID,
    current_user: CurrentUser,
    service: ItemServiceDep,
):
    try:
        return service.get_item(item_id=id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")


@router.put("/{id}", response_model=ItemResponse)
def update_item(
    id: UUID,
    payload: ItemBase,
    current_user: CurrentUser,
    service: ItemServiceDep,
):
    try:
        return service.update_item(
            item_id=id,
            title=payload.title,
            description=payload.description,
            actor=current_user,
        )
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    except ForbiddenError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    id: UUID,
    current_user: CurrentUser,
    service: ItemServiceDep,
):
    try:
        service.delete_item(item_id=id, actor=current_user)
    except ForbiddenError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return
