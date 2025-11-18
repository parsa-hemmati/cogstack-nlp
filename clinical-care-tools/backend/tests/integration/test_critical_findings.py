"""Integration tests for critical finding alerts."""

from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.critical_finding_alert import CriticalFindingAlert, FindingSeverity
from app.models.document import Document, DocumentStatus, DocumentType
from app.services.critical_finding_service import CriticalFindingService


@pytest.mark.asyncio
class TestCriticalFindingAlerts:
    """Test critical finding alert system."""

    async def test_detect_critical_finding(self, db_session, test_patient):
        """Test critical concept detection creates alert."""
        # Create document
        doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=datetime.utcnow(),
            title="Pathology Report",
            status=DocumentStatus.COMPLETED,
        )
        db_session.add(doc)
        await db_session.commit()

        # Simulate MedCAT detecting malignant neoplasm
        detected_concepts = [
            {
                "cui": "C0006826",  # Malignant Neoplasm
                "pretty_name": "Malignant Neoplasm",
                "meta_anns": {
                    "Negation": "Affirmed",
                    "Experiencer": "Patient",
                    "Temporality": "Recent",
                },
            }
        ]

        # Check for critical findings
        service = CriticalFindingService(db_session)
        alerts = await service.check_for_critical_findings(
            patient_id=test_patient.id,
            document_id=doc.id,
            detected_concepts=detected_concepts,
        )

        # Verify alert created
        assert len(alerts) == 1
        assert alerts[0].concept_cui == "C0006826"
        assert alerts[0].severity == FindingSeverity.CRITICAL

    async def test_negated_finding_not_alerted(self, db_session, test_patient):
        """Test negated findings don't create alerts."""
        doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=datetime.utcnow(),
            title="Clinical Note",
            status=DocumentStatus.COMPLETED,
        )
        db_session.add(doc)
        await db_session.commit()

        # Negated finding (e.g., "No evidence of acute MI")
        detected_concepts = [
            {
                "cui": "C0155626",  # Acute MI
                "pretty_name": "Acute Myocardial Infarction",
                "meta_anns": {
                    "Negation": "Negated",  # Negated!
                    "Experiencer": "Patient",
                    "Temporality": "Recent",
                },
            }
        ]

        service = CriticalFindingService(db_session)
        alerts = await service.check_for_critical_findings(
            patient_id=test_patient.id,
            document_id=doc.id,
            detected_concepts=detected_concepts,
        )

        # No alert for negated finding
        assert len(alerts) == 0

    async def test_family_history_not_alerted(self, db_session, test_patient):
        """Test family history findings don't create alerts."""
        doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=datetime.utcnow(),
            title="Family History",
            status=DocumentStatus.COMPLETED,
        )
        db_session.add(doc)
        await db_session.commit()

        # Family history (not about patient)
        detected_concepts = [
            {
                "cui": "C0006826",  # Malignant Neoplasm
                "pretty_name": "Malignant Neoplasm",
                "meta_anns": {
                    "Negation": "Affirmed",
                    "Experiencer": "Family",  # Family, not patient!
                    "Temporality": "Historical",
                },
            }
        ]

        service = CriticalFindingService(db_session)
        alerts = await service.check_for_critical_findings(
            patient_id=test_patient.id,
            document_id=doc.id,
            detected_concepts=detected_concepts,
        )

        # No alert for family history
        assert len(alerts) == 0

    async def test_acknowledge_alert(
        self, client: AsyncClient, test_clinician_user, test_patient, db_session
    ):
        """Test clinician can acknowledge critical finding."""
        # Create alert
        alert = CriticalFindingAlert(
            patient_id=test_patient.id,
            concept_cui="C0038454",
            concept_name="Cerebrovascular Accident",
            severity=FindingSeverity.CRITICAL,
        )
        db_session.add(alert)
        await db_session.commit()

        # Login as clinician
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_clinician_user.email,
                "password": "clinicianpass123",
            },
        )
        token = login_response.json()["access_token"]

        # Acknowledge alert
        response = await client.post(
            f"/api/v1/critical-findings/{alert.id}/acknowledge",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_acknowledged"] is True
        assert data["acknowledged_by"] == str(test_clinician_user.id)

        # Verify audit log
        query = select(AuditLog).where(
            AuditLog.action == "CRITICAL_FINDING_ACKNOWLEDGED",
            AuditLog.resource_id == str(alert.id),
        )
        result = await db_session.execute(query)
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None

    async def test_list_unacknowledged_alerts(
        self, client: AsyncClient, test_clinician_user, test_patient, db_session
    ):
        """Test listing unacknowledged critical findings."""
        # Create acknowledged alert
        ack_alert = CriticalFindingAlert(
            patient_id=test_patient.id,
            concept_cui="C0038454",
            concept_name="Stroke",
            severity=FindingSeverity.CRITICAL,
            acknowledged_by=test_clinician_user.id,
            acknowledged_at=datetime.utcnow(),
        )
        db_session.add(ack_alert)

        # Create unacknowledged alert
        unack_alert = CriticalFindingAlert(
            patient_id=test_patient.id,
            concept_cui="C0036690",
            concept_name="Sepsis",
            severity=FindingSeverity.CRITICAL,
        )
        db_session.add(unack_alert)

        await db_session.commit()

        # Login as clinician
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_clinician_user.email,
                "password": "clinicianpass123",
            },
        )
        token = login_response.json()["access_token"]

        # List unacknowledged only
        response = await client.get(
            "/api/v1/critical-findings?unacknowledged_only=true",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should only return unacknowledged
        assert len(data) == 1
        assert data[0]["id"] == str(unack_alert.id)
        assert data[0]["is_acknowledged"] is False
