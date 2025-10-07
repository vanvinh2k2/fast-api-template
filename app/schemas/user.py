
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True
