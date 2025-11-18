"""
Unit tests for Patient Search Service (Task 4.3).

Tests the concept highlights functionality including snippet extraction,
meta-annotations display, and edge cases.
"""
import pytest
from datetime import date, datetime
from uuid import uuid4, UUID

from app.services.patient_search_service import PatientSearchService
from app.schemas.patient_search import SearchFilters, MetaAnnotationDisplay


class TestSnippetExtraction:
    """Test suite for _extract_snippet method."""

    def test_snippet_extraction_normal_case(self):
        """Test snippet extraction with concept in middle of text."""
        # Arrange
        service = PatientSearchService(None)  # No DB needed for this test
        text = (
            "Patient presents to emergency department with severe chest pain and shortness of breath. "
            "ECG shows atrial flutter with rapid ventricular response. "
            "Patient is hemodynamically stable and alert."
        )
        start_char = 94  # "atrial flutter"
        end_char = 108

        # Act
        snippet = service._extract_snippet(text, start_char, end_char)

        # Assert
        assert "atrial flutter" in snippet or "atrial_flutter" in snippet.replace("<b>", "").replace("</b>", "")
        assert "<b>atrial flutter</b>" in snippet
        assert "ECG shows" in snippet
        assert "with rapid" in snippet
        assert len(snippet) < len(text)  # Should be truncated

    def test_snippet_extraction_concept_at_start(self):
        """Test snippet extraction when concept is at the beginning of text."""
        # Arrange
        service = PatientSearchService(None)
        text = "Diabetes mellitus type 2 with poor glycemic control and multiple complications."
        start_char = 0
        end_char = 17  # "Diabetes mellitus"

        # Act
        snippet = service._extract_snippet(text, start_char, end_char)

        # Assert
        assert "<b>Diabetes mellitus</b>" in snippet
        assert snippet.startswith("<b>Diabetes") or snippet.startswith("...<b>Diabetes")
        assert "type 2" in snippet
        assert "..." in snippet  # Should have ellipsis at end

    def test_snippet_extraction_concept_at_end(self):
        """Test snippet extraction when concept is at the end of text."""
        # Arrange
        service = PatientSearchService(None)
        text = (
            "Patient has long history of cardiovascular disease. "
            "Most recent diagnosis is atrial flutter"
        )
        start_char = len(text) - len("atrial flutter")
        end_char = len(text)

        # Act
        snippet = service._extract_snippet(text, start_char, end_char)

        # Assert
        assert "<b>atrial flutter</b>" in snippet
        assert snippet.startswith("...")  # Should have ellipsis at start
        assert "diagnosis is" in snippet

    def test_snippet_extraction_short_text(self):
        """Test snippet extraction when text is shorter than 200 chars."""
        # Arrange
        service = PatientSearchService(None)
        text = "Patient has diabetes."
        start_char = 12
        end_char = 20  # "diabetes"

        # Act
        snippet = service._extract_snippet(text, start_char, end_char)

        # Assert
        assert "<b>diabetes</b>" in snippet
        assert "Patient has" in snippet
        # Should not have ellipsis for short text
        assert snippet.count("...") <= 1

    def test_snippet_extraction_edge_case_invalid_indices(self):
        """Test snippet extraction with invalid character indices."""
        # Arrange
        service = PatientSearchService(None)
        text = "Some text here"

        # Act - invalid indices should return fallback
        snippet = service._extract_snippet(text, -5, 10)

        # Assert
        assert len(snippet) <= 200
        assert snippet == text[:200]  # Fallback behavior

    def test_snippet_extraction_edge_case_start_after_end(self):
        """Test snippet extraction when start_char >= end_char."""
        # Arrange
        service = PatientSearchService(None)
        text = "Some text here"

        # Act
        snippet = service._extract_snippet(text, 10, 5)

        # Assert
        assert len(snippet) <= 200
        assert snippet == text[:200]  # Fallback behavior


class TestMetaAnnotationsDisplay:
    """Test suite for meta-annotations display."""

    def test_meta_annotations_all_present(self):
        """Test meta-annotations display when all fields are present."""
        # Arrange
        meta_anns = {
            "Negation": "Affirmed",
            "Temporality": "Current",
            "Experiencer": "Patient",
            "Certainty": "Confirmed",
        }

        # Act
        display = MetaAnnotationDisplay(**meta_anns)

        # Assert
        assert display.Negation == "Affirmed"
        assert display.Temporality == "Current"
        assert display.Experiencer == "Patient"
        assert display.Certainty == "Confirmed"

    def test_meta_annotations_unknown_values(self):
        """Test meta-annotations display with Unknown values."""
        # Arrange
        meta_anns = {
            "Negation": "Unknown",
            "Temporality": "Unknown",
            "Experiencer": "Unknown",
            "Certainty": "Unknown",
        }

        # Act
        display = MetaAnnotationDisplay(**meta_anns)

        # Assert
        assert display.Negation == "Unknown"
        assert display.Temporality == "Unknown"
        assert display.Experiencer == "Unknown"
        assert display.Certainty == "Unknown"


class TestSearchFilters:
    """Test suite for SearchFilters schema."""

    def test_search_filters_default_values(self):
        """Test SearchFilters with default values."""
        # Arrange & Act
        filters = SearchFilters()

        # Assert
        assert filters.temporal.value == "current"
        assert filters.includeNegated is False
        assert filters.includeFamily is False
        assert filters.dateRange is None

    def test_search_filters_custom_values(self):
        """Test SearchFilters with custom values."""
        # Arrange & Act
        filters = SearchFilters(
            temporal="historical",
            includeNegated=True,
            includeFamily=True,
        )

        # Assert
        assert filters.temporal.value == "historical"
        assert filters.includeNegated is True
        assert filters.includeFamily is True


class TestConceptHighlights:
    """Integration-style tests for get_concept_highlights (mocked DB)."""

    @pytest.mark.asyncio
    async def test_empty_results_no_matching_entities(self, mocker):
        """Test get_concept_highlights returns empty results when no entities match."""
        # Arrange
        mock_db = mocker.Mock()
        mock_db.execute = mocker.AsyncMock(return_value=mocker.Mock(all=lambda: []))

        service = PatientSearchService(mock_db)
        patient_id = uuid4()
        cui = "C0004238"

        # Act
        response = await service.get_concept_highlights(patient_id, cui)

        # Assert
        assert response.totalCount == 0
        assert len(response.documents) == 0

    @pytest.mark.asyncio
    async def test_highlights_with_filters(self, mocker):
        """Test get_concept_highlights applies filters correctly."""
        # Arrange
        mock_db = mocker.Mock()

        # Mock entity and document
        mock_entity = mocker.Mock()
        mock_entity.cui = "C0004238"
        mock_entity.pretty_name = "Atrial Flutter"
        mock_entity.start_char = 50
        mock_entity.end_char = 64
        mock_entity.meta_anns = {
            "Negation": "Affirmed",
            "Temporality": "Current",
            "Experiencer": "Patient",
            "Certainty": "Confirmed",
        }

        mock_document = mocker.Mock()
        mock_document.id = uuid4()
        mock_document.title = "ECG Report"
        mock_document.document_date = date(2024, 11, 18)
        mock_document.encrypted_content = b"some encrypted content"

        mock_db.execute = mocker.AsyncMock(
            return_value=mocker.Mock(all=lambda: [(mock_entity, mock_document)])
        )

        # Mock encryption service
        mocker.patch(
            "app.services.patient_search_service.EncryptionService"
        ).return_value.decrypt.return_value = (
            "Patient presents to emergency department with severe atrial flutter and rapid ventricular response."
        )

        service = PatientSearchService(mock_db)
        patient_id = uuid4()
        cui = "C0004238"
        filters = SearchFilters(includeNegated=False)

        # Act
        response = await service.get_concept_highlights(patient_id, cui, filters)

        # Assert
        assert response.totalCount == 1
        assert len(response.documents) == 1
        assert response.documents[0].documentId == str(mock_document.id)
        assert response.documents[0].title == "ECG Report"
        assert "<b>atrial flutter</b>" in response.documents[0].snippet
        assert response.documents[0].metaAnnotations.Negation == "Affirmed"
        assert response.documents[0].metaAnnotations.Temporality == "Current"


class TestHighlightsPerformance:
    """Performance-related tests for highlights."""

    @pytest.mark.asyncio
    async def test_highlights_response_time(self, mocker):
        """Test get_concept_highlights completes within 300ms target."""
        # Arrange
        mock_db = mocker.Mock()
        mock_db.execute = mocker.AsyncMock(return_value=mocker.Mock(all=lambda: []))

        service = PatientSearchService(mock_db)
        patient_id = uuid4()
        cui = "C0004238"

        # Act
        import time
        start = time.time()
        await service.get_concept_highlights(patient_id, cui)
        duration_ms = (time.time() - start) * 1000

        # Assert
        assert duration_ms < 300  # Target: <300ms
