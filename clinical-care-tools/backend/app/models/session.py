"""
Session Model

Represents active user sessions for authentication and token management.
Includes security features for session binding and hijacking detection.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, func, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.models import Base


class Session(Base):
    """
    User session model for token-based authentication with security binding.

    Security Features:
        - Session binding: IP + User-Agent hash validation
        - Hijacking detection: Alert on binding violation
        - Idle timeout: Auto-logout after inactivity
        - Absolute timeout: Force re-authentication after max duration
        - Concurrent limits: Max N sessions per user

    Attributes:
        id: Unique session identifier
        user_id: Reference to user account
        token: Session token (32-char secure random)
        ip_hash: Hash of client IP (for binding)
        user_agent_hash: Hash of User-Agent (for binding)
        session_hash: Combined hash of IP + User-Agent
        device_name: Extracted device name from User-Agent
        is_active: Whether session is currently active
        created_at: When session was created
        expires_at: Absolute expiration time
        last_activity: Last request timestamp (for idle timeout)
        invalidated_at: When session was invalidated (logout/timeout)

    Relationships:
        user: Reference to User model
    """

    __tablename__ = "sessions"

    # Primary Key
    id: Mapped[str] = mapped_column(String(32), primary_key=True)

    # Foreign Keys
    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    # Authentication Token
    token: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="Secure session token (32 random bytes, hex-encoded)",
    )

    # Security: Session Binding Hashes (Phase 5)
    ip_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="SHA-256 hash of client IP address"
    )
    user_agent_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="SHA-256 hash of User-Agent string"
    )
    session_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Combined hash of IP + User-Agent for validation"
    )

    # Device Information
    device_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Extracted device name (e.g., 'iPhone', 'Windows PC')"
    )

    # Session State
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether session is currently active"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="Session creation time"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Absolute expiration time (24 hours from creation)"
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="Last activity timestamp (for idle timeout detection)"
    )
    invalidated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When session was invalidated (logout/timeout/hijacking)"
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="sessions",
        foreign_keys=[user_id],
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_sessions_user", "user_id"),
        Index("idx_sessions_token", "token"),
        Index("idx_sessions_active", "is_active"),
        Index("idx_sessions_expires", "expires_at"),
        Index("idx_sessions_user_active", "user_id", "is_active"),
        # For cleanup of expired sessions
        Index("idx_sessions_cleanup", "expires_at", postgresql_where="is_active = true AND expires_at < now()"),
    )

    def __repr__(self) -> str:
        """String representation of Session."""
        return f"<Session(id={self.id}, user_id={self.user_id}, is_active={self.is_active}, expires_at={self.expires_at})>"
