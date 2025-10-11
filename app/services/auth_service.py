from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repo import UserRepository


class AuthService:
    def __init__(self, user_repo: UserRepository | None = None) -> None:
        self.user_repo = user_repo or UserRepository()

    def authenticate(self, db: Session, *, email: str, password: str) -> User | None:
        user = self.user_repo.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def issue_token(self, user_id: int) -> str:
        expire = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(user_id, expire)

    def register(self, db: Session, *, email: str, full_name: str | None, password: str) -> User:
        hashed = get_password_hash(password)
        return self.user_repo.create(db, email=email, full_name=full_name, hashed_password=hashed)
