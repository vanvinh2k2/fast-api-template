from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.repositories.item_repo import ItemRepository
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.services.item_service import ItemService

bearer = HTTPBearer(auto_error=False)


def get_db_dep(db: Session = Depends(get_db)) -> Session:
    return db


SessionDep = Annotated[Session, Depends(get_db_dep)]


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(
        UserRepository(session),
        RefreshTokenRepository(session),
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_item_service(session: SessionDep) -> ItemService:
    return ItemService(ItemRepository(session))


ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]


def get_current_user_id(
    request: Request,
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> UUID:
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
    try:
        user_id = UUID(payload.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )
    request.state.actor_id = user_id
    return user_id


def get_current_user(
    service: AuthServiceDep,
    user_id: UUID = Depends(get_current_user_id),
) -> User:
    user = service.get_current_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

RequireAuth = Depends(get_current_user)
