from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.api.deps import AuthServiceDep, CurrentUser
from app.core.exceptions import AuthError, ConflictError
from app.schemas.auth import LoginRequest, RefreshIn, TokenPair, UserCreate, UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def read_me(current_user: CurrentUser):
    return current_user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
)
def register(payload: UserCreate, service: AuthServiceDep):
    try:
        return service.register(
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
        )
    except ConflictError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post("/login", response_model=TokenPair, summary="Login and get tokens")
def login(
    payload: LoginRequest,
    service: AuthServiceDep,
):
    user = service.authenticate(email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    return service.issue_token_pair(user_id=user.id)


@router.post("/refresh", response_model=TokenPair)
def refresh_token(payload: RefreshIn, service: AuthServiceDep):
    try:
        return service.rotate_refresh_token(refresh_token=payload.refresh_token)
    except AuthError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
