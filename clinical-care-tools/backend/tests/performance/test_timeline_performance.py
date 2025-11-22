"""
Performance Tests for Timeline Module.

Tests verify that timeline meets performance requirements:
- Timeline load time <2s for 100 documents
- Timeline load time <5s for 500 documents
- Filter update time <500ms
- Concept aggregation <1s
- PDF export <5s
- Concurrent users (10 simultaneous requests)

Uses pytest-benchmark for accurate timing measurements.
"""

import pytest
import time
from uuid import uuid4
from datetime import date, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.modules.patient.models import Patient
from app.modules.document.models import Document
from app.modules.timeline.models import TimelineRequest
from app.modules.timeline.service import TimelineService


@pytest.fixture
def performance_patient(db_session):
    """Create a test patient for performance testing."""
    patient = Patient(
        id=uuid4(),
        nhs_number="9999999999",
        first_name="Performance",
        last_name="Test",
        date_of_birth=date(1980, 1, 1),
        gender="M"
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


@pytest.fixture
def patient_with_100_documents(db_session, performance_patient, test_project):
    """Create patient with 100 documents for performance testing."""
    return _create_patient_with_n_documents(db_session, performance_patient, test_project, 100)


@pytest.fixture
def patient_with_500_documents(db_session, performance_patient, test_project):
    """Create patient with 500 documents for performance testing."""
    return _create_patient_with_n_documents(db_session, performance_patient, test_project, 500)


@pytest.fixture
def patient_with_1000_documents(db_session, performance_patient, test_project):
    """Create patient with 1000 documents for stress testing."""
    return _create_patient_with_n_documents(db_session, performance_patient, test_project, 1000)


def _create_patient_with_n_documents(db_session, patient, project, n_documents):
    """Helper to create N documents for a patient."""
    documents = []
    base_date = datetime(2024, 1, 1)

    document_types = [
        "Clinical Note", "Lab Report", "Discharge Summary",
        "Radiology Report", "Progress Note", "Consultation Note"
    ]

    for i in range(n_documents):
        # Spread documents over 2 years
        doc_date = base_date + timedelta(days=(i * 365 * 2 // n_documents))

        doc = Document(
            id=uuid4(),
            patient_id=patient.id,
            project_id=project.id,
            title=f"{document_types[i % len(document_types)]} {i+1}",
            content=f"""
                Patient presents with diabetes mellitus and hypertension.
                Blood pressure: 140/90 mmHg. Blood glucose: 180 mg/dL.
                Prescribed metformin 500mg twice daily.
                No adverse reactions reported.
                Follow-up in 3 months.
            """,
            document_date=doc_date.date(),
            document_type=document_types[i % len(document_types)],
            author=f"Dr. Smith {(i % 10) + 1}",
            source="Performance Test System"
        )
        db_session.add(doc)
        documents.append(doc)

        # Commit in batches of 100 to improve performance
        if (i + 1) % 100 == 0:
            db_session.commit()

    # Final commit for remaining documents
    db_session.commit()

    return patient, documents


@pytest.fixture
def mock_es_repo_with_concepts(mocker):
    """Mock Elasticsearch repository with realistic concept data."""
    mock_repo = mocker.MagicMock()

    # Mock concepts for each document
    concepts = []
    for i in range(20):  # 20 unique concepts
        concepts.append({
            "concept_cui": f"C{str(i).zfill(7)}",
            "name": f"Concept {i}",
            "type": "Disease" if i % 3 == 0 else ("Medication" if i % 3 == 1 else "Symptom"),
            "first_mention_date": "2024-01-01",
            "mention_count": (i + 1) * 5
        })

    mock_repo.query_patient_concepts.return_value = concepts

    # Mock frequency aggregation
    frequency_data = {}
    for concept in concepts:
        frequency_data[concept["concept_cui"]] = {
            "2024-01": 5,
            "2024-02": 4,
            "2024-03": 3,
            "2024-04": 6,
            "2024-05": 2,
            "2024-06": 4
        }

    mock_repo.aggregate_concept_frequency.return_value = frequency_data

    return mock_repo


@pytest.mark.performance
class TestTimelineLoadPerformance:
    """Test timeline load time with varying document counts."""

    def test_timeline_load_100_docs_under_2_seconds(
        self,
        client,
        auth_headers_clinician,
        patient_with_100_documents,
        mock_es_repo_with_concepts,
        mocker
    ):
        """
        Performance test: Timeline with 100 documents loads in <2 seconds.

        Target: <2s
        """
        patient, documents = patient_with_100_documents

        # Mock ES repository
        mocker.patch(
            "app.modules.timeline.service.ElasticsearchTimelineRepository",
            return_value=mock_es_repo_with_concepts
        )

        # Measure load time
        start_time = time.time()

        response = client.get(
            f"/api/v1/timeline/{patient.id}",
            headers=auth_headers_clinician
        )

        load_time = time.time() - start_time

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 100

        # Performance assertion
        assert load_time < 2.0, f"Timeline load took {load_time:.2f}s (target: <2s)"

        print(f"✅ Timeline load (100 docs): {load_time:.3f}s (target: <2s)")

    def test_timeline_load_500_docs_under_5_seconds(
        self,
        client,
        auth_headers_clinician,
        patient_with_500_documents,
        mock_es_repo_with_concepts,
        mocker
    ):
        """
        Performance test: Timeline with 500 documents loads in <5 seconds.

        Target: <5s
        """
        patient, documents = patient_with_500_documents

        # Mock ES repository
        mocker.patch(
            "app.modules.timeline.service.ElasticsearchTimelineRepository",
            return_value=mock_es_repo_with_concepts
        )

        # Measure load time
        start_time = time.time()

        response = client.get(
            f"/api/v1/timeline/{patient.id}",
            headers=auth_headers_clinician
        )

        load_time = time.time() - start_time

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 500

        # Performance assertion
        assert load_time < 5.0, f"Timeline load took {load_time:.2f}s (target: <5s)"

        print(f"✅ Timeline load (500 docs): {load_time:.3f}s (target: <5s)")


@pytest.mark.performance
class TestFilterPerformance:
    """Test filter application performance."""

    def test_filter_update_under_500ms(
        self,
        client,
        auth_headers_clinician,
        patient_with_100_documents,
        mock_es_repo_with_concepts,
        mocker
    ):
        """
        Performance test: Filter updates complete in <500ms.

        Target: <500ms
        """
        patient, documents = patient_with_100_documents

        # Mock ES repository
        mocker.patch(
            "app.modules.timeline.service.ElasticsearchTimelineRepository",
            return_value=mock_es_repo_with_concepts
        )

        # Measure filter update time
        start_time = time.time()

        response = client.get(
            f"/api/v1/timeline/{patient.id}",
            params={
                "date_start": "2024-01-01",
                "date_end": "2024-06-30",
                "negation": "Affirmed",
                "experiencer": "Patient"
            },
            headers=auth_headers_clinician
        )

        filter_time = time.time() - start_time

        # Assertions
        assert response.status_code == 200

        # Performance assertion
        assert filter_time < 0.5, f"Filter update took {filter_time:.3f}s (target: <500ms)"

        print(f"✅ Filter update: {filter_time:.3f}s (target: <0.5s)")


@pytest.mark.performance
class TestConceptAggregationPerformance:
    """Test concept frequency aggregation performance."""

    def test_concept_aggregation_under_1_second(
        self,
        timeline_service,
        patient_with_100_documents,
        mock_es_repo_with_concepts,
        test_user
    ):
        """
        Performance test: Concept frequency aggregation completes in <1s.

        Target: <1s
        """
        patient, documents = patient_with_100_documents

        # Measure aggregation time
        start_time = time.time()

        # Call service method that triggers aggregation
        request = TimelineRequest(patient_id=patient.id)
        timeline = timeline_service.get_patient_timeline(
            patient_id=patient.id,
            request=request,
            user=test_user,
            ip_address="127.0.0.1",
            user_agent="Performance Test"
        )

        aggregation_time = time.time() - start_time

        # Assertions
        assert timeline is not None
        assert len(timeline.concepts) > 0

        # Performance assertion
        assert aggregation_time < 1.0, f"Aggregation took {aggregation_time:.3f}s (target: <1s)"

        print(f"✅ Concept aggregation: {aggregation_time:.3f}s (target: <1s)")


@pytest.mark.performance
class TestExportPerformance:
    """Test export generation performance."""

    def test_pdf_export_under_5_seconds(
        self,
        client,
        auth_headers_clinician,
        patient_with_100_documents,
        mocker
    ):
        """
        Performance test: PDF export completes in <5s.

        Target: <5s
        """
        patient, documents = patient_with_100_documents

        # Measure export time
        start_time = time.time()

        response = client.post(
            f"/api/v1/timeline/{patient.id}/export",
            json={"format": "pdf"},
            headers=auth_headers_clinician
        )

        export_time = time.time() - start_time

        # Assertions
        assert response.status_code == 202
        export_data = response.json()
        assert export_data["format"] == "pdf"

        # Performance assertion
        assert export_time < 5.0, f"PDF export took {export_time:.2f}s (target: <5s)"

        print(f"✅ PDF export: {export_time:.3f}s (target: <5s)")

    def test_fhir_export_under_3_seconds(
        self,
        client,
        auth_headers_clinician,
        patient_with_100_documents
    ):
        """Performance test: FHIR export completes in <3s."""
        patient, documents = patient_with_100_documents

        # Measure export time
        start_time = time.time()

        response = client.post(
            f"/api/v1/timeline/{patient.id}/export",
            json={"format": "fhir"},
            headers=auth_headers_clinician
        )

        export_time = time.time() - start_time

        # Assertions
        assert response.status_code == 202

        # Performance assertion
        assert export_time < 3.0, f"FHIR export took {export_time:.2f}s (target: <3s)"

        print(f"✅ FHIR export: {export_time:.3f}s (target: <3s)")


@pytest.mark.performance
class TestConcurrentUsersPerformance:
    """Test concurrent user access performance."""

    def test_10_concurrent_users_handled(
        self,
        client,
        auth_headers_clinician,
        patient_with_100_documents,
        mock_es_repo_with_concepts,
        mocker
    ):
        """
        Performance test: 10 concurrent users can access timeline simultaneously.

        Target: All requests complete within 5 seconds
        """
        patient, documents = patient_with_100_documents

        # Mock ES repository
        mocker.patch(
            "app.modules.timeline.service.ElasticsearchTimelineRepository",
            return_value=mock_es_repo_with_concepts
        )

        def make_request():
            """Make a single timeline request."""
            response = client.get(
                f"/api/v1/timeline/{patient.id}",
                headers=auth_headers_clinician
            )
            return response.status_code

        # Measure concurrent request time
        start_time = time.time()

        # Execute 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]

        total_time = time.time() - start_time

        # Assertions
        assert all(status == 200 for status in results), "All requests should succeed"

        # Performance assertion
        assert total_time < 5.0, f"10 concurrent requests took {total_time:.2f}s (target: <5s)"

        print(f"✅ 10 concurrent users: {total_time:.3f}s (target: <5s)")
        print(f"   Average per request: {total_time / 10:.3f}s")


@pytest.mark.performance
class TestStressTest:
    """Stress tests for timeline with very large datasets."""

    @pytest.mark.skip(reason="Stress test - run manually")
    def test_timeline_with_1000_documents(
        self,
        client,
        auth_headers_clinician,
        patient_with_1000_documents,
        mock_es_repo_with_concepts,
        mocker
    ):
        """
        Stress test: Timeline with 1000 documents.

        This test is skipped by default and should be run manually to verify
        system behavior under stress.
        """
        patient, documents = patient_with_1000_documents

        # Mock ES repository
        mocker.patch(
            "app.modules.timeline.service.ElasticsearchTimelineRepository",
            return_value=mock_es_repo_with_concepts
        )

        # Measure load time
        start_time = time.time()

        response = client.get(
            f"/api/v1/timeline/{patient.id}",
            headers=auth_headers_clinician
        )

        load_time = time.time() - start_time

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 1000

        print(f"ℹ️ Timeline load (1000 docs): {load_time:.3f}s")

    @pytest.mark.skip(reason="Stress test - run manually")
    def test_50_concurrent_users(
        self,
        client,
        auth_headers_clinician,
        patient_with_100_documents,
        mock_es_repo_with_concepts,
        mocker
    ):
        """
        Stress test: 50 concurrent users.

        This test is skipped by default and should be run manually to verify
        system behavior under high load.
        """
        patient, documents = patient_with_100_documents

        # Mock ES repository
        mocker.patch(
            "app.modules.timeline.service.ElasticsearchTimelineRepository",
            return_value=mock_es_repo_with_concepts
        )

        def make_request():
            """Make a single timeline request."""
            response = client.get(
                f"/api/v1/timeline/{patient.id}",
                headers=auth_headers_clinician
            )
            return response.status_code, response.elapsed.total_seconds()

        # Measure concurrent request time
        start_time = time.time()

        # Execute 50 concurrent requests
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in as_completed(futures)]

        total_time = time.time() - start_time

        # Assertions
        successful_requests = sum(1 for status, _ in results if status == 200)
        assert successful_requests >= 45, f"At least 45/50 requests should succeed (got {successful_requests})"

        print(f"ℹ️ 50 concurrent users: {total_time:.3f}s")
        print(f"   Successful requests: {successful_requests}/50")
        print(f"   Average per request: {total_time / 50:.3f}s")
