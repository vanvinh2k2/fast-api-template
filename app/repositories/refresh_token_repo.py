from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken, RefreshTokenFamily


class RefreshTokenRepository:
    def create_family(
        self,
        db: Session,
        *,
        user_id: int,
        expires_at: datetime,
    ) -> RefreshTokenFamily:
        obj = RefreshTokenFamily(
            user_id=user_id,
            expires_at=expires_at,
        )
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    def get_family(self, db: Session, family_id: int) -> Optional[RefreshTokenFamily]:
        return db.query(RefreshTokenFamily).filter(RefreshTokenFamily.id == family_id).first()

    def get_by_jti(self, db: Session, jti: str) -> Optional[RefreshToken]:
        return db.query(RefreshToken).filter(RefreshToken.jti == jti).first()

    def create(
        self,
        db: Session,
        *,
        family_id: int,
        jti: str,
        expires_at: datetime,
    ) -> RefreshToken:
        obj = RefreshToken(family_id=family_id, jti=jti, expires_at=expires_at)
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    def revoke(
        self,
        db: Session,
        obj: RefreshToken,
        *,
        revoked_at: datetime,
        replaced_by_jti: str | None = None,
    ) -> RefreshToken:
        obj.revoked_at = revoked_at
        obj.replaced_by_jti = replaced_by_jti
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj

    def revoke_family(
        self,
        db: Session,
        obj: RefreshTokenFamily,
        *,
        revoked_at: datetime,
    ) -> RefreshTokenFamily:
        obj.revoked_at = revoked_at
        db.add(obj)
        db.flush()
        db.refresh(obj)
        return obj
