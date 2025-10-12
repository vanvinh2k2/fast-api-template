from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
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

    def register(self, db: Session, *, email: str, full_name: str | None, password: str) -> User:
        hashed = get_password_hash(password)
        return self.user_repo.create(db, email=email, full_name=full_name, hashed_password=hashed)
