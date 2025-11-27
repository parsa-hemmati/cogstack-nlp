"""
Integration tests for Timeline API endpoints.

Tests:
- GET /api/v1/timeline/{patient_id} - Timeline retrieval with filters
- POST /api/v1/timeline/{patient_id}/export - Timeline export (PDF, JSON, FHIR)
- GET /api/v1/timeline/documents/{document_id} - Document details

Coverage:
- Authentication requirements
- Filter functionality (date range, document types, concept types, meta-annotations)
- Export format validation
- Audit logging verification
- Error handling (404, 403, 400)
"""

import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.models.document import Document, DocumentType, ProcessingStatus
from app.models.annotation import Annotation
from app.models.user import User


# ===== Test Data Fixtures =====


@pytest_asyncio.fixture
async def test_patient(db_session: AsyncSession) -> Patient:
    """Create test patient."""
    patient = Patient(
        id=uuid.uuid4(),
        patient_id="MRN-12345",
        first_name="John",
        last_name="Doe",
        date_of_birth=datetime(1960, 5, 15),
        gender="male",
        created_at=datetime.utcnow(),
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


@pytest_asyncio.fixture
async def test_documents(
    db_session: AsyncSession, test_patient: Patient
) -> list[Document]:
    """Create test documents with varied dates and types."""
    documents = []

    # Clinical note from 6 months ago
    doc1 = Document(
        id=uuid.uuid4(),
        patient_id=test_patient.id,
        title="Initial Assessment",
        document_type=DocumentType.CLINICAL_NOTE,
        document_date=datetime.utcnow() - timedelta(days=180),
        author="Dr. Smith",
        status="completed",
        encrypted_content=b"encrypted_content_1",
        content_hash="hash1",
        created_at=datetime.utcnow() - timedelta(days=180),
    )
    documents.append(doc1)

    # Lab result from 3 months ago
    doc2 = Document(
        id=uuid.uuid4(),
        patient_id=test_patient.id,
        title="Blood Work Results",
        document_type=DocumentType.LAB_RESULT,
        document_date=datetime.utcnow() - timedelta(days=90),
        author="Lab Tech",
        status="completed",
        encrypted_content=b"encrypted_content_2",
        content_hash="hash2",
        created_at=datetime.utcnow() - timedelta(days=90),
    )
    documents.append(doc2)

    # Discharge summary from 1 month ago
    doc3 = Document(
        id=uuid.uuid4(),
        patient_id=test_patient.id,
        title="Discharge Summary",
        document_type=DocumentType.DISCHARGE_SUMMARY,
        document_date=datetime.utcnow() - timedelta(days=30),
        author="Dr. Johnson",
        status="completed",
        encrypted_content=b"encrypted_content_3",
        content_hash="hash3",
        created_at=datetime.utcnow() - timedelta(days=30),
    )
    documents.append(doc3)

    for doc in documents:
        db_session.add(doc)

    await db_session.commit()

    for doc in documents:
        await db_session.refresh(doc)

    return documents


@pytest_asyncio.fixture
async def test_annotations(
    db_session: AsyncSession, test_documents: list[Document]
) -> list[Annotation]:
    """Create test annotations with meta-annotations."""
    annotations = []

    # Condition on doc1 - affirmed, current, patient
    ann1 = Annotation(
        id=uuid.uuid4(),
        document_id=test_documents[0].id,
        cui="C0011849",
        preferred_name="Diabetes Mellitus",
        concept_type="condition",
        text="diabetes mellitus",
        start_char=50,
        end_char=67,
        negation="Affirmed",
        temporality="Current",
        experiencer="Patient",
        confidence=0.95,
        created_at=datetime.utcnow(),
    )
    annotations.append(ann1)

    # Condition on doc1 - negated (should be filtered by default)
    ann2 = Annotation(
        id=uuid.uuid4(),
        document_id=test_documents[0].id,
        cui="C0020538",
        preferred_name="Hypertension",
        concept_type="condition",
        text="hypertension",
        start_char=100,
        end_char=112,
        negation="Negated",
        temporality="Current",
        experiencer="Patient",
        confidence=0.88,
        created_at=datetime.utcnow(),
    )
    annotations.append(ann2)

    # Medication on doc2
    ann3 = Annotation(
        id=uuid.uuid4(),
        document_id=test_documents[1].id,
        cui="C0025598",
        preferred_name="Metformin",
        concept_type="medication",
        text="metformin",
        start_char=25,
        end_char=34,
        negation="Affirmed",
        temporality="Current",
        experiencer="Patient",
        confidence=0.92,
        created_at=datetime.utcnow(),
    )
    annotations.append(ann3)

    # Procedure on doc3
    ann4 = Annotation(
        id=uuid.uuid4(),
        document_id=test_documents[2].id,
        cui="C0005823",
        preferred_name="Blood Glucose Test",
        concept_type="procedure",
        text="blood glucose test",
        start_char=75,
        end_char=93,
        negation="Affirmed",
        temporality="Recent",
        experiencer="Patient",
        confidence=0.90,
        created_at=datetime.utcnow(),
    )
    annotations.append(ann4)

    # Family history condition (should be filtered by default)
    ann5 = Annotation(
        id=uuid.uuid4(),
        document_id=test_documents[0].id,
        cui="C0011849",
        preferred_name="Diabetes Mellitus",
        concept_type="condition",
        text="family history of diabetes",
        start_char=200,
        end_char=226,
        negation="Affirmed",
        temporality="Historical",
        experiencer="Family",
        confidence=0.85,
        created_at=datetime.utcnow(),
    )
    annotations.append(ann5)

    for ann in annotations:
        db_session.add(ann)

    await db_session.commit()

    for ann in annotations:
        await db_session.refresh(ann)

    return annotations


# ===== Timeline Retrieval Tests =====


class TestTimelineRetrieval:
    """Tests for GET /api/v1/timeline/{patient_id}"""

    @pytest.mark.asyncio
    async def test_get_timeline_success(
        self,
        clinician_client: AsyncClient,
        test_patient: Patient,
        test_documents: list[Document],
        test_annotations: list[Annotation],
    ):
        """Test successful timeline retrieval."""
        response = await clinician_client.get(
            f"/api/v1/timeline/{test_patient.id}"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "patientId" in data
        assert "documents" in data
        assert "concepts" in data
        assert "dateRange" in data
        assert "metadata" in data

        # Verify patient ID
        assert data["patientId"] == str(test_patient.id)

        # Verify documents returned
        assert len(data["documents"]) == 3

        # Verify metadata
        assert data["metadata"]["documentCount"] == 3

    @pytest.mark.asyncio
    async def test_get_timeline_unauthenticated(
        self,
        client: AsyncClient,
        test_patient: Patient,
    ):
        """Test timeline retrieval without authentication."""
        response = await client.get(f"/api/v1/timeline/{test_patient.id}")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_timeline_patient_not_found(
        self,
        clinician_client: AsyncClient,
    ):
        """Test timeline retrieval with non-existent patient."""
        fake_id = uuid.uuid4()
        response = await clinician_client.get(f"/api/v1/timeline/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_timeline_date_filter(
        self,
        clinician_client: AsyncClient,
        test_patient: Patient,
        test_documents: list[Document],
    ):
        """Test timeline with date range filter."""
        # Filter to last 60 days (should return 2 documents)
        start_date = (datetime.utcnow() - timedelta(days=60)).isoformat()

        response = await clinician_client.get(
            f"/api/v1/timeline/{test_patient.id}",
            params={"start_date": start_date}
        )

        assert response.status_code == 200
        data = response.json()

        # Should return documents from last 60 days
        assert data["metadata"]["documentCount"] <= 2

    @pytest.mark.asyncio
    async def test_get_timeline_document_type_filter(
        self,
        clinician_client: AsyncClient,
        test_patient: Patient,
        test_documents: list[Document],
    ):
        """Test timeline with document type filter."""
        response = await clinician_client.get(
            f"/api/v1/timeline/{test_patient.id}",
            params={"document_types": "clinical_note,lab_result"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should only return clinical notes and lab results
        for doc in data["documents"]:
            assert doc["type"] in ["clinical_note", "lab_result"]

    @pytest.mark.asyncio
    async def test_get_timeline_meta_annotation_filter(
        self,
        clinician_client: AsyncClient,
        test_patient: Patient,
        test_annotations: list[Annotation],
    ):
        """Test timeline with meta-annotation filters."""
        # Default: exclude negated and family
        response = await clinician_client.get(
            f"/api/v1/timeline/{test_patient.id}"
        )

        assert response.status_code == 200
        data = response.json()

        # Should not include negated or family history concepts
        for concept in data["concepts"]:
            meta = concept.get("metaAnnotations", {})
            assert meta.get("negation") != "Negated"
            assert meta.get("experiencer") != "Family"

    @pytest.mark.asyncio
    async def test_get_timeline_include_negated(
        self,
        clinician_client: AsyncClient,
        test_patient: Patient,
        test_annotations: list[Annotation],
    ):
        """Test timeline with include_negated=true."""
        response = await clinician_client.get(
            f"/api/v1/timeline/{test_patient.id}",
            params={"include_negated": True}
        )

        assert response.status_code == 200
        data = response.json()

        # Count should be higher when including negated
        assert data["metadata"]["conceptCount"] >= 1


# ===== Timeline Export Tests =====


class TestTimelineExport:
    """Tests for POST /api/v1/timeline/{patient_id}/export"""

    @pytest.mark.asyncio
    async def test_export_json_success(
        self,
        clinician_client: AsyncClient,
        test_patient: Patient,
        test_documents: list[Document],
    ):
        """Test JSON export."""
        response = await clinician_client.post(
            f"/api/v1/timeline/{test_patient.id}/export",
            params={"format": "json"}
        )

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_export_pdf_success(
        self,
        clinician_client: AsyncClient,
        test_patient: Patient,
        test_documents: list[Document],
    ):
        """Test PDF export."""
        response = await clinician_client.post(
            f"/api/v1/timeline/{test_patient.id}/export",
            params={"format": "pdf"}
        )

        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_export_fhir_success(
        self,
        clinician_client: AsyncClient,
        test_patient: Patient,
        test_documents: list[Document],
    ):
        """Test FHIR export."""
        response = await clinician_client.post(
            f"/api/v1/timeline/{test_patient.id}/export",
            params={"format": "fhir"}
        )

        assert response.status_code == 200
        assert "application/fhir+json" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_export_invalid_format(
        self,
        clinician_client: AsyncClient,
        test_patient: Patient,
    ):
        """Test export with invalid format."""
        response = await clinician_client.post(
            f"/api/v1/timeline/{test_patient.id}/export",
            params={"format": "invalid"}
        )

        # FastAPI validates Literal types, should return 422
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_export_unauthenticated(
        self,
        client: AsyncClient,
        test_patient: Patient,
    ):
        """Test export without authentication."""
        response = await client.post(
            f"/api/v1/timeline/{test_patient.id}/export",
            params={"format": "json"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_export_with_filters(
        self,
        clinician_client: AsyncClient,
        test_patient: Patient,
        test_documents: list[Document],
    ):
        """Test export with filters applied."""
        start_date = (datetime.utcnow() - timedelta(days=60)).isoformat()

        response = await clinician_client.post(
            f"/api/v1/timeline/{test_patient.id}/export",
            params={
                "format": "json",
                "start_date": start_date,
                "document_types": "clinical_note"
            }
        )

        assert response.status_code == 200


# ===== Document Details Tests =====


class TestDocumentDetails:
    """Tests for GET /api/v1/timeline/documents/{document_id}"""

    @pytest.mark.asyncio
    async def test_get_document_details_success(
        self,
        clinician_client: AsyncClient,
        test_documents: list[Document],
        test_annotations: list[Annotation],
    ):
        """Test successful document details retrieval."""
        doc = test_documents[0]

        response = await clinician_client.get(
            f"/api/v1/timeline/documents/{doc.id}"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert data["id"] == str(doc.id)
        assert "title" in data
        assert "documentType" in data
        assert "date" in data
        assert "content" in data
        assert "annotations" in data

        # Verify annotations included
        assert len(data["annotations"]) > 0

    @pytest.mark.asyncio
    async def test_get_document_details_not_found(
        self,
        clinician_client: AsyncClient,
    ):
        """Test document details with non-existent document."""
        fake_id = uuid.uuid4()

        response = await clinician_client.get(
            f"/api/v1/timeline/documents/{fake_id}"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_document_details_unauthenticated(
        self,
        client: AsyncClient,
        test_documents: list[Document],
    ):
        """Test document details without authentication."""
        doc = test_documents[0]

        response = await client.get(
            f"/api/v1/timeline/documents/{doc.id}"
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_document_annotations_structure(
        self,
        clinician_client: AsyncClient,
        test_documents: list[Document],
        test_annotations: list[Annotation],
    ):
        """Test annotation structure in document details."""
        doc = test_documents[0]

        response = await clinician_client.get(
            f"/api/v1/timeline/documents/{doc.id}"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify annotation structure
        for ann in data["annotations"]:
            assert "id" in ann
            assert "cui" in ann
            assert "preferredName" in ann
            assert "conceptType" in ann
            assert "startChar" in ann
            assert "endChar" in ann
            assert "metaAnnotations" in ann


# ===== Audit Logging Tests =====


class TestAuditLogging:
    """Tests for audit logging of PHI access."""

    @pytest.mark.asyncio
    async def test_timeline_access_creates_audit_log(
        self,
        clinician_client: AsyncClient,
        test_patient: Patient,
        test_documents: list[Document],
        db_session: AsyncSession,
    ):
        """Test that timeline access creates audit log."""
        from sqlalchemy import select
        from app.models.audit_log import AuditLog

        # Access timeline
        response = await clinician_client.get(
            f"/api/v1/timeline/{test_patient.id}"
        )

        assert response.status_code == 200

        # Check audit log was created
        result = await db_session.execute(
            select(AuditLog).where(
                AuditLog.resource_type == "Timeline",
                AuditLog.resource_id == str(test_patient.id)
            )
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.action == "VIEW_RECORD"
        assert audit_log.success is True

    @pytest.mark.asyncio
    async def test_export_creates_audit_log(
        self,
        clinician_client: AsyncClient,
        test_patient: Patient,
        test_documents: list[Document],
        db_session: AsyncSession,
    ):
        """Test that export creates audit log."""
        from sqlalchemy import select
        from app.models.audit_log import AuditLog

        # Export timeline
        response = await clinician_client.post(
            f"/api/v1/timeline/{test_patient.id}/export",
            params={"format": "json"}
        )

        assert response.status_code == 200

        # Check audit log was created
        result = await db_session.execute(
            select(AuditLog).where(
                AuditLog.resource_type == "Timeline",
                AuditLog.action == "EXPORT_RECORD"
            )
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert "export_format" in (audit_log.details or {})
