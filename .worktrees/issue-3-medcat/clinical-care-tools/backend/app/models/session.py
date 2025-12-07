"""
Session model for authentication session management.

Tracks user sessions with expiry, binding, and concurrency limits.
"""

from datetime import datetime, timedelta
import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Session(Base):
    """
    Session model for tracking user authentication sessions.

    Features:
    - 8-hour expiry with activity-based renewal
    - IP and user-agent binding for hijacking prevention
    - Max 2 concurrent sessions per user (enforced in service layer)
    - Token JTI tracking for JWT invalidation
    """

    __tablename__ = "sessions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique session identifier"
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who owns this session"
    )

    token_jti = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="JWT Token ID (jti claim) for token invalidation"
    )

    ip_hash = Column(
        String(64),
        nullable=False,
        doc="SHA256 hash of client IP address for binding"
    )

    user_agent_hash = Column(
        String(64),
        nullable=False,
        doc="SHA256 hash of User-Agent header for binding"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Session creation timestamp (UTC)"
    )

    last_activity = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Last activity timestamp (UTC)"
    )

    expires_at = Column(
        DateTime,
        nullable=False,
        doc="Session expiration timestamp (UTC)"
    )

    # Relationship to User model
    user = relationship("User", back_populates="sessions")

    def __init__(self, **kwargs):
        """
        Initialize Session with automatic expiry calculation.

        Sets expires_at to 8 hours from creation if not provided.
        """
        super().__init__(**kwargs)

        # Set expiry to 8 hours from now if not provided
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(hours=8)

        # Ensure created_at and last_activity are set
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.last_activity:
            self.last_activity = datetime.utcnow()

    @property
    def is_expired(self) -> bool:
        """
        Check if session has expired.

        Returns:
            True if session is expired, False otherwise
        """
        return self.expires_at <= datetime.utcnow()

    def update_activity(self) -> None:
        """
        Update last activity timestamp and extend expiry.

        Extends session expiry to 8 hours from current time.
        """
        now = datetime.utcnow()
        self.last_activity = now
        self.expires_at = now + timedelta(hours=8)

    def validate_binding(self, ip_hash: str, user_agent_hash: str) -> bool:
        """
        Validate that IP and user-agent match session binding.

        Prevents session hijacking by ensuring requests come from
        the same IP and browser as the original login.

        Args:
            ip_hash: SHA256 hash of current request IP
            user_agent_hash: SHA256 hash of current User-Agent

        Returns:
            True if binding is valid, False otherwise
        """
        return (
            self.ip_hash == ip_hash and
            self.user_agent_hash == user_agent_hash
        )

    def invalidate(self) -> None:
        """
        Invalidate session immediately.

        Sets expiry to past time, making session unusable.
        Used for logout and security events.
        """
        self.expires_at = datetime.utcnow() - timedelta(seconds=1)

    def __repr__(self) -> str:
        """String representation of Session."""
        return (
            f"<Session(id={self.id}, user_id={self.user_id}, "
            f"expires_at={self.expires_at}, is_expired={self.is_expired})>"
        )
