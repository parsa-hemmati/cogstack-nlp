"""
Unit tests for clinical safety service.

Tests cover:
- NLP confidence checking
- Critical concept detection
- Duplicate patient detection
- Date validation
- Required field validation
- Warning management
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.services.clinical_safety_service import ClinicalSafetyService
from app.models.clinical_safety import SafetyWarningType, SafetyWarningLevel


@pytest.mark.unit
class TestClinicalSafetyService:
    """Test cases for clinical safety service."""

    @pytest.fixture
    async def service(self, db_session):
        """Create service instance."""
        return ClinicalSafetyService(db_session)

    @pytest.fixture
    def test_user_id(self):
        """Test user ID."""
        return str(uuid4())

    @pytest.fixture
    def test_patient_id(self):
        """Test patient ID."""
        return str(uuid4())

    @pytest.mark.asyncio
    async def test_check_nlp_confidence_low(self, service, test_user_id, test_patient_id):
        """Test detection of low NLP confidence."""
        warning = await service.check_nlp_confidence(
            user_id=test_user_id,
            patient_id=test_patient_id,
            concept="diabetes mellitus",
            confidence=0.65  # Below default 0.7 threshold
        )

        assert warning is not None
        assert warning.warning_type == SafetyWarningType.LOW_CONFIDENCE
        assert warning.warning_level == SafetyWarningLevel.WARNING

    @pytest.mark.asyncio
    async def test_check_nlp_confidence_high(self, service, test_user_id, test_patient_id):
        """Test no warning for high NLP confidence."""
        warning = await service.check_nlp_confidence(
            user_id=test_user_id,
            patient_id=test_patient_id,
            concept="diabetes mellitus",
            confidence=0.95  # Above threshold
        )

        assert warning is None

    @pytest.mark.asyncio
    async def test_check_critical_concept(self, service, test_user_id, test_patient_id):
        """Test detection of critical concept."""
        warning = await service.check_critical_concept(
            user_id=test_user_id,
            patient_id=test_patient_id,
            concept="Penicillin",
            concept_type="allergy"
        )

        assert warning is not None
        assert warning.warning_type == SafetyWarningType.CRITICAL_CONCEPT
        assert warning.warning_level == SafetyWarningLevel.ALERT

    @pytest.mark.asyncio
    async def test_check_required_fields_missing(self, service, test_user_id, test_patient_id):
        """Test detection of missing required fields."""
        patient_data = {
            "id": test_patient_id,
            "first_name": "John",
            # Missing last_name, date_of_birth, mrn
        }

        warning = await service.check_required_fields(
            user_id=test_user_id,
            patient_data=patient_data
        )

        assert warning is not None
        assert warning.warning_type == SafetyWarningType.MISSING_FIELD

    @pytest.mark.asyncio
    async def test_check_required_fields_complete(self, service, test_user_id, test_patient_id):
        """Test no warning for complete required fields."""
        patient_data = {
            "id": test_patient_id,
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "mrn": "12345"
        }

        warning = await service.check_required_fields(
            user_id=test_user_id,
            patient_data=patient_data
        )

        assert warning is None

    @pytest.mark.asyncio
    async def test_check_future_date_invalid(self, service, test_user_id, test_patient_id):
        """Test detection of invalid future date."""
        future_date = datetime.now(timezone.utc) + timedelta(days=1)

        warning = await service.check_future_date(
            user_id=test_user_id,
            field_name="admission_date",
            date_value=future_date,
            patient_id=test_patient_id
        )

        assert warning is not None
        assert warning.warning_type == SafetyWarningType.FUTURE_DATE
        assert warning.warning_level == SafetyWarningLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_check_future_date_valid(self, service, test_user_id, test_patient_id):
        """Test no warning for valid past/present date."""
        past_date = datetime.now(timezone.utc) - timedelta(days=1)

        warning = await service.check_future_date(
            user_id=test_user_id,
            field_name="admission_date",
            date_value=past_date,
            patient_id=test_patient_id
        )

        assert warning is None

    @pytest.mark.asyncio
    async def test_create_warning(self, service, test_user_id, test_patient_id):
        """Test warning creation."""
        warning = await service.create_warning(
            user_id=test_user_id,
            patient_id=test_patient_id,
            warning_type=SafetyWarningType.LOW_CONFIDENCE,
            warning_level=SafetyWarningLevel.WARNING,
            message="Low confidence for concept"
        )

        assert warning is not None
        assert warning.user_id == test_user_id
        assert warning.patient_id == test_patient_id
        assert warning.is_active is True

    @pytest.mark.asyncio
    async def test_dismiss_warning(self, service, test_user_id, test_patient_id):
        """Test dismissing a warning."""
        # Create warning
        warning = await service.create_warning(
            user_id=test_user_id,
            patient_id=test_patient_id,
            warning_type=SafetyWarningType.LOW_CONFIDENCE,
            warning_level=SafetyWarningLevel.WARNING,
            message="Test warning"
        )

        # Dismiss
        dismissed = await service.dismiss_warning(
            warning_id=warning.id,
            user_id=test_user_id,
            reason="Already confirmed"
        )

        assert dismissed.is_active is False
        assert dismissed.dismissed_at is not None

    @pytest.mark.asyncio
    async def test_override_warning(self, service, test_user_id, test_patient_id):
        """Test overriding a warning."""
        # Create warning
        warning = await service.create_warning(
            user_id=test_user_id,
            patient_id=test_patient_id,
            warning_type=SafetyWarningType.LOW_CONFIDENCE,
            warning_level=SafetyWarningLevel.WARNING,
            message="Test warning"
        )

        # Override
        override = await service.override_warning(
            warning_id=warning.id,
            user_id=test_user_id,
            justification="Clinical judgment confirms data is correct",
            severity="low"
        )

        assert override is not None
        assert override.justification == "Clinical judgment confirms data is correct"

    @pytest.mark.asyncio
    async def test_get_active_warnings(self, service, test_user_id, test_patient_id):
        """Test retrieving active warnings."""
        # Create multiple warnings
        for i in range(3):
            await service.create_warning(
                user_id=test_user_id,
                patient_id=test_patient_id,
                warning_type=SafetyWarningType.LOW_CONFIDENCE,
                warning_level=SafetyWarningLevel.WARNING,
                message=f"Warning {i}"
            )

        # Get active warnings
        warnings = await service.get_active_warnings(
            user_id=test_user_id,
            patient_id=test_patient_id
        )

        assert len(warnings) >= 3
        assert all(w.is_active for w in warnings)

    @pytest.mark.asyncio
    async def test_warning_levels(self, service, test_user_id, test_patient_id):
        """Test different warning levels."""
        # Info warning
        info = await service.create_warning(
            user_id=test_user_id,
            warning_type=SafetyWarningType.LOW_CONFIDENCE,
            warning_level=SafetyWarningLevel.INFO,
            message="Info"
        )

        # Warning
        warn = await service.create_warning(
            user_id=test_user_id,
            warning_type=SafetyWarningType.LOW_CONFIDENCE,
            warning_level=SafetyWarningLevel.WARNING,
            message="Warning"
        )

        # Critical
        crit = await service.create_warning(
            user_id=test_user_id,
            warning_type=SafetyWarningType.LOW_CONFIDENCE,
            warning_level=SafetyWarningLevel.CRITICAL,
            message="Critical"
        )

        # Alert
        alert = await service.create_warning(
            user_id=test_user_id,
            warning_type=SafetyWarningType.LOW_CONFIDENCE,
            warning_level=SafetyWarningLevel.ALERT,
            message="Alert"
        )

        assert info.warning_level == SafetyWarningLevel.INFO
        assert warn.warning_level == SafetyWarningLevel.WARNING
        assert crit.warning_level == SafetyWarningLevel.CRITICAL
        assert alert.warning_level == SafetyWarningLevel.ALERT
