from collections.abc import Sequence
from typing import Annotated

from fastapi import Query
from starlette.datastructures import URL
from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )


class PageParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20
    offset: Annotated[int, Query(ge=0, description="Zero-based item offset")] = 0


class Page[T](ApiModel):
    count: int = Field(ge=0)
    next: str | None
    previous: str | None
    results: Sequence[T]

    @classmethod
    def create(cls, items: Sequence[T], count: int, params: PageParams, url: URL) -> "Page[T]":
        next_url = None
        next_offset = params.offset + params.limit
        if next_offset < count:
            next_url = str(url.include_query_params(limit=params.limit, offset=next_offset))

        previous_url = None
        if params.offset > 0:
            previous_offset = max(params.offset - params.limit, 0)
            previous_url = str(url.include_query_params(limit=params.limit, offset=previous_offset))

        return cls(
            count=count,
            next=next_url,
            previous=previous_url,
            results=items,
        )
