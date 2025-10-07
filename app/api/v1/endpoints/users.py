
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_dep
from app.models.user import User
from app.schemas.user import UserCreate, UserPublic
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("/me", response_model=UserPublic)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("", response_model=UserPublic, summary="Register new user")
def register(user_in: UserCreate, db: Session = Depends(get_db_dep)):
    svc = AuthService()
    user = svc.register(db, email=user_in.email, full_name=user_in.full_name, password=user_in.password)
    return user
