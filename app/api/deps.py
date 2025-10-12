from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.core.database import get_db
from app.models.user import User

bearer = HTTPBearer(auto_error=False)


def get_db_dep(db: Session = Depends(get_db)) -> Session:
    return db


def get_current_user_id(
    request: Request,
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> int:
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    try:
        payload = decode_token(creds.credentials, expected_type="access")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )
    request.state.actor_id = payload.user_id
    return payload.user_id


def get_current_user(
    db: Session = Depends(get_db_dep),
    user_id: int = Depends(get_current_user_id),
) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user
