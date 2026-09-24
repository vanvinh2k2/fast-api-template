from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenPair


class InvalidRefreshTokenError(Exception):
    pass


class InactiveUserError(Exception):
    pass


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository | None = None,
        refresh_token_repo: RefreshTokenRepository | None = None,
    ) -> None:
        self.user_repo = user_repo or UserRepository()
        self.refresh_token_repo = refresh_token_repo or RefreshTokenRepository()

    def authenticate(self, db: Session, *, email: str, password: str) -> User | None:
        user = self.user_repo.get_by_email(db, email=email)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def register(self, db: Session, *, email: str, full_name: str | None, password: str) -> User:
        hashed = get_password_hash(password)
        return self.user_repo.create(db, email=email, full_name=full_name, hashed_password=hashed)

    def issue_token_pair(
        self,
        db: Session,
        *,
        user_id: int,
    ) -> TokenPair:
        refresh_token = create_refresh_token(user_id)
        refresh_payload = decode_token(refresh_token, expected_type="refresh")
        expires_at = datetime.fromtimestamp(refresh_payload.exp, timezone.utc)
        family = self.refresh_token_repo.create_family(
            db,
            user_id=user_id,
            expires_at=expires_at,
        )
        return self._issue_token_pair_for_family(
            db,
            user_id=user_id,
            family_id=family.id,
            refresh_token=refresh_token,
        )

    def _issue_token_pair_for_family(
        self,
        db: Session,
        *,
        user_id: int,
        family_id: int,
        refresh_token: str | None = None,
    ) -> TokenPair:
        access_token = create_access_token(user_id)
        refresh_token = refresh_token or create_refresh_token(user_id)
        refresh_payload = decode_token(refresh_token, expected_type="refresh")
        self.refresh_token_repo.create(
            db,
            family_id=family_id,
            jti=refresh_payload.jti,
            expires_at=datetime.fromtimestamp(refresh_payload.exp, timezone.utc),
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def rotate_refresh_token(self, db: Session, *, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
            user_id = int(payload.sub)
        except Exception:
            raise InvalidRefreshTokenError

        user = self.user_repo.get(db, user_id)
        if not user or not user.is_active:
            raise InactiveUserError

        stored_token = self.refresh_token_repo.get_by_jti(db, payload.jti)
        if not stored_token:
            raise InvalidRefreshTokenError

        family = self.refresh_token_repo.get_family(db, stored_token.family_id)
        if not family or family.revoked_at is not None:
            raise InvalidRefreshTokenError

        now = datetime.now(timezone.utc)
        if stored_token.revoked_at is not None:
            self.refresh_token_repo.revoke_family(db, family, revoked_at=now)
            raise InvalidRefreshTokenError

        token_pair = self._issue_token_pair_for_family(
            db,
            user_id=user_id,
            family_id=family.id,
        )
        new_refresh_payload = decode_token(token_pair.refresh_token, expected_type="refresh")
        self.refresh_token_repo.revoke(
            db,
            stored_token,
            revoked_at=now,
            replaced_by_jti=new_refresh_payload.jti,
        )
        return token_pair
