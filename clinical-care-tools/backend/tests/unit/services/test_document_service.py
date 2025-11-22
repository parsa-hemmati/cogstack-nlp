"""
Unit tests for Document Service

Tests document upload, encryption, retrieval, and management functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.services.document_service import DocumentService
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentFilter


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    db.get = AsyncMock()
    db.execute = AsyncMock()
    db.scalar = AsyncMock()
    return db


@pytest.fixture
def mock_audit_service():
    """Create mock audit service."""
    audit = AsyncMock()
    audit.log_document_upload = AsyncMock()
    audit.log_phi_access = AsyncMock()
    audit.log_document_deletion = AsyncMock()
    return audit


@pytest.fixture
def document_service(mock_db, mock_audit_service):
    """Create document service instance."""
    return DocumentService(mock_db, mock_audit_service)


@pytest.fixture
def sample_user():
    """Create sample user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        full_name="Test User"
    )
    return user


@pytest.fixture
def sample_document():
    """Create sample document."""
    return Document(
        id=uuid4(),
        project_id=uuid4(),
        uploaded_by=uuid4(),
        filename="test.rtf",
        file_type="rtf",
        file_size=1024,
        content=b"encrypted_content",
        content_hash="abc123",
        encryption_key_id="key-123",
        medcat_status="pending",
        contains_phi=True,
        phi_types=["NAME", "NHS_NUMBER"],
        uploaded_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


class TestDocumentService:
    """Test document service functionality."""

    @pytest.mark.asyncio
    async def test_upload_document_success(
        self, document_service, mock_db, mock_audit_service, sample_user
    ):
        """Test successful document upload."""
        # Arrange
        file = AsyncMock()
        file.filename = "test.rtf"
        file.read = AsyncMock(return_value=b"test content")

        project_id = uuid4()
        mock_db.get.return_value = MagicMock()  # Project exists
        mock_db.scalar = AsyncMock(return_value=None)  # No duplicate

        with patch('app.services.document_service.encrypt_document') as mock_encrypt:
            mock_encrypt.return_value = (b"encrypted", "key-123")

            # Act
            result = await document_service.upload_document(
                file=file,
                project_id=project_id,
                user=sample_user,
                document_type="clinical_letter"
            )

        # Assert
        assert result is not None
        assert mock_db.add.called
        assert mock_db.commit.called
        mock_audit_service.log_document_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_document_invalid_file_type(
        self, document_service, sample_user
    ):
        """Test upload with invalid file type."""
        # Arrange
        file = AsyncMock()
        file.filename = "test.exe"

        # Act & Assert
        with pytest.raises(Exception) as exc:
            await document_service.upload_document(
                file=file,
                project_id=uuid4(),
                user=sample_user
            )
        assert "Unsupported file type" in str(exc.value)

    @pytest.mark.asyncio
    async def test_upload_document_file_too_large(
        self, document_service, sample_user
    ):
        """Test upload with file exceeding size limit."""
        # Arrange
        file = AsyncMock()
        file.filename = "test.rtf"
        file.read = AsyncMock(return_value=b"x" * (11 * 1024 * 1024))  # 11MB

        # Act & Assert
        with pytest.raises(Exception) as exc:
            await document_service.upload_document(
                file=file,
                project_id=uuid4(),
                user=sample_user
            )
        assert "exceeds maximum" in str(exc.value)

    @pytest.mark.asyncio
    async def test_get_document_with_content(
        self, document_service, mock_db, mock_audit_service, sample_user, sample_document
    ):
        """Test retrieving document with decrypted content."""
        # Arrange
        mock_db.get.return_value = sample_document

        with patch('app.services.document_service.decrypt_document') as mock_decrypt:
            mock_decrypt.return_value = b"decrypted content"

            # Act
            result = await document_service.get_document(
                document_id=sample_document.id,
                user=sample_user,
                include_content=True
            )

        # Assert
        assert result is not None
        assert result.content == "decrypted content"
        mock_audit_service.log_phi_access.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_not_found(
        self, document_service, mock_db, sample_user
    ):
        """Test getting non-existent document."""
        # Arrange
        mock_db.get.return_value = None

        # Act & Assert
        with pytest.raises(Exception) as exc:
            await document_service.get_document(
                document_id=uuid4(),
                user=sample_user
            )
        assert "not found" in str(exc.value)

    @pytest.mark.asyncio
    async def test_list_documents_with_filter(
        self, document_service, mock_db, mock_audit_service, sample_user
    ):
        """Test listing documents with filters."""
        # Arrange
        filter = DocumentFilter(
            medcat_status="complete",
            contains_phi=True
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_document()]
        mock_db.execute.return_value = mock_result
        mock_db.scalar.return_value = 1  # Total count

        # Act
        documents, total = await document_service.list_documents(
            user=sample_user,
            filter=filter,
            page=1,
            page_size=20
        )

        # Assert
        assert len(documents) == 1
        assert total == 1
        mock_audit_service.log_phi_access.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_document_soft(
        self, document_service, mock_db, mock_audit_service, sample_user, sample_document
    ):
        """Test soft delete of document."""
        # Arrange
        mock_db.get.return_value = sample_document

        # Act
        result = await document_service.delete_document(
            document_id=sample_document.id,
            user=sample_user,
            soft_delete=True
        )

        # Assert
        assert result is True
        assert sample_document.medcat_status == "deleted"
        mock_db.commit.assert_called_once()
        mock_audit_service.log_document_deletion.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_processing_status(
        self, document_service, mock_db, sample_document
    ):
        """Test updating document processing status."""
        # Arrange
        mock_db.get.return_value = sample_document

        # Act
        await document_service.update_processing_status(
            document_id=sample_document.id,
            status="complete"
        )

        # Assert
        assert sample_document.medcat_status == "complete"
        assert sample_document.medcat_processed_at is not None
        mock_db.commit.assert_called_once()

    def test_compute_content_hash(self, document_service):
        """Test content hash computation."""
        # Arrange
        content = b"test content"

        # Act
        hash_value = document_service._compute_content_hash(content)

        # Assert
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA-256 produces 64 hex characters