from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken, RefreshTokenFamily
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, RefreshToken)
        self.family_repo = BaseRepository(db, RefreshTokenFamily)

    def create_family(
        self,
        user_id: UUID,
        expires_at: datetime,
    ) -> RefreshTokenFamily:
        return self.family_repo.create(user_id=user_id, expires_at=expires_at)

    def get_family(self, family_id: UUID) -> Optional[RefreshTokenFamily]:
        return self.db.scalar(select(RefreshTokenFamily).where(RefreshTokenFamily.id == family_id))

    def get_by_jti(self, jti: str) -> Optional[RefreshToken]:
        return self.db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))

    def create(
        self,
        family_id: UUID,
        jti: str,
        expires_at: datetime,
    ) -> RefreshToken:
        return super().create(family_id=family_id, jti=jti, expires_at=expires_at)

    def revoke(
        self,
        obj: RefreshToken,
        revoked_at: datetime,
        replaced_by_jti: str | None = None,
    ) -> RefreshToken:
        obj.revoked_at = revoked_at
        obj.replaced_by_jti = replaced_by_jti
        return self.save(obj)

    def revoke_family(
        self,
        obj: RefreshTokenFamily,
        revoked_at: datetime,
    ) -> RefreshTokenFamily:
        obj.revoked_at = revoked_at
        return self.family_repo.save(obj)
