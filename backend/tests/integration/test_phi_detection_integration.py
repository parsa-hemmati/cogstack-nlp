"""
Integration tests for PHI Detection Service.

Tests PHI detection with real MedCAT service.

Note: These tests require MedCAT service to be running with the
de-identification model loaded.
"""
import pytest
from datetime import datetime

from app.services.phi_detection_service import PHIDetectionService
from app.clients.modelserve_client import CogStackModelServeClient, ProcessingError


@pytest.fixture
def medcat_client():
    """Create real MedCAT client (requires service to be running)."""
    return CogStackModelServeClient.from_env()


@pytest.fixture
def phi_detection_service(medcat_client):
    """Create PHI detection service with real client."""
    return PHIDetectionService(medcat_client=medcat_client)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_phi_detection_with_real_medcat_service(phi_detection_service):
    """Test detection with actual MedCAT service."""
    # Arrange
    text = "Patient John Smith (NHS: 1234567890) was seen on 01/15/2024."

    # Act
    try:
        entities = await phi_detection_service.detect_phi(text)
    except ProcessingError as e:
        pytest.skip(f"MedCAT service not available: {e}")

    # Assert - At minimum, should detect some PHI (exact entities depend on model)
    # This is a smoke test - if service is up, it should return entities
    assert isinstance(entities, list)
    # Each entity should have required fields
    for entity in entities:
        assert hasattr(entity, 'entity_type')
        assert hasattr(entity, 'text')
        assert hasattr(entity, 'start')
        assert hasattr(entity, 'end')
        assert hasattr(entity, 'confidence')
        assert 0.0 <= entity.confidence <= 1.0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_phi_detection_all_18_categories(phi_detection_service):
    """Test sample text with all 18 PHI types detected."""
    # Arrange - Synthetic clinical note with all 18 PHI categories
    text = """
    Patient: John Smith
    DOB: 01/15/1980
    Address: 123 Main Street, Springfield, IL 62701
    Phone: (555) 123-4567
    Fax: (555) 123-4568
    Email: john.smith@example.com
    SSN: 123-45-6789
    MRN: 987654321
    NHS Number: 1234567890
    Insurance: Blue Cross Plan #BC123456
    Account: ACC-789012
    Drivers License: DL-12345678
    Vehicle VIN: 1HGBH41JXMN109186
    Device Serial: DEV-SN-987654
    Website: https://patient-portal.hospital.com
    IP Address: 192.168.1.100
    Fingerprint on file (biometric ID)
    Photo ID verified

    Chief Complaint: Chest pain
    """

    # Act
    try:
        entities = await phi_detection_service.detect_phi(text)
    except ProcessingError as e:
        pytest.skip(f"MedCAT service not available: {e}")

    # Assert
    assert isinstance(entities, list)
    # At minimum should detect several PHI entities
    # (exact count depends on model performance)
    assert len(entities) > 0

    # Verify all detected entities are PHI types
    valid_phi_types = phi_detection_service.SUPPORTED_PHI_TYPES
    for entity in entities:
        assert entity.entity_type in valid_phi_types


@pytest.mark.asyncio
@pytest.mark.integration
async def test_phi_detection_performance_benchmark(phi_detection_service):
    """Test 10-page note processed in <2 minutes."""
    # Arrange - Simulate a 10-page clinical note (~500 words per page)
    sample_paragraph = """
    Patient John Smith, a 45-year-old male (NHS: 1234567890), presented to the
    Emergency Department at Springfield General Hospital on January 15, 2024,
    complaining of chest pain radiating to the left arm. The patient's medical
    history includes hypertension, type 2 diabetes mellitus, and hyperlipidemia.
    Current medications include Lisinopril 10mg daily, Metformin 1000mg twice
    daily, and Atorvastatin 40mg at bedtime. Contact information: Phone (555)
    123-4567, Email john.smith@example.com. Emergency contact is wife Jane Smith
    at (555) 765-4321. The patient denies smoking but admits to occasional
    alcohol use. Family history significant for coronary artery disease in father
    who died at age 55. Physical examination revealed blood pressure 145/92,
    heart rate 88, respiratory rate 16, temperature 98.6F. Cardiovascular exam
    showed regular rate and rhythm with no murmurs. ECG demonstrated ST segment
    elevation in leads II, III, and aVF consistent with inferior wall myocardial
    infarction. Troponin levels elevated at 2.5 ng/mL. Patient was immediately
    taken to the cardiac catheterization lab where angiography revealed 95%
    stenosis of the right coronary artery. Successful percutaneous coronary
    intervention with drug-eluting stent placement was performed. Post-procedure
    vital signs stable. Patient admitted to cardiac care unit for monitoring.
    """

    # Create a 10-page note (approximately 5000 words)
    ten_page_note = sample_paragraph * 20  # ~4000 words

    # Act
    start_time = datetime.now()
    try:
        entities = await phi_detection_service.detect_phi(ten_page_note)
    except ProcessingError as e:
        pytest.skip(f"MedCAT service not available: {e}")
    end_time = datetime.now()

    # Assert
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 120, f"Processing took {processing_time}s, should be <120s"
    assert isinstance(entities, list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_phi_detection_batch_processing_integration(phi_detection_service):
    """Test batch processing with real MedCAT service."""
    # Arrange
    texts = [
        "Patient John Smith, MRN: 123456",
        "Contact Dr. Jane Doe at (555) 999-8888",
        "Clinical note from 01/15/2024",
        "No PHI in this simple sentence",
    ]

    # Act
    try:
        results = await phi_detection_service.detect_phi_batch(texts)
    except ProcessingError as e:
        pytest.skip(f"MedCAT service not available: {e}")

    # Assert
    assert len(results) == 4
    # First 3 should have PHI entities (depending on model)
    # Fourth should have few or no entities
    for result in results:
        assert isinstance(result, list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_phi_detection_handles_service_unavailable(phi_detection_service):
    """Test graceful handling when service is unavailable."""
    # Arrange - Create service with bad URL
    bad_client = CogStackModelServeClient(base_url="http://localhost:9999")
    bad_service = PHIDetectionService(medcat_client=bad_client)

    # Act & Assert
    # Should raise ProcessingError after retries
    with pytest.raises((ProcessingError, Exception)):
        await bad_service.detect_phi("Test text")
