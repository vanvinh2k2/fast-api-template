from pydantic import BaseModel, ConfigDict


class ItemBase(BaseModel):
    title: str
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class ItemPublic(ItemBase):
    id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
