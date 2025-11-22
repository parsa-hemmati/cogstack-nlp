"""
Session Management Service for Clinical Care Tools.

Handles session creation, validation, security binding, and timeout management.
HIPAA Compliance: Implements session binding and hijacking detection.
"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func
from fastapi import HTTPException, status
import redis.asyncio as redis
import json

from app.core.config import settings
from app.core.security import hash_session_identifier, generate_secure_token
from app.models.session import Session
from app.models.audit_log import AuditLog
from app.schemas.session import SessionCreate, SessionResponse


class SessionService:
    """Service for managing user sessions with security features."""

    def __init__(self, db: AsyncSession, redis_client: Optional[redis.Redis] = None):
        """
        Initialize session service.

        Args:
            db: Database session
            redis_client: Optional Redis client for session caching
        """
        self.db = db
        self.redis = redis_client

    async def create_session(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        device_name: Optional[str] = None
    ) -> Session:
        """
        Create a new user session with security binding.

        Args:
            user_id: User ID
            ip_address: Client IP address
            user_agent: Client User-Agent string
            device_name: Optional device name for identification

        Returns:
            Created session object

        Raises:
            HTTPException: If max concurrent sessions exceeded
        """
        # Check concurrent session limit
        await self._check_concurrent_sessions(user_id)

        # Generate session token and identifiers
        session_token = generate_secure_token(32)
        session_hash = hash_session_identifier(ip_address, user_agent)

        # Create session
        new_session = Session(
            id=generate_secure_token(16),
            user_id=user_id,
            token=session_token,
            ip_hash=hash_session_identifier(ip_address, ""),  # Hash IP separately
            user_agent_hash=hash_session_identifier("", user_agent),  # Hash UA separately
            session_hash=session_hash,  # Combined hash for validation
            device_name=device_name or self._extract_device_name(user_agent),
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + settings.session_absolute_timeout,
            is_active=True
        )

        self.db.add(new_session)
        await self.db.commit()
        await self.db.refresh(new_session)

        # Cache session in Redis if available
        if self.redis:
            await self._cache_session(new_session)

        # Audit log session creation
        await self._audit_log(
            action="SESSION_CREATED",
            user_id=user_id,
            details={
                "session_id": new_session.id,
                "device_name": new_session.device_name,
                "ip_address": ip_address[:50]  # Store partial IP for privacy
            }
        )

        return new_session

    async def validate_session(
        self,
        session_id: str,
        token: str,
        ip_address: str,
        user_agent: str
    ) -> Optional[Session]:
        """
        Validate session with security checks.

        Args:
            session_id: Session ID
            token: Session token
            ip_address: Current client IP
            user_agent: Current client User-Agent

        Returns:
            Valid session object or None

        Raises:
            HTTPException: If session hijacking detected
        """
        # Try to get session from cache first
        session = None
        if self.redis:
            session = await self._get_cached_session(session_id)

        # If not in cache, get from database
        if not session:
            result = await self.db.execute(
                select(Session).where(
                    and_(
                        Session.id == session_id,
                        Session.token == token,
                        Session.is_active == True
                    )
                )
            )
            session = result.scalar_one_or_none()

        if not session:
            return None

        # Check session expiration
        now = datetime.now(timezone.utc)
        if session.expires_at < now:
            await self.invalidate_session(session_id)
            await self._audit_log(
                action="SESSION_EXPIRED",
                user_id=session.user_id,
                details={"session_id": session_id}
            )
            return None

        # Check idle timeout
        idle_time = now - session.last_activity
        if idle_time.total_seconds() > settings.session_idle_timeout.total_seconds():
            await self.invalidate_session(session_id)
            await self._audit_log(
                action="SESSION_IDLE_TIMEOUT",
                user_id=session.user_id,
                details={
                    "session_id": session_id,
                    "idle_minutes": idle_time.total_seconds() / 60
                }
            )
            return None

        # Session binding and hijacking detection
        if settings.SESSION_BINDING_ENABLED:
            current_hash = hash_session_identifier(ip_address, user_agent)

            # Strict validation - must match exactly
            if session.session_hash != current_hash:
                if settings.SESSION_HIJACK_DETECTION:
                    # Potential hijacking detected
                    await self._handle_hijacking_attempt(session, ip_address, user_agent)
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Session security violation detected"
                    )
                return None

        # Update last activity
        session.last_activity = now
        await self.db.execute(
            update(Session).where(Session.id == session_id).values(
                last_activity=now
            )
        )
        await self.db.commit()

        # Update cache if available
        if self.redis:
            await self._cache_session(session)

        return session

    async def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a session.

        Args:
            session_id: Session ID to invalidate

        Returns:
            True if session was invalidated
        """
        # Mark session as inactive
        result = await self.db.execute(
            update(Session).where(Session.id == session_id).values(
                is_active=False,
                invalidated_at=datetime.now(timezone.utc)
            )
        )
        await self.db.commit()

        # Remove from cache
        if self.redis:
            await self._remove_cached_session(session_id)

        # Audit log
        if result.rowcount > 0:
            session_result = await self.db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = session_result.scalar_one_or_none()
            if session:
                await self._audit_log(
                    action="SESSION_INVALIDATED",
                    user_id=session.user_id,
                    details={"session_id": session_id}
                )

        return result.rowcount > 0

    async def invalidate_all_user_sessions(
        self,
        user_id: str,
        except_current: Optional[str] = None
    ) -> int:
        """
        Invalidate all sessions for a user.

        Args:
            user_id: User ID
            except_current: Optional current session ID to keep active

        Returns:
            Number of sessions invalidated
        """
        # Build query
        query = update(Session).where(
            and_(
                Session.user_id == user_id,
                Session.is_active == True
            )
        )

        # Exclude current session if specified
        if except_current:
            query = query.where(Session.id != except_current)

        # Invalidate sessions
        query = query.values(
            is_active=False,
            invalidated_at=datetime.now(timezone.utc)
        )

        result = await self.db.execute(query)
        await self.db.commit()

        # Clear from cache
        if self.redis and result.rowcount > 0:
            sessions_result = await self.db.execute(
                select(Session).where(Session.user_id == user_id)
            )
            sessions = sessions_result.scalars().all()
            for session in sessions:
                if session.id != except_current:
                    await self._remove_cached_session(session.id)

        # Audit log
        if result.rowcount > 0:
            await self._audit_log(
                action="ALL_SESSIONS_INVALIDATED",
                user_id=user_id,
                details={
                    "count": result.rowcount,
                    "except_session": except_current
                }
            )

        return result.rowcount

    async def get_user_sessions(self, user_id: str) -> List[Session]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of active sessions
        """
        result = await self.db.execute(
            select(Session).where(
                and_(
                    Session.user_id == user_id,
                    Session.is_active == True
                )
            ).order_by(Session.created_at.desc())
        )
        return result.scalars().all()

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now(timezone.utc)

        # Find expired sessions
        expired_result = await self.db.execute(
            select(Session).where(
                and_(
                    Session.is_active == True,
                    Session.expires_at < now
                )
            )
        )
        expired_sessions = expired_result.scalars().all()

        # Invalidate expired sessions
        if expired_sessions:
            session_ids = [s.id for s in expired_sessions]
            result = await self.db.execute(
                update(Session).where(Session.id.in_(session_ids)).values(
                    is_active=False,
                    invalidated_at=now
                )
            )
            await self.db.commit()

            # Remove from cache
            if self.redis:
                for session_id in session_ids:
                    await self._remove_cached_session(session_id)

            # Audit log
            await self._audit_log(
                action="SESSIONS_CLEANUP",
                user_id="SYSTEM",
                details={"count": len(session_ids)}
            )

            return len(session_ids)

        return 0

    async def _check_concurrent_sessions(self, user_id: str):
        """
        Check if user has exceeded concurrent session limit.

        Args:
            user_id: User ID

        Raises:
            HTTPException: If limit exceeded
        """
        result = await self.db.execute(
            select(func.count(Session.id)).where(
                and_(
                    Session.user_id == user_id,
                    Session.is_active == True
                )
            )
        )
        count = result.scalar()

        if count >= settings.SESSION_MAX_CONCURRENT:
            # Get oldest session to suggest invalidation
            oldest_result = await self.db.execute(
                select(Session).where(
                    and_(
                        Session.user_id == user_id,
                        Session.is_active == True
                    )
                ).order_by(Session.created_at.asc()).limit(1)
            )
            oldest_session = oldest_result.scalar_one_or_none()

            await self._audit_log(
                action="SESSION_LIMIT_EXCEEDED",
                user_id=user_id,
                details={
                    "current_count": count,
                    "limit": settings.SESSION_MAX_CONCURRENT
                }
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": f"Maximum concurrent sessions ({settings.SESSION_MAX_CONCURRENT}) exceeded",
                    "oldest_session": {
                        "id": oldest_session.id if oldest_session else None,
                        "device": oldest_session.device_name if oldest_session else None,
                        "created": oldest_session.created_at.isoformat() if oldest_session else None
                    }
                }
            )

    async def _handle_hijacking_attempt(
        self,
        session: Session,
        ip_address: str,
        user_agent: str
    ):
        """
        Handle potential session hijacking attempt.

        Args:
            session: Session that failed validation
            ip_address: Current IP address
            user_agent: Current User-Agent
        """
        # Invalidate the compromised session
        await self.invalidate_session(session.id)

        # Audit log with security alert
        await self._audit_log(
            action="SESSION_HIJACKING_DETECTED",
            user_id=session.user_id,
            details={
                "session_id": session.id,
                "original_ip_hash": session.ip_hash,
                "current_ip": ip_address[:50],
                "original_ua_hash": session.user_agent_hash,
                "alert_level": "HIGH"
            }
        )

        # NOTE: Send security alert email if configured
        # await self._send_security_alert(session.user_id, "Session hijacking detected")

    def _extract_device_name(self, user_agent: str) -> str:
        """
        Extract device name from User-Agent string.

        Args:
            user_agent: User-Agent string

        Returns:
            Extracted device name or generic name
        """
        # Simple extraction - can be enhanced with ua-parser library
        if "Mobile" in user_agent:
            if "iPhone" in user_agent:
                return "iPhone"
            elif "Android" in user_agent:
                return "Android Device"
            return "Mobile Device"
        elif "Windows" in user_agent:
            return "Windows PC"
        elif "Mac" in user_agent:
            return "Mac"
        elif "Linux" in user_agent:
            return "Linux PC"
        return "Unknown Device"

    async def _cache_session(self, session: Session):
        """Cache session in Redis."""
        if self.redis:
            cache_key = f"session:{session.id}"
            session_data = {
                "id": session.id,
                "user_id": session.user_id,
                "token": session.token,
                "session_hash": session.session_hash,
                "ip_hash": session.ip_hash,
                "user_agent_hash": session.user_agent_hash,
                "last_activity": session.last_activity.isoformat(),
                "expires_at": session.expires_at.isoformat(),
                "is_active": session.is_active
            }
            ttl = int(settings.session_idle_timeout.total_seconds())
            await self.redis.setex(
                cache_key,
                ttl,
                json.dumps(session_data)
            )

    async def _get_cached_session(self, session_id: str) -> Optional[Session]:
        """Get session from Redis cache."""
        if self.redis:
            cache_key = f"session:{session_id}"
            data = await self.redis.get(cache_key)
            if data:
                session_data = json.loads(data)
                # Convert to Session object (simplified)
                return Session(**session_data)
        return None

    async def _remove_cached_session(self, session_id: str):
        """Remove session from Redis cache."""
        if self.redis:
            cache_key = f"session:{session_id}"
            await self.redis.delete(cache_key)

    async def _audit_log(
        self,
        action: str,
        user_id: str,
        details: dict
    ):
        """Create audit log entry."""
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type="SESSION",
            resource_id=details.get("session_id"),
            details=details,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(audit_entry)
        await self.db.commit()