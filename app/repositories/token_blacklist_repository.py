from datetime import datetime, timezone
from typing import Optional, cast

from sqlalchemy.orm import Session

from app.models.token_blacklist import TokenBlacklist


class TokenBlacklistRepository:
    @staticmethod
    def _to_utc_aware(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def get_by_hash(db: Session, token_hash: str) -> Optional[TokenBlacklist]:
        return db.query(TokenBlacklist).filter(TokenBlacklist.token_hash == token_hash).first()

    @staticmethod
    def is_blacklisted(db: Session, token_hash: str) -> bool:
        record = TokenBlacklistRepository.get_by_hash(db, token_hash=token_hash)
        if not record:
            return False
        expires_at = cast(Optional[datetime], record.expires_at)
        if expires_at is None:
            return True
        return TokenBlacklistRepository._to_utc_aware(expires_at) > datetime.now(timezone.utc)

    @staticmethod
    def add(db: Session, token_hash: str, user_id: Optional[int], expires_at: Optional[datetime]) -> TokenBlacklist:
        existing = TokenBlacklistRepository.get_by_hash(db, token_hash=token_hash)
        if existing:
            return existing

        record = TokenBlacklist(token_hash=token_hash, user_id=user_id, expires_at=expires_at)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
