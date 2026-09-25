from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error

from app.core.config import settings
from app.schemas.auth import TokenPayload

password_hasher = PasswordHasher()
JWT_ISSUER = "auth-service"
JWT_AUDIENCE = "api"


def _create_token(
    *, user_id: UUID, token_type: Literal["access", "refresh"], exp_delta: timedelta
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "jti": str(uuid4()),
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + exp_delta).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: UUID) -> str:
    return _create_token(
        user_id=user_id,
        token_type="access",
        exp_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(
        user_id=user_id,
        token_type="refresh",
        exp_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(
    token: str, *, expected_type: Optional[Literal["access", "refresh"]] = None
) -> TokenPayload:
    data = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
        options={"require": ["sub", "type", "jti", "iss", "aud", "iat", "exp"]},
    )
    payload = TokenPayload(**data)
    if expected_type and payload.type != expected_type:
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
