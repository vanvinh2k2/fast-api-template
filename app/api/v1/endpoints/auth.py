from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.schemas.auth import TokenPair, RefreshIn
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest
from app.core.security import create_access_token, create_refresh_token, decode_token

router = APIRouter()


@router.post("/login", response_model=TokenPair, summary="Login and get tokens")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db_dep),
):
    svc = AuthService()
    user = svc.authenticate(db, email=request.username, password=request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    return TokenPair(
        access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id)
    )


@router.post("/refresh", response_model=TokenPair)
def refresh_token(body: RefreshIn):
    try:
        payload = decode_token(body.refresh_token, expected_type="refresh")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
        )
    uid = payload.user_id
    return TokenPair(access_token=create_access_token(uid), refresh_token=create_refresh_token(uid))
