from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar, Generic, TypeVar, get_args, get_origin
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    list_param_names: ClassVar[set[str]] = {"limit", "offset", "search", "ordering"}
    model: ClassVar[type[Any]]
    related_fields: ClassVar[Mapping[str, tuple[type[Any], ColumnElement[bool]]]] = {}
    field_overrides: ClassVar[Mapping[str, ColumnElement[Any]]] = {}
    search_fields: ClassVar[tuple[str, ...]] = ()
    filter_fields: ClassVar[tuple[str, ...]] = ()
    ordering_fields: ClassVar[tuple[str, ...]] = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        for base in getattr(cls, "__orig_bases__", ()):
            if get_origin(base) is BaseRepository:
                cls.model = get_args(base)[0]
                break

    def __init__(self, db: Session, model: type[ModelT]) -> None:
        self.db = db
        self.model = model

    def get(self, obj_id: UUID) -> ModelT | None:
        return self.db.get(self.model, obj_id)

    def count(self) -> int:
        return self.db.scalar(select(func.count()).select_from(self.model)) or 0

    def count_filtered(
        self,
        *,
        search: str | None = None,
        filters: Mapping[str, Any] | None = None,
        ordering: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(self.model)
        stmt = self._apply_list_query(stmt, search=search, filters=filters, ordering=ordering)
        return self.db.scalar(stmt) or 0

    def extract_filters(self, query_params: Mapping[str, Any]) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        filter_fields = self.get_filter_fields()
        for field_name, value in query_params.items():
            if field_name in self.list_param_names or field_name not in filter_fields:
                continue
            if value is None or value == "":
                continue
            filters[field_name] = self._coerce_filter_value(field_name, value)
        return filters

    @classmethod
    def openapi_filter_parameters(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": field_name,
                "in": "query",
                "required": False,
                "schema": cls._openapi_schema_for_column(column),
                "description": f"Filter by {field_name}",
            }
            for field_name, column in cls.get_filter_fields().items()
        ]

    @classmethod
    def get_search_fields(cls) -> dict[str, ColumnElement[Any]]:
        return cls._resolve_fields(cls.search_fields)

    @classmethod
    def get_filter_fields(cls) -> dict[str, ColumnElement[Any]]:
        return cls._resolve_fields(cls.filter_fields)

    @classmethod
    def get_ordering_fields(cls) -> dict[str, ColumnElement[Any]]:
        return cls._resolve_fields(cls.ordering_fields)

    def list(
        self,
        offset: int = 0,
        limit: int = 100,
        order_by: Any | None = None,
    ) -> list[ModelT]:
        stmt = select(self.model).offset(offset).limit(limit)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        return list(self.db.scalars(stmt).all())

    def list_filtered(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        search: str | None = None,
        filters: Mapping[str, Any] | None = None,
        ordering: str | None = None,
    ) -> list[ModelT]:
        stmt = select(self.model)
        stmt = self._apply_list_query(stmt, search=search, filters=filters, ordering=ordering)
        if ordering:
            stmt = self._apply_ordering(stmt, self.validate_ordering(ordering))
        stmt = stmt.offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def list_with_count_filtered(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        search: str | None = None,
        filters: Mapping[str, Any] | None = None,
        ordering: str | None = None,
    ) -> tuple[list[ModelT], int]:
        return self.list_filtered(
            offset=offset,
            limit=limit,
            search=search,
            filters=filters,
            ordering=ordering,
        ), self.count_filtered(search=search, filters=filters, ordering=ordering)

    def create(self, **values: Any) -> ModelT:
        obj = self.model(**values)
        return self.save(obj)

    def save(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.flush()

    def _apply_list_query(
        self,
        stmt: Select,
        *,
        search: str | None,
        filters: Mapping[str, Any] | None,
        ordering: str | None,
    ) -> Select:
        active_fields = self._active_list_fields(
            search=search,
            filters=filters,
            ordering=self.validate_ordering(ordering) if ordering else None,
        )
        stmt = self.apply_list_joins(stmt, active_fields)
        stmt = self._apply_search(stmt, search)
        stmt = self._apply_filters(stmt, filters or {})
        return stmt

    def apply_list_joins(self, stmt: Select, active_fields: set[str]) -> Select:
        for field_name in active_fields:
            stmt = self._apply_field_joins(stmt, field_name)
        return stmt

    def _active_list_fields(
        self,
        *,
        search: str | None,
        filters: Mapping[str, Any] | None,
        ordering: str | None,
    ) -> set[str]:
        fields: set[str] = set()
        if search:
            fields.update(self.get_search_fields())
        for key, value in (filters or {}).items():
            if value is not None and value != "":
                fields.add(key)
        if ordering:
            fields.add(ordering.removeprefix("-"))
        return fields

    def _apply_search(self, stmt: Select, search: str | None) -> Select:
        if not search:
            return stmt
        pattern = f"%{search.strip()}%"
        return stmt.where(
            or_(*(field.ilike(pattern) for field in self.get_search_fields().values()))
        )

    def _apply_filters(self, stmt: Select, filters: Mapping[str, Any]) -> Select:
        filter_fields = self.get_filter_fields()
        for field_name, value in filters.items():
            if value is None or value == "":
                continue
            column = filter_fields[field_name]
            if isinstance(value, str):
                stmt = stmt.where(column.ilike(f"%{value.strip()}%"))
            else:
                stmt = stmt.where(column == value)
        return stmt

    def validate_ordering(self, ordering: str | None) -> str:
        if not ordering:
            raise ValueError("Ordering is required")
        field_name = ordering.removeprefix("-")
        ordering_fields = self.get_ordering_fields()
        if field_name not in ordering_fields:
            allowed = ", ".join(sorted(ordering_fields))
            raise ValueError(f"Invalid ordering field '{field_name}'. Allowed fields: {allowed}")
        return ordering

    def _apply_ordering(self, stmt: Select, ordering: str) -> Select:
        descending = ordering.startswith("-")
        field_name = ordering.removeprefix("-")
        column = self.get_ordering_fields()[field_name]
        if descending:
            column = column.desc()
        return stmt.order_by(column)

    def _coerce_filter_value(self, field_name: str, value: Any) -> Any:
        column = self.get_filter_fields()[field_name]
        try:
            python_type = column.type.python_type
        except (AttributeError, NotImplementedError):
            return value
        if python_type is str or not isinstance(value, str):
            return value
        try:
            return python_type(value)
        except ValueError as exc:
            raise ValueError(f"Invalid value for filter '{field_name}'") from exc

    @classmethod
    def _resolve_fields(cls, field_names: tuple[str, ...]) -> dict[str, ColumnElement[Any]]:
        if isinstance(field_names, str):
            raise TypeError("Repository field config must be a tuple, for example ('title',)")
        return {field_name: cls._resolve_field(field_name) for field_name in field_names}

    @classmethod
    def _resolve_field(cls, field_name: str) -> ColumnElement[Any]:
        if field_name in cls.field_overrides:
            return cls.field_overrides[field_name]
        model = cls.model
        parts = field_name.split("__")
        for relationship_name in parts[:-1]:
            if relationship_name in cls.related_fields:
                model = cls.related_fields[relationship_name][0]
            else:
                relationship = getattr(model, relationship_name)
                model = relationship.property.mapper.class_
        return getattr(model, parts[-1])

    def _apply_field_joins(self, stmt: Select, field_name: str) -> Select:
        if field_name in self.field_overrides:
            return self._apply_override_field_join(stmt, self.field_overrides[field_name])

        model = self.model
        for relationship_name in field_name.split("__")[:-1]:
            if relationship_name in self.related_fields:
                related_model, onclause = self.related_fields[relationship_name]
                stmt = stmt.outerjoin(related_model, onclause)
                model = related_model
            else:
                relationship = getattr(model, relationship_name)
                stmt = stmt.outerjoin(relationship)
                model = relationship.property.mapper.class_
        return stmt

    def _apply_override_field_join(self, stmt: Select, column: ColumnElement[Any]) -> Select:
        for related_model, onclause in self.related_fields.values():
            if self._column_belongs_to_model(column, related_model):
                return stmt.outerjoin(related_model, onclause)
        return stmt

    @classmethod
    def _column_belongs_to_model(cls, column: ColumnElement[Any], model: type[Any]) -> bool:
        if getattr(column, "class_", None) is model:
            return True
        try:
            return column.property.parent.class_ is model
        except AttributeError:
            return False

    @classmethod
    def _openapi_schema_for_column(cls, column: ColumnElement[Any]) -> dict[str, Any]:
        try:
            python_type = column.type.python_type
        except (AttributeError, NotImplementedError):
            python_type = str

        type_map = {
            bool: "boolean",
            float: "number",
            int: "integer",
            str: "string",
        }
        return {"type": type_map.get(python_type, "string")}
