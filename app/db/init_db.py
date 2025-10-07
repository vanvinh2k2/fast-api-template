
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import get_password_hash


def init_db(db: Session) -> None:
    # create an admin if not exists (email: admin@example.com / password: admin)
    admin = db.query(User).filter(User.email == "admin@example.com").first()
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
