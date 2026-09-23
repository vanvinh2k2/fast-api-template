from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error

from app.core.config import settings
from app.schemas.auth import TokenPayload

password_hasher = PasswordHasher()


def _create_token(
    *, user_id: int, token_type: Literal["access", "refresh"], exp_delta: timedelta
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "token_type": token_type,
        "user_id": int(user_id),
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + exp_delta).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _create_token(
        user_id=user_id,
        token_type="access",
        exp_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        user_id=user_id,
        token_type="refresh",
        exp_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(
    token: str, *, expected_type: Optional[Literal["access", "refresh"]] = None
) -> TokenPayload:
    data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    payload = TokenPayload(**data)
    if expected_type and payload.token_type != expected_type:
        raise ValueError("Invalid token type")
    return payload


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_hasher.verify(hashed_password, plain_password)
    except Argon2Error:
        return False
    return True


def get_password_hash(password: str) -> str:
    return password_hasher.hash(password)
