from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Literal
from uuid import UUID

from app.schemas.base import ORMModel


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    type: Literal["access", "refresh"]
    jti: str
    iss: str
    aud: str
    iat: int
    exp: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    password: str = Field(min_length=9)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain an uppercase letter")
        if not any(char.islower() for char in value):
            raise ValueError("Password must contain a lowercase letter")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain a number")
        if not any(not char.isalnum() for char in value):
            raise ValueError("Password must contain a special character")
        return value


class UserResponse(ORMModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
