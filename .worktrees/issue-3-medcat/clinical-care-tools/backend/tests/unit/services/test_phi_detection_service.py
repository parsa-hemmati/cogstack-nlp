"""Unit tests for PHI Detection Service (Sprint 4, Phase 4.1, Task 4.1.2)"""

import pytest
from app.services.phi.phi_detection_service import PHIDetectionService
from app.schemas.phi import PHIEntityType


class TestPHIDetectionService:
    """Test PHI detection service"""

    @pytest.fixture
    def service(self):
        """Create PHI detection service"""
        return PHIDetectionService(use_mock=True)

    @pytest.mark.asyncio
    async def test_detect_person_names(self, service):
        """Test detection of person names"""
        text = "Patient John Doe was treated by Dr. Jane Smith."
        entities = await service.detect_phi(text)

        person_entities = [e for e in entities if e.label == PHIEntityType.PERSON]
        assert len(person_entities) >= 2

        texts = [e.text for e in person_entities]
        assert any("John Doe" in t for t in texts)
        assert any("Jane Smith" in t for t in texts)

    @pytest.mark.asyncio
    async def test_detect_dates(self, service):
        """Test detection of dates"""
        text = "Patient DOB: 01/15/1980. Admission date: 2023-11-17."
        entities = await service.detect_phi(text)

        date_entities = [e for e in entities if e.label == PHIEntityType.DATE]
        assert len(date_entities) >= 2

        texts = [e.text for e in date_entities]
        assert any("01/15/1980" in t for t in texts)
        assert any("2023-11-17" in t for t in texts)

    @pytest.mark.asyncio
    async def test_detect_ssn(self, service):
        """Test detection of SSN"""
        text = "Patient SSN: 123-45-6789"
        entities = await service.detect_phi(text)

        id_entities = [e for e in entities if e.label == PHIEntityType.ID]
        assert len(id_entities) >= 1
        assert any("123-45-6789" in e.text for e in id_entities)

    @pytest.mark.asyncio
    async def test_detect_mrn(self, service):
        """Test detection of MRN"""
        text = "MRN: 12345678"
        entities = await service.detect_phi(text)

        id_entities = [e for e in entities if e.label == PHIEntityType.ID]
        assert len(id_entities) >= 1
        assert any("MRN" in e.text for e in id_entities)

    @pytest.mark.asyncio
    async def test_detect_address(self, service):
        """Test detection of addresses"""
        text = "Patient lives at 123 Main Street, New York, NY 10001"
        entities = await service.detect_phi(text)

        location_entities = [e for e in entities if e.label == PHIEntityType.LOCATION]
        assert len(location_entities) >= 1

    @pytest.mark.asyncio
    async def test_detect_phone(self, service):
        """Test detection of phone numbers"""
        text = "Contact: (555) 123-4567 or 555-987-6543"
        entities = await service.detect_phi(text)

        phone_entities = [e for e in entities if e.label == PHIEntityType.PHONE]
        assert len(phone_entities) >= 1

    @pytest.mark.asyncio
    async def test_detect_email(self, service):
        """Test detection of email addresses"""
        text = "Email: patient@example.com"
        entities = await service.detect_phi(text)

        email_entities = [e for e in entities if e.label == PHIEntityType.EMAIL]
        assert len(email_entities) == 1
        assert email_entities[0].text == "patient@example.com"

    @pytest.mark.asyncio
    async def test_detect_age_over_89(self, service):
        """Test detection of ages over 89 (HIPAA requirement)"""
        text = "Patient is 92 years old"
        entities = await service.detect_phi(text)

        age_entities = [e for e in entities if e.label == PHIEntityType.AGE]
        assert len(age_entities) >= 1

    @pytest.mark.asyncio
    async def test_entity_positions_correct(self, service):
        """Test that entity positions are accurate"""
        text = "Patient John Doe (DOB: 01/15/1980)"
        entities = await service.detect_phi(text)

        for entity in entities:
            # Verify entity text matches substring
            assert text[entity.start:entity.end] == entity.text
            # Verify positions are valid
            assert entity.start >= 0
            assert entity.end > entity.start
            assert entity.end <= len(text)

    @pytest.mark.asyncio
    async def test_confidence_scores_valid(self, service):
        """Test that confidence scores are in valid range"""
        text = "Patient John Doe (DOB: 01/15/1980, SSN: 123-45-6789)"
        entities = await service.detect_phi(text)

        for entity in entities:
            assert 0.0 <= entity.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_multiple_entities_same_type(self, service):
        """Test detection of multiple entities of same type"""
        text = "Dr. John Doe referred patient to Dr. Jane Smith"
        entities = await service.detect_phi(text)

        person_entities = [e for e in entities if e.label == PHIEntityType.PERSON]
        assert len(person_entities) >= 2

    @pytest.mark.asyncio
    async def test_no_phi_returns_empty(self, service):
        """Test that text without PHI returns empty list"""
        text = "The patient presents with chest pain and shortness of breath."
        entities = await service.detect_phi(text)

        # Should detect no PHI (generic clinical terms)
        assert len(entities) == 0 or all(e.label != PHIEntityType.PERSON for e in entities)

    @pytest.mark.asyncio
    async def test_filter_false_positive_person_names(self, service):
        """Test filtering of false positive person names"""
        text = "Patient was seen in the Emergency Department."
        entities = await service.detect_phi(text)

        # "Emergency Department" should not be detected as PERSON
        person_entities = [e for e in entities if e.label == PHIEntityType.PERSON]
        assert not any("Emergency Department" in e.text for e in person_entities)

    @pytest.mark.asyncio
    async def test_overlapping_entities_handled(self, service):
        """Test that overlapping entities are handled correctly"""
        text = "John Doe Smith"  # Could be "John Doe" or "Doe Smith"
        entities = await service.detect_phi(text)

        # Should not have overlapping entities
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # No overlap
                assert not (entity1.start < entity2.end and entity1.end > entity2.start)

    @pytest.mark.asyncio
    async def test_comprehensive_clinical_note(self, service):
        """Test detection in comprehensive clinical note"""
        text = """
        Patient: John Doe
        DOB: 01/15/1980
        MRN: 12345678
        SSN: 123-45-6789
        Address: 123 Main Street, New York, NY 10001
        Phone: (555) 123-4567
        Email: jdoe@example.com

        Chief Complaint: Chest pain

        History: Patient is a 43-year-old male presenting with chest pain.
        Patient was referred by Dr. Jane Smith.

        Examination reveals tenderness to palpation over the left chest wall.

        Plan: Continue current medications. Follow-up in 2 weeks.
        """
        entities = await service.detect_phi(text)

        # Should detect multiple types
        entity_types = {e.label for e in entities}
        assert PHIEntityType.PERSON in entity_types
        assert PHIEntityType.DATE in entity_types
        assert PHIEntityType.ID in entity_types
        assert PHIEntityType.LOCATION in entity_types or PHIEntityType.PHONE in entity_types

        # Should detect at least 5 entities total
        assert len(entities) >= 5

    @pytest.mark.asyncio
    async def test_sorted_by_position(self, service):
        """Test that entities are sorted by start position"""
        text = "Patient John Doe (DOB: 01/15/1980, SSN: 123-45-6789)"
        entities = await service.detect_phi(text)

        # Verify sorted order
        for i in range(len(entities) - 1):
            assert entities[i].start <= entities[i+1].start

    @pytest.mark.asyncio
    async def test_empty_text(self, service):
        """Test handling of empty text"""
        entities = await service.detect_phi("")
        assert entities == []

    @pytest.mark.asyncio
    async def test_whitespace_only(self, service):
        """Test handling of whitespace-only text"""
        entities = await service.detect_phi("   \n\t  ")
        assert entities == []

    @pytest.mark.asyncio
    async def test_special_characters(self, service):
        """Test handling of special characters"""
        text = "Patient: <REDACTED> DOB: **PROTECTED**"
        # Should not crash
        entities = await service.detect_phi(text)
        assert isinstance(entities, list)
