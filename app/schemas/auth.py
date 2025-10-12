from pydantic import BaseModel
from typing import Literal


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    token_type: Literal["access", "refresh"]
    user_id: int
    jti: str
    iat: int
    exp: int


class LoginRequest(BaseModel):
    username: str
    password: str
