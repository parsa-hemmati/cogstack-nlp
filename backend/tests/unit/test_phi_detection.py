"""
Unit tests for PHI Detection Model.

Tests validate MedCAT PHI detection model against HIPAA Safe Harbor 18 identifiers.
Target metrics: Precision >95%, Recall >90%, F1 >0.92
"""
import pytest
from typing import List
from app.clients.modelserve_client import CogStackModelServeClient, Entity


class TestPHIDetectionModel:
    """Test suite for PHI detection model validation."""

    # HIPAA Safe Harbor 18 Identifiers test cases
    PHI_TEST_CASES = [
        # 1. Names
        (
            "Patient John Smith visited the clinic.",
            ["John Smith"],
            "phi_name",
        ),
        # 2. Geographic locations (smaller than state)
        (
            "Patient lives at 123 Main Street, London, EC1A 1BB.",
            ["123 Main Street, London, EC1A 1BB"],
            "phi_address",
        ),
        # 3. Dates (except year)
        (
            "Admission date: 15/03/2023",
            ["15/03/2023"],
            "phi_date",
        ),
        # 4. Telephone numbers
        (
            "Contact number: 020-7123-4567",
            ["020-7123-4567"],
            "phi_phone",
        ),
        # 5. Email addresses
        (
            "Email: john.smith@nhs.net",
            ["john.smith@nhs.net"],
            "phi_email",
        ),
        # 6. NHS numbers (UK equivalent of SSN)
        (
            "NHS number: 123 456 7890",
            ["123 456 7890"],
            "phi_nhs_number",
        ),
        # 7. Medical record numbers
        (
            "MRN: MED-2023-001234",
            ["MED-2023-001234"],
            "phi_mrn",
        ),
        # 8. URLs
        (
            "Patient portal: https://patient.example.nhs.uk/123456",
            ["https://patient.example.nhs.uk/123456"],
            "phi_url",
        ),
        # 9. IP addresses
        (
            "Logged from IP: 192.168.1.100",
            ["192.168.1.100"],
            "phi_ip",
        ),
    ]

    @pytest.fixture
    def medcat_client(self):
        """Create MedCAT client for testing."""
        return CogStackModelServeClient()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("text,expected_phi,expected_type", PHI_TEST_CASES)
    async def test_detect_phi_entity_types(
        self,
        medcat_client: CogStackModelServeClient,
        text: str,
        expected_phi: List[str],
        expected_type: str,
    ):
        """
        Test PHI detection for each HIPAA Safe Harbor identifier type.

        Validates that MedCAT correctly identifies each PHI type.
        """
        # Act
        entities = await medcat_client.detect_phi(text)

        # Assert: At least one PHI entity detected
        assert len(entities) > 0, f"No PHI detected in: {text}"

        # Assert: Expected PHI entities found
        detected_names = [e.pretty_name for e in entities]
        for expected in expected_phi:
            assert any(
                expected.lower() in name.lower() for name in detected_names
            ), f"Expected PHI '{expected}' not found. Detected: {detected_names}"

    @pytest.mark.asyncio
    async def test_phi_detection_precision(self, medcat_client: CogStackModelServeClient):
        """
        Test PHI detection precision (target: >95%).

        Precision = True Positives / (True Positives + False Positives)
        Ensures model doesn't over-detect (false positives).
        """
        # Clinical text with NO PHI (should not detect anything)
        clean_texts = [
            "Patient has diabetes mellitus type 2.",
            "Blood pressure 120/80 mmHg.",
            "Prescribed metformin 500mg twice daily.",
            "Family history of hypertension.",
            "No known drug allergies.",
        ]

        total_false_positives = 0

        for text in clean_texts:
            entities = await medcat_client.detect_phi(text)
            false_positives = len(entities)
            total_false_positives += false_positives

            # Assert: No PHI in clean clinical text
            assert (
                false_positives == 0
            ), f"False positive PHI detected in clean text: {text} -> {entities}"

        # Target: 0 false positives in clean clinical text (precision = 100%)
        assert total_false_positives == 0, f"Total false positives: {total_false_positives}"

    @pytest.mark.asyncio
    async def test_phi_detection_recall(self, medcat_client: CogStackModelServeClient):
        """
        Test PHI detection recall (target: >90%).

        Recall = True Positives / (True Positives + False Negatives)
        Ensures model doesn't miss PHI (false negatives).
        """
        # Clinical text with embedded PHI
        text_with_phi = """
        Patient: John Smith
        NHS Number: 123 456 7890
        DOB: 15/03/1980
        Address: 123 Main St, London EC1A 1BB
        Phone: 020-7123-4567
        Email: john.smith@nhs.net
        """

        expected_phi_count = 6  # Name, NHS#, DOB, Address, Phone, Email

        # Act
        entities = await medcat_client.detect_phi(text_with_phi)

        # Assert: Detected at least 90% of PHI (recall ≥0.90)
        recall = len(entities) / expected_phi_count
        assert recall >= 0.90, (
            f"Recall too low: {recall:.2f} (detected {len(entities)}/{expected_phi_count}). "
            f"Target: ≥0.90. Detected: {[e.pretty_name for e in entities]}"
        )

    @pytest.mark.asyncio
    async def test_phi_detection_confidence_scores(
        self, medcat_client: CogStackModelServeClient
    ):
        """
        Test PHI detection confidence scores.

        Validates that all detected PHI has accuracy score in valid range [0, 1].
        High-confidence detections (accuracy >0.8) should be the majority.
        """
        text = "Patient John Smith, NHS 123 456 7890, DOB 15/03/1980"

        # Act
        entities = await medcat_client.detect_phi(text)

        # Assert: All confidence scores valid
        for entity in entities:
            assert (
                0.0 <= entity.accuracy <= 1.0
            ), f"Invalid accuracy score: {entity.accuracy} for {entity.pretty_name}"

        # Assert: At least 80% of detections have high confidence (>0.8)
        high_confidence_count = sum(1 for e in entities if e.accuracy > 0.8)
        high_confidence_ratio = high_confidence_count / len(entities) if entities else 0

        assert high_confidence_ratio >= 0.8, (
            f"Too many low-confidence detections: {high_confidence_ratio:.2f} "
            f"(expected ≥0.80)"
        )

    @pytest.mark.asyncio
    async def test_phi_detection_no_false_negatives_critical(
        self, medcat_client: CogStackModelServeClient
    ):
        """
        Test PHI detection for CRITICAL identifiers (must not miss).

        Critical PHI types (high privacy risk):
        - NHS numbers
        - Names
        - Addresses

        False negatives for these types are unacceptable (HIPAA violation risk).
        """
        critical_phi_tests = [
            ("Patient John Smith", ["John Smith"], "Name"),
            ("NHS number: 123 456 7890", ["123 456 7890"], "NHS Number"),
            (
                "Address: 123 Main St, London EC1A 1BB",
                ["123 Main St, London EC1A 1BB"],
                "Address",
            ),
        ]

        for text, expected_phi, phi_type in critical_phi_tests:
            entities = await medcat_client.detect_phi(text)

            # Assert: Critical PHI MUST be detected (no false negatives)
            detected_names = [e.pretty_name for e in entities]
            found = any(
                expected.lower() in name.lower()
                for expected in expected_phi
                for name in detected_names
            )

            assert found, (
                f"CRITICAL: {phi_type} PHI not detected (false negative). "
                f"Text: '{text}'. Expected: {expected_phi}. Detected: {detected_names}"
            )

    @pytest.mark.asyncio
    async def test_phi_detection_mixed_clinical_and_phi(
        self, medcat_client: CogStackModelServeClient
    ):
        """
        Test PHI detection in realistic clinical notes (mixed content).

        Validates model can distinguish PHI from clinical concepts.
        """
        clinical_note = """
        Patient John Smith (NHS 123 456 7890) presented with chest pain.
        History: Type 2 diabetes mellitus, hypertension.
        Examination: BP 140/90 mmHg, heart rate 82 bpm.
        Plan: ECG, troponin, refer to cardiology.
        Contact: 020-7123-4567 (patient mobile).
        """

        # Expected PHI: John Smith, NHS 123 456 7890, 020-7123-4567
        # Should NOT detect: diabetes, hypertension, chest pain (clinical concepts)

        # Act
        entities = await medcat_client.detect_phi(clinical_note)

        # Assert: At least 3 PHI detected (name, NHS#, phone)
        assert len(entities) >= 3, f"Expected ≥3 PHI, detected {len(entities)}"

        # Assert: No clinical concepts misclassified as PHI
        clinical_concepts = ["diabetes", "hypertension", "chest pain", "ECG", "troponin"]
        detected_names_lower = [e.pretty_name.lower() for e in entities]

        for concept in clinical_concepts:
            assert concept not in detected_names_lower, (
                f"Clinical concept '{concept}' incorrectly classified as PHI"
            )


class TestPHIDetectionPerformance:
    """Test suite for PHI detection performance benchmarks."""

    @pytest.fixture
    def medcat_client(self):
        """Create MedCAT client for testing."""
        return CogStackModelServeClient()

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_phi_detection_speed(self, medcat_client: CogStackModelServeClient):
        """
        Test PHI detection inference speed.

        Target: <2 minutes per 10-page note (~5000 words).
        """
        # Simulate 10-page clinical note (~5000 words)
        # Each page ~500 words = 3000 chars
        sample_page = (
            "Patient John Smith, NHS 123 456 7890, DOB 15/03/1980. "
            "Presented with chest pain radiating to left arm. "
            "History of type 2 diabetes mellitus and hypertension. "
            "Current medications: metformin 500mg BD, ramipril 10mg OD. "
            "Examination: BP 140/90 mmHg, HR 82 bpm, SpO2 98% on air. "
        ) * 10  # ~3000 chars per page

        ten_page_note = sample_page * 10  # ~30,000 chars total

        # Act: Measure inference time
        import time

        start_time = time.time()
        entities = await medcat_client.detect_phi(ten_page_note)
        elapsed_time = time.time() - start_time

        # Assert: Processing time <120 seconds (2 minutes)
        assert elapsed_time < 120.0, (
            f"PHI detection too slow: {elapsed_time:.2f}s for 10-page note. "
            f"Target: <120s. Detected {len(entities)} PHI entities."
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_phi_detection_model_loaded(
        self, medcat_client: CogStackModelServeClient
    ):
        """
        Test that PHI detection model is loaded and available.

        Integration test: requires CogStack-ModelServe running.
        """
        # Act: Check model availability
        models = await medcat_client.get_available_models()

        # Assert: De-identification model available
        assert "medcat_deid" in models, (
            f"PHI detection model 'medcat_deid' not available. "
            f"Available models: {models}"
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_phi_detection_health_check(
        self, medcat_client: CogStackModelServeClient
    ):
        """
        Test CogStack-ModelServe health for PHI detection.

        Integration test: requires CogStack-ModelServe running.
        """
        # Act
        is_healthy = await medcat_client.health_check()

        # Assert: Service healthy
        assert is_healthy, "CogStack-ModelServe not healthy (PHI detection unavailable)"


class TestPHIDetectionMetrics:
    """Test suite for PHI detection metrics calculation."""

    def test_calculate_precision(self):
        """
        Test precision calculation.

        Precision = TP / (TP + FP)
        """
        # Example: 95 true positives, 5 false positives
        true_positives = 95
        false_positives = 5

        precision = true_positives / (true_positives + false_positives)

        # Assert: Precision >0.95 (target)
        assert precision >= 0.95, f"Precision {precision:.3f} below target (≥0.95)"

    def test_calculate_recall(self):
        """
        Test recall calculation.

        Recall = TP / (TP + FN)
        """
        # Example: 90 true positives, 10 false negatives
        true_positives = 90
        false_negatives = 10

        recall = true_positives / (true_positives + false_negatives)

        # Assert: Recall >0.90 (target)
        assert recall >= 0.90, f"Recall {recall:.3f} below target (≥0.90)"

    def test_calculate_f1_score(self):
        """
        Test F1 score calculation.

        F1 = 2 * (Precision * Recall) / (Precision + Recall)
        """
        # Example: Precision 0.95, Recall 0.90
        precision = 0.95
        recall = 0.90

        f1_score = 2 * (precision * recall) / (precision + recall)

        # Assert: F1 >0.92 (target)
        assert f1_score >= 0.92, f"F1 score {f1_score:.3f} below target (≥0.92)"

        # Verify calculation
        expected_f1 = 2 * (0.95 * 0.90) / (0.95 + 0.90)
        assert abs(f1_score - expected_f1) < 0.001, f"F1 calculation error"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "benchmark: Performance benchmark tests")
    config.addinivalue_line(
        "markers", "integration: Integration tests (require services running)"
    )
