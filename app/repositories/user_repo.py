from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, User)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.scalar(select(User).where(User.email == email))

    def create(self, email: str, full_name: str | None, hashed_password: str) -> User:
        return super().create(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
        )
