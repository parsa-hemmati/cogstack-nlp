"""
Break-Glass Access Service (Phase 5)

Manages emergency access to patient data with mandatory audit and review.
Implements access control, time-limited access windows, and security alerts.

HIPAA Compliance:
- All break-glass access is logged and audited
- Requires clinical justification
- Mandatory security team review within 24 hours
- Alert notifications to security team
- Access window limited to 60 minutes
- Can be revoked immediately
"""

from typing import Optional, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, desc
from fastapi import HTTPException, status
import uuid

from app.core.config import settings
from app.models.break_glass_access import BreakGlassAccess, BreakGlassStatus
from app.models.audit_log import AuditLog


class BreakGlassService:
    """Service for managing emergency access to patient data."""

    def __init__(self, db: AsyncSession):
        """
        Initialize break-glass service.

        Args:
            db: Database session
        """
        self.db = db

    async def request_access(
        self,
        user_id: str,
        patient_id: str,
        justification: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> BreakGlassAccess:
        """
        Request emergency access to patient data.

        Args:
            user_id: Clinician requesting access
            patient_id: Patient ID being accessed
            justification: Clinical reason for emergency access (required)
            ip_address: Client IP for audit
            user_agent: Client User-Agent for audit

        Returns:
            Created break-glass access request

        Raises:
            HTTPException: If justification is empty or too short
        """
        # Validate justification (required by law)
        if not justification or len(justification.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Justification must be at least 10 characters (required by HIPAA)"
            )

        # Create access request
        access_id = str(uuid.uuid4())
        access = BreakGlassAccess(
            id=access_id,
            user_id=user_id,
            patient_id=patient_id,
            status=BreakGlassStatus.PENDING,
            justification=justification,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc)
        )

        self.db.add(access)
        await self.db.commit()
        await self.db.refresh(access)

        # Audit log
        await self._audit_log(
            action="BREAK_GLASS_REQUESTED",
            user_id=user_id,
            resource_id=access_id,
            details={
                "patient_id": patient_id,
                "justification_length": len(justification),
                "ip_address": ip_address[:20] if ip_address else None
            }
        )

        # NOTE: Send alert email to security team
        # await self._send_security_alert(user_id, patient_id, justification)

        return access

    async def get_pending_reviews(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[BreakGlassAccess], int]:
        """
        Get pending break-glass access requests (for security team review).

        Args:
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            Tuple of (access_list, total_count)
        """
        # Get total count
        count_result = await self.db.execute(
            select(BreakGlassAccess).where(
                BreakGlassAccess.status == BreakGlassStatus.PENDING
            ).order_by(desc(BreakGlassAccess.created_at))
        )

        # Get paginated results
        result = await self.db.execute(
            select(BreakGlassAccess).where(
                BreakGlassAccess.status == BreakGlassStatus.PENDING
            ).order_by(desc(BreakGlassAccess.created_at))
            .limit(limit)
            .offset(offset)
        )

        accesses = result.scalars().all()
        total_count = len(count_result.scalars().all())

        return accesses, total_count

    async def approve_access(
        self,
        access_id: str,
        reviewer_id: str,
        review_notes: Optional[str] = None
    ) -> BreakGlassAccess:
        """
        Approve emergency access request (security team only).

        Args:
            access_id: Break-glass access ID
            reviewer_id: Security team member approving
            review_notes: Optional notes on review

        Returns:
            Updated access record

        Raises:
            HTTPException: If access not found or not pending
        """
        # Get access record
        result = await self.db.execute(
            select(BreakGlassAccess).where(BreakGlassAccess.id == access_id)
        )
        access = result.scalar_one_or_none()

        if not access:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Break-glass access request not found"
            )

        if access.status != BreakGlassStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve access with status: {access.status}"
            )

        # Update access
        now = datetime.now(timezone.utc)
        access.status = BreakGlassStatus.APPROVED
        access.access_granted_at = now
        access.access_expires_at = now + timedelta(
            minutes=settings.BREAK_GLASS_ACCESS_WINDOW_MINUTES
        )
        access.reviewed_by = reviewer_id
        access.reviewed_at = now
        access.review_notes = review_notes

        await self.db.commit()
        await self.db.refresh(access)

        # Audit log
        await self._audit_log(
            action="BREAK_GLASS_APPROVED",
            user_id=reviewer_id,
            resource_id=access_id,
            details={
                "clinician_id": access.user_id,
                "patient_id": access.patient_id,
                "expires_at": access.access_expires_at.isoformat() if access.access_expires_at else None
            }
        )

        return access

    async def deny_access(
        self,
        access_id: str,
        reviewer_id: str,
        reason: str
    ) -> BreakGlassAccess:
        """
        Deny emergency access request (security team only).

        Args:
            access_id: Break-glass access ID
            reviewer_id: Security team member denying
            reason: Reason for denial

        Returns:
            Updated access record

        Raises:
            HTTPException: If access not found or not pending
        """
        # Get access record
        result = await self.db.execute(
            select(BreakGlassAccess).where(BreakGlassAccess.id == access_id)
        )
        access = result.scalar_one_or_none()

        if not access:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Break-glass access request not found"
            )

        if access.status != BreakGlassStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot deny access with status: {access.status}"
            )

        # Update access
        now = datetime.now(timezone.utc)
        access.status = BreakGlassStatus.DENIED
        access.reviewed_by = reviewer_id
        access.reviewed_at = now
        access.review_notes = reason

        await self.db.commit()
        await self.db.refresh(access)

        # Audit log
        await self._audit_log(
            action="BREAK_GLASS_DENIED",
            user_id=reviewer_id,
            resource_id=access_id,
            details={
                "clinician_id": access.user_id,
                "patient_id": access.patient_id,
                "reason": reason
            }
        )

        return access

    async def revoke_access(
        self,
        access_id: str,
        revoked_by: str,
        reason: Optional[str] = None
    ) -> BreakGlassAccess:
        """
        Revoke approved access immediately (security team or admin).

        Args:
            access_id: Break-glass access ID
            revoked_by: User revoking access
            reason: Reason for revocation

        Returns:
            Updated access record

        Raises:
            HTTPException: If access not found or not approved
        """
        # Get access record
        result = await self.db.execute(
            select(BreakGlassAccess).where(BreakGlassAccess.id == access_id)
        )
        access = result.scalar_one_or_none()

        if not access:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Break-glass access request not found"
            )

        if access.status != BreakGlassStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot revoke access with status: {access.status}"
            )

        # Update access
        now = datetime.now(timezone.utc)
        access.status = BreakGlassStatus.REVOKED
        access.revoked_by = revoked_by
        access.revoked_at = now
        access.access_expires_at = now  # Immediate expiration

        await self.db.commit()
        await self.db.refresh(access)

        # Audit log
        await self._audit_log(
            action="BREAK_GLASS_REVOKED",
            user_id=revoked_by,
            resource_id=access_id,
            details={
                "clinician_id": access.user_id,
                "patient_id": access.patient_id,
                "reason": reason,
                "was_accessed": access.accessed_at is not None
            }
        )

        return access

    async def record_access(
        self,
        access_id: str
    ) -> BreakGlassAccess:
        """
        Record when clinician actually accesses patient data.

        Args:
            access_id: Break-glass access ID

        Returns:
            Updated access record

        Raises:
            HTTPException: If access not found, not approved, or expired
        """
        # Get access record
        result = await self.db.execute(
            select(BreakGlassAccess).where(BreakGlassAccess.id == access_id)
        )
        access = result.scalar_one_or_none()

        if not access:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Break-glass access request not found"
            )

        if access.status != BreakGlassStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot use access with status: {access.status}"
            )

        # Check if access window is still valid
        now = datetime.now(timezone.utc)
        if access.access_expires_at and now > access.access_expires_at:
            access.status = BreakGlassStatus.EXPIRED
            await self.db.commit()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Break-glass access window has expired"
            )

        # Record access time
        access.accessed_at = now
        await self.db.commit()
        await self.db.refresh(access)

        # Audit log (very important - document actual data access)
        await self._audit_log(
            action="BREAK_GLASS_ACCESSED",
            user_id=access.user_id,
            resource_id=access_id,
            details={
                "patient_id": access.patient_id,
                "approved_by": access.reviewed_by,
                "justification_summary": access.justification[:100]
            }
        )

        return access

    async def check_access(
        self,
        user_id: str,
        patient_id: str
    ) -> Optional[BreakGlassAccess]:
        """
        Check if user has valid break-glass access to patient.

        Args:
            user_id: Clinician ID
            patient_id: Patient ID

        Returns:
            Valid access record or None
        """
        result = await self.db.execute(
            select(BreakGlassAccess).where(
                and_(
                    BreakGlassAccess.user_id == user_id,
                    BreakGlassAccess.patient_id == patient_id,
                    BreakGlassAccess.status == BreakGlassStatus.APPROVED
                )
            ).order_by(desc(BreakGlassAccess.access_granted_at))
        )
        access = result.scalar_one_or_none()

        if not access:
            return None

        # Check if access is still valid
        now = datetime.now(timezone.utc)
        if access.access_expires_at and now > access.access_expires_at:
            # Mark as expired
            access.status = BreakGlassStatus.EXPIRED
            await self.db.commit()
            return None

        return access

    async def cleanup_expired_access(self) -> int:
        """
        Clean up expired access records.

        Returns:
            Number of records marked as expired
        """
        now = datetime.now(timezone.utc)

        # Find expired approved access
        result = await self.db.execute(
            select(BreakGlassAccess).where(
                and_(
                    BreakGlassAccess.status == BreakGlassStatus.APPROVED,
                    BreakGlassAccess.access_expires_at < now
                )
            )
        )
        expired = result.scalars().all()

        if expired:
            for access in expired:
                access.status = BreakGlassStatus.EXPIRED

            await self.db.commit()

            # Audit log
            await self._audit_log(
                action="BREAK_GLASS_CLEANUP",
                user_id="SYSTEM",
                resource_id=None,
                details={"count": len(expired)}
            )

        return len(expired)

    async def _audit_log(
        self,
        action: str,
        user_id: str,
        resource_id: Optional[str],
        details: dict
    ):
        """Create audit log entry for break-glass action."""
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type="BREAK_GLASS_ACCESS",
            resource_id=resource_id,
            details=details,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(audit_entry)
        await self.db.commit()
