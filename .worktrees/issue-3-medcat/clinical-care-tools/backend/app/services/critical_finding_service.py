"""Critical finding alert service for patient safety."""

import json
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.critical_finding_alert import CriticalFindingAlert, FindingSeverity
from app.models.document import Document
from app.models.patient import Patient
from app.models.user import User

logger = logging.getLogger(__name__)


class CriticalFindingService:
    """
    Critical finding alert service.

    Detects critical medical concepts in NLP-processed documents
    and creates alerts to notify clinicians.

    Critical concepts include:
    - Cancer diagnoses (malignant neoplasm)
    - Acute myocardial infarction
    - Stroke/CVA
    - Sepsis
    - Pulmonary embolism
    - Acute renal failure
    """

    # Critical SNOMED-CT/UMLS concept IDs
    CRITICAL_CONCEPTS = {
        "C0006826": {"name": "Malignant Neoplasm", "severity": FindingSeverity.CRITICAL},
        "C0027651": {"name": "Neoplasm", "severity": FindingSeverity.HIGH},
        "C0155626": {"name": "Acute Myocardial Infarction", "severity": FindingSeverity.CRITICAL},
        "C0038454": {"name": "Cerebrovascular Accident", "severity": FindingSeverity.CRITICAL},
        "C0036690": {"name": "Sepsis", "severity": FindingSeverity.CRITICAL},
        "C0034065": {"name": "Pulmonary Embolism", "severity": FindingSeverity.CRITICAL},
        "C0022660": {"name": "Acute Renal Failure", "severity": FindingSeverity.HIGH},
        "C0270611": {"name": "Brain Injuries", "severity": FindingSeverity.HIGH},
        "C0001339": {"name": "Acute Pancreatitis", "severity": FindingSeverity.HIGH},
    }

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db

    async def check_for_critical_findings(
        self,
        patient_id: UUID,
        document_id: UUID,
        detected_concepts: List[dict],
    ) -> List[CriticalFindingAlert]:
        """
        Check NLP-extracted concepts for critical findings.

        Args:
            patient_id: Patient UUID
            document_id: Document UUID where concepts were found
            detected_concepts: List of MedCAT-extracted concepts
                Each concept should have: cui, pretty_name, meta_anns

        Returns:
            List of created critical finding alerts
        """
        alerts_created = []

        for concept in detected_concepts:
            cui = concept.get("cui")
            if not cui:
                continue

            # Check if this is a critical concept
            if cui not in self.CRITICAL_CONCEPTS:
                continue

            # Check meta-annotations to avoid false positives
            meta_anns = concept.get("meta_anns", {})

            # Skip if negated ("Patient denies chest pain")
            if meta_anns.get("Negation") == "Negated":
                continue

            # Skip if not about patient ("Family history of cancer")
            if meta_anns.get("Experiencer") != "Patient":
                continue

            # Skip if historical/hypothetical
            temporality = meta_anns.get("Temporality", "Recent")
            if temporality in ["Historical", "Hypothetical"]:
                continue

            # Create alert
            critical_info = self.CRITICAL_CONCEPTS[cui]
            alert = await self._create_alert(
                patient_id=patient_id,
                document_id=document_id,
                concept_cui=cui,
                concept_name=concept.get("pretty_name", critical_info["name"]),
                severity=critical_info["severity"],
            )

            alerts_created.append(alert)

            logger.warning(
                f"Critical finding detected: {alert.concept_name} "
                f"(CUI: {cui}) for patient {patient_id}"
            )

        return alerts_created

    async def _create_alert(
        self,
        patient_id: UUID,
        document_id: UUID,
        concept_cui: str,
        concept_name: str,
        severity: FindingSeverity,
    ) -> CriticalFindingAlert:
        """Create a critical finding alert."""
        # Check if alert already exists for this concept/patient/document
        existing_query = select(CriticalFindingAlert).where(
            CriticalFindingAlert.patient_id == patient_id,
            CriticalFindingAlert.document_id == document_id,
            CriticalFindingAlert.concept_cui == concept_cui,
        )
        result = await self.db.execute(existing_query)
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(
                f"Alert already exists for {concept_name} "
                f"(patient {patient_id}, document {document_id})"
            )
            return existing

        # Create new alert
        alert = CriticalFindingAlert(
            patient_id=patient_id,
            document_id=document_id,
            concept_cui=concept_cui,
            concept_name=concept_name,
            severity=severity,
        )

        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)

        return alert

    async def acknowledge_alert(
        self,
        alert_id: UUID,
        user_id: UUID,
    ) -> CriticalFindingAlert:
        """
        Acknowledge a critical finding alert.

        Args:
            alert_id: Alert UUID
            user_id: User acknowledging the alert

        Returns:
            Updated alert

        Raises:
            ValueError: If alert not found
        """
        query = select(CriticalFindingAlert).where(CriticalFindingAlert.id == alert_id)
        result = await self.db.execute(query)
        alert = result.scalar_one_or_none()

        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(alert)

        logger.info(f"Alert {alert_id} acknowledged by user {user_id}")

        return alert

    async def get_unacknowledged_alerts(
        self,
        patient_id: Optional[UUID] = None,
        severity: Optional[FindingSeverity] = None,
    ) -> List[CriticalFindingAlert]:
        """
        Get unacknowledged critical finding alerts.

        Args:
            patient_id: Optional filter by patient
            severity: Optional filter by severity

        Returns:
            List of unacknowledged alerts
        """
        query = select(CriticalFindingAlert).where(
            CriticalFindingAlert.acknowledged_at.is_(None)
        )

        if patient_id:
            query = query.where(CriticalFindingAlert.patient_id == patient_id)

        if severity:
            query = query.where(CriticalFindingAlert.severity == severity)

        # Order by severity (critical first) then creation date
        query = query.order_by(
            CriticalFindingAlert.severity.desc(),
            CriticalFindingAlert.created_at.desc(),
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def notify_clinicians(
        self,
        alert: CriticalFindingAlert,
        user_ids: List[UUID],
    ) -> None:
        """
        Notify clinicians about critical finding.

        In production, this would send email/SMS/push notifications.
        For MVP, we just log the notification and update the alert.

        Args:
            alert: Critical finding alert
            user_ids: List of user IDs to notify
        """
        # Update alert with notification info
        alert.notified_users = json.dumps([str(uid) for uid in user_ids])
        alert.notification_sent_at = datetime.utcnow()

        await self.db.commit()

        # Log notification (in production, send actual notifications here)
        logger.info(
            f"Notification sent for critical finding: {alert.concept_name} "
            f"(severity: {alert.severity}) to {len(user_ids)} clinicians"
        )

        # TODO: Integrate with email service (SendGrid, AWS SES)
        # TODO: Integrate with SMS service (Twilio)
        # TODO: Integrate with push notification service (Firebase)
