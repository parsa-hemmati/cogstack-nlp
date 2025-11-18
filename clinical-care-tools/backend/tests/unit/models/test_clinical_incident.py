"""Tests for clinical incident model."""

from datetime import datetime

import pytest
from sqlalchemy import select

from app.models.clinical_incident import (
    ClinicalIncident,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)


@pytest.mark.asyncio
class TestClinicalIncident:
    """Test clinical incident model."""

    async def test_create_incident(self, db_session, test_clinician_user, test_patient):
        """Test creating clinical incident."""
        incident = ClinicalIncident(
            incident_type=IncidentType.DATA_ACCURACY,
            severity=IncidentSeverity.MEDIUM,
            description="Patient's medication list shows drug A, but discharge summary shows drug B",
            patient_id=test_patient.id,
            reported_by=test_clinician_user.id,
            status=IncidentStatus.REPORTED,
        )

        db_session.add(incident)
        await db_session.commit()

        # Verify created
        query = select(ClinicalIncident).where(ClinicalIncident.id == incident.id)
        result = await db_session.execute(query)
        db_incident = result.scalar_one()

        assert db_incident.incident_type == IncidentType.DATA_ACCURACY
        assert db_incident.severity == IncidentSeverity.MEDIUM
        assert db_incident.status == IncidentStatus.REPORTED
        assert db_incident.patient_id == test_patient.id

    async def test_incident_severity_classification(self, db_session, test_clinician_user):
        """Test different severity levels."""
        # Low severity
        low_incident = ClinicalIncident(
            incident_type=IncidentType.USER_ERROR,
            severity=IncidentSeverity.LOW,
            description="User clicked wrong button but immediately corrected",
            reported_by=test_clinician_user.id,
        )
        db_session.add(low_incident)

        # Critical severity
        critical_incident = ClinicalIncident(
            incident_type=IncidentType.SAFETY_CONCERN,
            severity=IncidentSeverity.CRITICAL,
            description="NLP system failed to detect critical finding mentioned in report",
            reported_by=test_clinician_user.id,
        )
        db_session.add(critical_incident)

        await db_session.commit()

        assert low_incident.severity == IncidentSeverity.LOW
        assert critical_incident.severity == IncidentSeverity.CRITICAL

    async def test_incident_workflow(self, db_session, test_clinician_user, test_admin_user):
        """Test incident investigation workflow."""
        # Create incident
        incident = ClinicalIncident(
            incident_type=IncidentType.SYSTEM_ERROR,
            severity=IncidentSeverity.HIGH,
            description="System returned incorrect search results for patient cohort",
            reported_by=test_clinician_user.id,
            status=IncidentStatus.REPORTED,
        )
        db_session.add(incident)
        await db_session.commit()

        # Assign investigator
        incident.investigated_by = test_admin_user.id
        incident.status = IncidentStatus.UNDER_INVESTIGATION
        await db_session.commit()

        assert incident.status == IncidentStatus.UNDER_INVESTIGATION
        assert incident.investigated_by == test_admin_user.id

        # Resolve incident
        incident.resolution = "Bug in Elasticsearch query builder fixed. Deployed patch v1.2.1."
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.utcnow()
        await db_session.commit()

        assert incident.status == IncidentStatus.RESOLVED
        assert incident.resolution is not None
        assert incident.resolved_at is not None

    async def test_incident_types(self, db_session, test_clinician_user):
        """Test all incident types can be created."""
        types = [
            IncidentType.DATA_ACCURACY,
            IncidentType.SYSTEM_ERROR,
            IncidentType.USER_ERROR,
            IncidentType.SAFETY_CONCERN,
            IncidentType.PRIVACY_BREACH,
            IncidentType.OTHER,
        ]

        for incident_type in types:
            incident = ClinicalIncident(
                incident_type=incident_type,
                severity=IncidentSeverity.MEDIUM,
                description=f"Test incident of type {incident_type.value}",
                reported_by=test_clinician_user.id,
            )
            db_session.add(incident)

        await db_session.commit()

        # Verify all created
        query = select(ClinicalIncident)
        result = await db_session.execute(query)
        incidents = result.scalars().all()

        assert len(incidents) == len(types)
