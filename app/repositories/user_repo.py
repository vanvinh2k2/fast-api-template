from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def create(
        self, db: Session, *, email: str, full_name: str | None, hashed_password: str
    ) -> User:
        obj = User(email=email, full_name=full_name, hashed_password=hashed_password)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
