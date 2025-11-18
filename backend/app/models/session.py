"""
Session Model
In-memory representation of user sessions (stored in Redis)
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel


class Session(BaseModel):
    """
    Session model for user authentication sessions.

    Stored in Redis with key: session:{session_id}
    TTL: 8 hours (28800 seconds)
    """

    session_id: str
    user_id: str
    token_jti: str  # JWT token ID
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    @classmethod
    def create(
        cls,
        user_id: str,
        token_jti: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        ttl_hours: int = 8
    ) -> "Session":
        """Create new session."""
        now = datetime.utcnow()
        return cls(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            token_jti=token_jti,
            expires_at=now + timedelta(hours=ttl_hours),
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
        )

    def to_redis_key(self) -> str:
        """Get Redis key for this session."""
        return f"session:{self.session_id}"

    def ttl_seconds(self) -> int:
        """Get remaining TTL in seconds."""
        remaining = (self.expires_at - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))
