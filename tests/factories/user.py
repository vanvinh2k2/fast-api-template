from app.models.user import User
from app.core.security import get_password_hash


def make_user(
    db,
    *,
    email: str = "user@example.com",
    password: str = "secret",
    is_active: bool = True,
    is_superuser: bool = False,
    full_name: str | None = None,
) -> User:
    u = User(
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        is_active=is_active,
        is_superuser=is_superuser,
    )
    db.add(u)
    db.flush()
    return u
