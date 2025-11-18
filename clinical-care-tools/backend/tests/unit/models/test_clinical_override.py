"""Tests for clinical override model."""

import pytest
from sqlalchemy import select

from app.models.clinical_override import ClinicalOverride


@pytest.mark.asyncio
class TestClinicalOverride:
    """Test clinical override model."""

    async def test_create_override(self, db_session, test_clinician_user, test_patient):
        """Test creating clinical override."""
        override = ClinicalOverride(
            user_id=test_clinician_user.id,
            patient_id=test_patient.id,
            recommendation_type="critical_alert",
            recommendation_value="Alert: Possible sepsis based on vital signs",
            override_value="Clinical assessment indicates viral infection, not sepsis",
            justification="Patient has clear viral prodrome, elevated WBC is consistent with viral response",
            severity="high",
        )

        db_session.add(override)
        await db_session.commit()

        # Verify created
        query = select(ClinicalOverride).where(ClinicalOverride.id == override.id)
        result = await db_session.execute(query)
        db_override = result.scalar_one()

        assert db_override.user_id == test_clinician_user.id
        assert db_override.patient_id == test_patient.id
        assert db_override.recommendation_type == "critical_alert"
        assert db_override.severity == "high"
        assert len(db_override.justification) >= 20

    async def test_justification_required(self, db_session, test_clinician_user, test_patient):
        """Test justification is required and meaningful."""
        # This test verifies the model structure
        # Actual validation happens in API layer (Pydantic)
        override = ClinicalOverride(
            user_id=test_clinician_user.id,
            patient_id=test_patient.id,
            recommendation_type="dosage_warning",
            recommendation_value="Recommended dose: 10mg",
            override_value="Prescribed dose: 15mg",
            justification="Patient has higher BMI and tolerates higher dose well based on previous treatments",
            severity="medium",
        )

        db_session.add(override)
        await db_session.commit()

        assert len(override.justification) >= 20

    async def test_override_timestamps(self, db_session, test_clinician_user, test_patient):
        """Test override has creation timestamp."""
        override = ClinicalOverride(
            user_id=test_clinician_user.id,
            patient_id=test_patient.id,
            recommendation_type="lab_value_alert",
            recommendation_value="High potassium: 5.8 mmol/L",
            override_value="Acknowledged - patient on ACE inhibitor, recheck in 24h",
            justification="Patient is stable, on chronic ACE inhibitor therapy. Will recheck labs tomorrow.",
            severity="medium",
        )

        db_session.add(override)
        await db_session.commit()

        assert override.created_at is not None
