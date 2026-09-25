from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.error_codes import ErrorCode
from app.core.exceptions import AuthError, ConflictError
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


class AuthService:
    def get_current_user(self, db: Session, user_id: UUID) -> User | None:
        return UserRepository(db).get(user_id)

    def authenticate(self, db: Session, email: str, password: str) -> User | None:
        user = UserRepository(db).get_by_email(email=email)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def register(self, db: Session, email: str, full_name: str | None, password: str) -> User:
        if UserRepository(db).get_by_email(email=email):
            raise ConflictError("Email already registered", code=ErrorCode.USER_EMAIL_TAKEN)
        hashed = get_password_hash(password)
        return UserRepository(db).create(email=email, full_name=full_name, hashed_password=hashed)

    def issue_token_pair(
        self,
        db: Session,
        user_id: UUID,
    ) -> TokenPair:
        refresh_token = create_refresh_token(user_id)
        refresh_payload = decode_token(refresh_token, expected_type="refresh")
        expires_at = datetime.fromtimestamp(refresh_payload.exp, timezone.utc)
        refresh_token_repo = RefreshTokenRepository(db)
        family = refresh_token_repo.create_family(
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
        user_id: UUID,
        family_id: UUID,
        refresh_token: str | None = None,
    ) -> TokenPair:
        access_token = create_access_token(user_id)
        refresh_token = refresh_token or create_refresh_token(user_id)
        refresh_payload = decode_token(refresh_token, expected_type="refresh")
        RefreshTokenRepository(db).create(
            family_id=family_id,
            jti=refresh_payload.jti,
            expires_at=datetime.fromtimestamp(refresh_payload.exp, timezone.utc),
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def rotate_refresh_token(self, db: Session, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
            user_id = UUID(payload.sub)
        except Exception:
            raise AuthError("Invalid or expired refresh token", code=ErrorCode.AUTH_INVALID_TOKEN)

        user = UserRepository(db).get(user_id)
        if not user or not user.is_active:
            raise AuthError("User inactive")

        refresh_token_repo = RefreshTokenRepository(db)
        stored_token = refresh_token_repo.get_by_jti(payload.jti)
        if not stored_token:
            raise AuthError("Invalid or expired refresh token", code=ErrorCode.AUTH_INVALID_TOKEN)

        family = refresh_token_repo.get_family(stored_token.family_id)
        if not family or family.revoked_at is not None:
            raise AuthError("Invalid or expired refresh token", code=ErrorCode.AUTH_INVALID_TOKEN)

        now = datetime.now(timezone.utc)
        if stored_token.revoked_at is not None:
            refresh_token_repo.revoke_family(family, revoked_at=now)
            raise AuthError("Invalid or expired refresh token", code=ErrorCode.AUTH_INVALID_TOKEN)

        token_pair = self._issue_token_pair_for_family(
            db,
            user_id=user_id,
            family_id=family.id,
        )
        new_refresh_payload = decode_token(token_pair.refresh_token, expected_type="refresh")
        refresh_token_repo.revoke(
            stored_token,
            revoked_at=now,
            replaced_by_jti=new_refresh_payload.jti,
        )
        return token_pair
