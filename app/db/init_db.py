from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User


def init_db(db: Session) -> None:
    # create an admin if not exists (email: admin@example.com / password: admin)
    admin = db.scalar(select(User).where(User.email == "admin@example.com"))
    if not admin:
        admin = User(
            email="admin@example.com",
            full_name="Admin",
            hashed_password=get_password_hash("admin"),
            is_active=True,
            is_superuser=True,
        )
        db.add(admin)
        db.commit()
