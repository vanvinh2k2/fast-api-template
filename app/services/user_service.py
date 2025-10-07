
from sqlalchemy.orm import Session

from app.repositories.user_repo import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository | None = None) -> None:
        self.user_repo = user_repo or UserRepository()

    def get_current_user(self, db: Session, user_id: int):
        return self.user_repo.get(db, user_id)
