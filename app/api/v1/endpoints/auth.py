from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_dep
from app.core.exceptions import AuthError, ConflictError
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshIn, TokenPair, UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
)
def register(user_in: UserCreate, db: Session = Depends(get_db_dep)):
    svc = AuthService()
    try:
        return svc.register(
            db,
            email=user_in.email,
            full_name=user_in.full_name,
            password=user_in.password,
        )
    except ConflictError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post("/login", response_model=TokenPair, summary="Login and get tokens")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db_dep),
):
    svc = AuthService()
    user = svc.authenticate(db, email=request.email, password=request.password)
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
    except AuthError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
