"""Tests for critical finding service."""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.critical_finding_alert import CriticalFindingAlert, FindingSeverity
from app.models.document import Document, DocumentStatus, DocumentType
from app.services.critical_finding_service import CriticalFindingService


@pytest.mark.asyncio
class TestCriticalFindingService:
    """Test critical finding service."""

    async def test_detect_critical_concept(self, db_session, test_patient):
        """Test detection of critical medical concept."""
        # Create document
        doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=datetime.utcnow(),
            title="Test Document",
            status=DocumentStatus.COMPLETED,
        )
        db_session.add(doc)
        await db_session.commit()

        # Simulate MedCAT detecting cancer
        concepts = [
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

        service = CriticalFindingService(db_session)
        alerts = await service.check_for_critical_findings(
            patient_id=test_patient.id,
            document_id=doc.id,
            detected_concepts=concepts,
        )

        assert len(alerts) == 1
        assert alerts[0].concept_cui == "C0006826"
        assert alerts[0].severity == FindingSeverity.CRITICAL

    async def test_negated_not_alerted(self, db_session, test_patient):
        """Test negated findings don't create alerts."""
        doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=datetime.utcnow(),
            title="Test",
            status=DocumentStatus.COMPLETED,
        )
        db_session.add(doc)
        await db_session.commit()

        # Negated: "No evidence of MI"
        concepts = [
            {
                "cui": "C0155626",  # Acute MI
                "pretty_name": "Acute MI",
                "meta_anns": {
                    "Negation": "Negated",
                    "Experiencer": "Patient",
                    "Temporality": "Recent",
                },
            }
        ]

        service = CriticalFindingService(db_session)
        alerts = await service.check_for_critical_findings(
            patient_id=test_patient.id,
            document_id=doc.id,
            detected_concepts=concepts,
        )

        assert len(alerts) == 0

    async def test_family_history_not_alerted(self, db_session, test_patient):
        """Test family history doesn't create alerts."""
        doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=datetime.utcnow(),
            title="Test",
            status=DocumentStatus.COMPLETED,
        )
        db_session.add(doc)
        await db_session.commit()

        # Family history
        concepts = [
            {
                "cui": "C0006826",  # Cancer
                "pretty_name": "Malignant Neoplasm",
                "meta_anns": {
                    "Negation": "Affirmed",
                    "Experiencer": "Family",  # Not patient!
                    "Temporality": "Historical",
                },
            }
        ]

        service = CriticalFindingService(db_session)
        alerts = await service.check_for_critical_findings(
            patient_id=test_patient.id,
            document_id=doc.id,
            detected_concepts=concepts,
        )

        assert len(alerts) == 0

    async def test_historical_not_alerted(self, db_session, test_patient):
        """Test historical findings don't create alerts."""
        doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=datetime.utcnow(),
            title="Test",
            status=DocumentStatus.COMPLETED,
        )
        db_session.add(doc)
        await db_session.commit()

        # Historical
        concepts = [
            {
                "cui": "C0155626",  # MI
                "pretty_name": "Myocardial Infarction",
                "meta_anns": {
                    "Negation": "Affirmed",
                    "Experiencer": "Patient",
                    "Temporality": "Historical",  # Old MI
                },
            }
        ]

        service = CriticalFindingService(db_session)
        alerts = await service.check_for_critical_findings(
            patient_id=test_patient.id,
            document_id=doc.id,
            detected_concepts=concepts,
        )

        assert len(alerts) == 0

    async def test_acknowledge_alert(self, db_session, test_patient, test_clinician_user):
        """Test acknowledging critical finding alert."""
        # Create alert
        alert = CriticalFindingAlert(
            patient_id=test_patient.id,
            concept_cui="C0038454",
            concept_name="Stroke",
            severity=FindingSeverity.CRITICAL,
        )
        db_session.add(alert)
        await db_session.commit()

        # Acknowledge
        service = CriticalFindingService(db_session)
        updated = await service.acknowledge_alert(
            alert_id=alert.id,
            user_id=test_clinician_user.id,
        )

        assert updated.acknowledged_by == test_clinician_user.id
        assert updated.acknowledged_at is not None
        assert updated.is_acknowledged is True

    async def test_get_unacknowledged_alerts(self, db_session, test_patient, test_clinician_user):
        """Test getting unacknowledged alerts."""
        # Create acknowledged alert
        ack = CriticalFindingAlert(
            patient_id=test_patient.id,
            concept_cui="C0038454",
            concept_name="Stroke",
            severity=FindingSeverity.HIGH,
            acknowledged_by=test_clinician_user.id,
            acknowledged_at=datetime.utcnow(),
        )
        db_session.add(ack)

        # Create unacknowledged alert
        unack = CriticalFindingAlert(
            patient_id=test_patient.id,
            concept_cui="C0036690",
            concept_name="Sepsis",
            severity=FindingSeverity.CRITICAL,
        )
        db_session.add(unack)

        await db_session.commit()

        # Get unacknowledged
        service = CriticalFindingService(db_session)
        alerts = await service.get_unacknowledged_alerts()

        assert len(alerts) == 1
        assert alerts[0].id == unack.id

    async def test_duplicate_alert_not_created(self, db_session, test_patient):
        """Test duplicate alerts are not created."""
        doc = Document(
            patient_id=test_patient.id,
            document_type=DocumentType.CLINICAL_NOTE,
            document_date=datetime.utcnow(),
            title="Test",
            status=DocumentStatus.COMPLETED,
        )
        db_session.add(doc)
        await db_session.commit()

        concepts = [
            {
                "cui": "C0006826",
                "pretty_name": "Malignant Neoplasm",
                "meta_anns": {
                    "Negation": "Affirmed",
                    "Experiencer": "Patient",
                    "Temporality": "Recent",
                },
            }
        ]

        service = CriticalFindingService(db_session)

        # Create first alert
        alerts1 = await service.check_for_critical_findings(
            patient_id=test_patient.id,
            document_id=doc.id,
            detected_concepts=concepts,
        )

        # Try to create duplicate
        alerts2 = await service.check_for_critical_findings(
            patient_id=test_patient.id,
            document_id=doc.id,
            detected_concepts=concepts,
        )

        # Should return existing alert, not create new one
        assert len(alerts1) == 1
        assert len(alerts2) == 1
        assert alerts1[0].id == alerts2[0].id

        # Verify only one alert in database
        query = select(CriticalFindingAlert).where(
            CriticalFindingAlert.patient_id == test_patient.id
        )
        result = await db_session.execute(query)
        all_alerts = result.scalars().all()
        assert len(all_alerts) == 1
