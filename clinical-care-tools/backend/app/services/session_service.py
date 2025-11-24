"""
Session management service.

Handles session creation, validation, cleanup, and concurrency limits.
"""

from datetime import datetime
from typing import Optional, List
import hashlib

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.models.user import User


def hash_value(value: str) -> str:
    """
    Hash a value using SHA256.

    Args:
        value: String to hash

    Returns:
        SHA256 hex digest
    """
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


async def create_session(
    db: AsyncSession,
    user_id: str,
    token_jti: str,
    ip_address: str,
    user_agent: str
) -> Session:
    """
    Create a new session for a user.

    Enforces max 2 concurrent sessions per user by invalidating oldest session.

    Args:
        db: Database session
        user_id: User UUID
        token_jti: JWT token ID (jti claim)
        ip_address: Client IP address
        user_agent: User-Agent header

    Returns:
        Created Session object

    Example:
        session = await create_session(
            db, user_id="123e4567-e89b-12d3-a456-426614174000",
            token_jti="abc-def-ghi", ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )
    """
    # Check active sessions for this user
    active_sessions = await get_active_sessions(db, user_id)

    # If user has 2+ active sessions, invalidate the oldest one
    if len(active_sessions) >= 2:
        # Sort by created_at ascending (oldest first)
        oldest_session = min(active_sessions, key=lambda s: s.created_at)
        oldest_session.invalidate()
        await db.commit()

    # Create new session
    session = Session(
        user_id=user_id,
        token_jti=token_jti,
        ip_hash=hash_value(ip_address),
        user_agent_hash=hash_value(user_agent)
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session


async def get_session_by_jti(
    db: AsyncSession,
    token_jti: str
) -> Optional[Session]:
    """
    Get session by JWT token ID.

    Args:
        db: Database session
        token_jti: JWT token ID (jti claim)

    Returns:
        Session if found, None otherwise
    """
    result = await db.execute(
        select(Session).where(Session.token_jti == token_jti)
    )
    return result.scalar_one_or_none()


async def get_active_sessions(
    db: AsyncSession,
    user_id: str
) -> List[Session]:
    """
    Get all active (non-expired) sessions for a user.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        List of active Session objects
    """
    result = await db.execute(
        select(Session).where(
            and_(
                Session.user_id == user_id,
                Session.expires_at > datetime.utcnow()
            )
        )
    )
    return result.scalars().all()


async def validate_session(
    db: AsyncSession,
    token_jti: str,
    ip_address: str,
    user_agent: str
) -> Optional[Session]:
    """
    Validate a session by JTI, expiry, and binding.

    Args:
        db: Database session
        token_jti: JWT token ID
        ip_address: Current request IP
        user_agent: Current User-Agent

    Returns:
        Valid Session if all checks pass, None otherwise

    Validation checks:
    1. Session exists
    2. Session not expired
    3. IP binding matches
    4. User-agent binding matches
    """
    session = await get_session_by_jti(db, token_jti)

    if not session:
        return None

    if session.is_expired:
        return None

    if not session.validate_binding(hash_value(ip_address), hash_value(user_agent)):
        return None

    return session


async def update_session_activity(
    db: AsyncSession,
    session: Session
) -> Session:
    """
    Update session last activity and extend expiry.

    Args:
        db: Database session
        session: Session to update

    Returns:
        Updated Session object
    """
    session.update_activity()
    await db.commit()
    await db.refresh(session)
    return session


async def invalidate_session(
    db: AsyncSession,
    token_jti: str
) -> bool:
    """
    Invalidate a session (logout).

    Args:
        db: Database session
        token_jti: JWT token ID

    Returns:
        True if session was invalidated, False if not found
    """
    session = await get_session_by_jti(db, token_jti)

    if not session:
        return False

    session.invalidate()
    await db.commit()
    return True


async def invalidate_all_user_sessions(
    db: AsyncSession,
    user_id: str
) -> int:
    """
    Invalidate all sessions for a user.

    Used for security events (password change, suspicious activity).

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        Number of sessions invalidated
    """
    sessions = await get_active_sessions(db, user_id)

    for session in sessions:
        session.invalidate()

    await db.commit()
    return len(sessions)


async def cleanup_expired_sessions(
    db: AsyncSession
) -> int:
    """
    Delete expired sessions from database.

    Should be run periodically (e.g., daily cron job).

    Args:
        db: Database session

    Returns:
        Number of sessions deleted
    """
    result = await db.execute(
        delete(Session).where(Session.expires_at <= datetime.utcnow())
    )
    await db.commit()
    return result.rowcount
