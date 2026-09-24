from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.schemas.auth import LoginRequest, RefreshIn, TokenPair
from app.services.auth_service import AuthService, InactiveUserError, InvalidRefreshTokenError

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
    return svc.issue_token_pair(db, user_id=user.id)


@router.post("/refresh", response_model=TokenPair)
def refresh_token(body: RefreshIn, db: Session = Depends(get_db_dep)):
    svc = AuthService()
    try:
        return svc.rotate_refresh_token(db, refresh_token=body.refresh_token)
    except InvalidRefreshTokenError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired refresh token"},
        )
    except InactiveUserError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "User inactive"},
        )
