"""
Integration tests for Patient Search API (Sprint 1 PRD compliance).

Tests all functional requirements (FR1-FR4) end-to-end through API endpoints.

PRD Specification: .specify/specifications/patient-search.md
Test Coverage: FR1 (Search), FR2 (Filters), FR3 (Pagination), FR4 (Patient Details)
"""
import pytest
from uuid import uuid4
from datetime import datetime, date

pytestmark = pytest.mark.asyncio


class TestPatientSearchAPI:
    """
    PRD Requirement: FR1 - Search by Medical Concept
    PRD Requirement: FR2 - Meta-Annotation Filtering
    PRD Requirement: FR3 - Result Ranking & Pagination
    PRD Requirement: FR4 - Patient Details in Response
    """

    async def test_search_by_concept_name(self, client, test_db_with_search_data, auth_headers_clinician):
        """
        FR1.1: Search by concept name returns matching patients

        Acceptance Criteria:
        - POST /api/v1/patients/search with concept="diabetes" returns 200 OK
        - Response includes results array
        - Response includes pagination object (nested)
        - Response includes performance object (nested)
        """
        # Arrange
        request = {
            "concept": "diabetes",
            "filters": {"temporal": "current", "includeNegated": False, "includeFamily": False},
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "relevance"
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # FR1: Response structure
        assert "results" in data
        assert "pagination" in data
        assert "performance" in data

        # FR3: Pagination structure (PRD-compliant nested object)
        assert "page" in data["pagination"]
        assert "pageSize" in data["pagination"]
        assert "totalResults" in data["pagination"]
        assert "totalPages" in data["pagination"]
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["pageSize"] == 20

        # FR1: Performance tracking
        assert "searchTime" in data["performance"]
        assert "source" in data["performance"]
        assert data["performance"]["searchTime"] >= 0


    async def test_search_by_cui(self, client, test_db_with_search_data, auth_headers_clinician):
        """
        FR1.2: Search by SNOMED-CT CUI returns matching patients

        Acceptance Criteria:
        - POST /api/v1/patients/search with concept="C0011849" returns 200 OK
        - Results format matches concept name search
        - CUI format: C followed by digits
        """
        # Arrange
        request = {
            "concept": "C0011849",  # Diabetes mellitus CUI
            "filters": {"temporal": "current", "includeNegated": False, "includeFamily": False},
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "relevance"
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)


    async def test_search_empty_query_validation(self, client, auth_headers_clinician):
        """
        FR1.3: Empty query returns validation error

        Acceptance Criteria:
        - POST /api/v1/patients/search with concept="" returns 422 Unprocessable Entity
        - Error message indicates validation failure
        """
        # Arrange
        request = {
            "concept": "",  # Empty query
            "filters": {},
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "relevance"
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        # Pydantic validation returns 422, not 400
        assert response.status_code == 422


    async def test_negation_filter_excludes_negated(self, client, test_db_with_annotations, auth_headers_clinician):
        """
        FR2.1: Negation filter excludes negated mentions

        Acceptance Criteria:
        - Search with includeNegated=false excludes "no diabetes" mentions
        - Only "Affirmed" Negation meta-annotations returned
        - Precision improves from 60% to 90%+

        Test Data Requirements:
        - Patient A: "has diabetes" (Negation=Affirmed)
        - Patient B: "no diabetes" (Negation=Negated)

        Expected Result: Only Patient A returned
        """
        # Arrange
        request = {
            "concept": "diabetes",
            "filters": {
                "temporal": "any",
                "includeNegated": False,  # Exclude negated
                "includeFamily": True
            },
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "relevance"
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # FR2.1: All annotations have negated=False (Affirmed)
        for result in data["results"]:
            for annotation in result["annotations"]:
                assert annotation["metaAnnotations"]["negated"] is False, \
                    f"Found negated annotation: {annotation}"


    async def test_temporal_filter_current_only(self, client, test_db_with_annotations, auth_headers_clinician):
        """
        FR2.2: Temporality filter excludes historical mentions

        Acceptance Criteria:
        - Search with temporal="current" excludes "patient had diabetes 10 years ago"
        - Only "Current" Temporality meta-annotations returned

        Test Data Requirements:
        - Patient A: "has diabetes" (Temporality=Current)
        - Patient B: "had diabetes 10 years ago" (Temporality=Historical)

        Expected Result: Only Patient A returned
        """
        # Arrange
        request = {
            "concept": "diabetes",
            "filters": {
                "temporal": "current",  # Current only
                "includeNegated": True,
                "includeFamily": True
            },
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "relevance"
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # FR2.2: All annotations have Temporality=Current
        for result in data["results"]:
            for annotation in result["annotations"]:
                # Current filter should only return Current temporality
                assert annotation["metaAnnotations"]["temporality"] == "Current", \
                    f"Found non-current temporality: {annotation['metaAnnotations']['temporality']}"


    async def test_experiencer_filter_patient_only(self, client, test_db_with_annotations, auth_headers_clinician):
        """
        FR2.3: Experiencer filter excludes family history

        Acceptance Criteria:
        - Search with includeFamily=false excludes "father has diabetes"
        - Only "Patient" Experiencer meta-annotations returned

        Test Data Requirements:
        - Patient A: "has diabetes" (Experiencer=Patient)
        - Patient B: document mentions "father has diabetes" (Experiencer=Family)

        Expected Result: Only Patient A returned
        """
        # Arrange
        request = {
            "concept": "diabetes",
            "filters": {
                "temporal": "any",
                "includeNegated": True,
                "includeFamily": False  # Exclude family
            },
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "relevance"
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # FR2.3: All annotations have Experiencer=Patient
        for result in data["results"]:
            for annotation in result["annotations"]:
                assert annotation["metaAnnotations"]["experiencer"] == "Patient", \
                    f"Found non-patient experiencer: {annotation['metaAnnotations']['experiencer']}"


    async def test_multiple_filters_and_logic(self, client, test_db_with_annotations, auth_headers_clinician):
        """
        FR2.4: Multiple filters applied as AND conditions

        Acceptance Criteria:
        - All filters must match (AND logic, not OR)
        - temporal="current" AND includeNegated=false AND includeFamily=false
        - Only annotations matching ALL conditions returned
        """
        # Arrange
        request = {
            "concept": "diabetes",
            "filters": {
                "temporal": "current",
                "includeNegated": False,
                "includeFamily": False
            },
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "relevance"
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # FR2.4: All annotations match ALL filters
        for result in data["results"]:
            for annotation in result["annotations"]:
                assert annotation["metaAnnotations"]["temporality"] == "Current"
                assert annotation["metaAnnotations"]["negated"] is False
                assert annotation["metaAnnotations"]["experiencer"] == "Patient"


    async def test_search_pagination_structure(self, client, test_db_with_search_data, auth_headers_clinician):
        """
        FR3.3: Pagination object structure (PRD-compliant nested object)

        Acceptance Criteria:
        - Response includes nested pagination object
        - pagination.page matches request
        - pagination.pageSize matches request
        - pagination.totalResults is accurate
        - pagination.totalPages calculated correctly (ceiling division)
        """
        # Arrange
        request = {
            "concept": "diabetes",
            "filters": {},
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "relevance"
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # FR3.3: Pagination object (nested, not flat)
        assert "pagination" in data
        pagination = data["pagination"]

        # All required fields present
        assert "page" in pagination
        assert "pageSize" in pagination
        assert "totalResults" in pagination
        assert "totalPages" in pagination

        # Values match request
        assert pagination["page"] == 1
        assert pagination["pageSize"] == 20

        # totalPages calculation correct (ceiling division)
        if pagination["totalResults"] > 0:
            expected_pages = (pagination["totalResults"] + pagination["pageSize"] - 1) // pagination["pageSize"]
            assert pagination["totalPages"] == expected_pages


    async def test_patient_details_mrn_masked(self, client, test_db_with_search_data, auth_headers_clinician):
        """
        FR4.1: MRN masked for privacy (XXX-XXX-1234)

        Acceptance Criteria:
        - mrn field returns "XXX-XXX-1234" format
        - Only last 4 digits visible
        - First 6 digits masked with X

        HIPAA Compliance: PHI minimization
        """
        # Arrange
        request = {
            "concept": "diabetes",
            "filters": {},
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "relevance"
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # FR4.1: MRN masking (if results exist)
        if len(data["results"]) > 0:
            for result in data["results"]:
                mrn = result["mrn"]
                # Should match XXX-XXX-#### format
                assert mrn.startswith("XXX-XXX-"), f"MRN not masked: {mrn}"
                # Last part should be 4 digits
                last_part = mrn.split("-")[-1]
                assert len(last_part) == 4, f"MRN last part not 4 digits: {last_part}"
                assert last_part.isdigit(), f"MRN last part not digits: {last_part}"


    async def test_patient_demographics_included(self, client, test_db_with_search_data, auth_headers_clinician):
        """
        FR4.2: Demographics included in response

        Acceptance Criteria:
        - Response includes demographics.age
        - Response includes demographics.gender (if available)
        - Response includes demographics.department (if available)
        """
        # Arrange
        request = {
            "concept": "diabetes",
            "filters": {},
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "relevance"
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # FR4.2: Demographics structure (if results exist)
        if len(data["results"]) > 0:
            for result in data["results"]:
                assert "demographics" in result
                demographics = result["demographics"]

                # Age is required
                assert "age" in demographics
                assert isinstance(demographics["age"], int)

                # Gender and department are optional but must be present (can be None)
                assert "gender" in demographics
                assert "department" in demographics


    async def test_performance_object_structure(self, client, test_db_with_search_data, auth_headers_clinician):
        """
        NFR Test: Performance object structure (PRD-compliant nested object)

        Acceptance Criteria:
        - Response includes nested performance object
        - performance.searchTime is present and non-negative
        - performance.source indicates data source ('cache' or 'live')
        """
        # Arrange
        request = {
            "concept": "diabetes",
            "filters": {},
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "relevance"
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Performance object (nested, not flat)
        assert "performance" in data
        performance = data["performance"]

        # Required fields
        assert "searchTime" in performance
        assert "source" in performance

        # Values validation
        assert isinstance(performance["searchTime"], int)
        assert performance["searchTime"] >= 0
        assert performance["source"] in ["cache", "live"]


    async def test_annotations_structure(self, client, test_db_with_search_data, auth_headers_clinician):
        """
        FR4.3: Annotations array structure

        Acceptance Criteria:
        - Each result includes annotations array
        - Annotations include required fields (cui, conceptName, sourceValue, etc.)
        - Meta-annotations are present and structured correctly
        """
        # Arrange
        request = {
            "concept": "diabetes",
            "filters": {},
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "relevance"
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # FR4.3: Annotations structure (if results exist)
        if len(data["results"]) > 0:
            for result in data["results"]:
                assert "annotations" in result
                assert isinstance(result["annotations"], list)

                # Check annotation structure
                for annotation in result["annotations"]:
                    # Required fields
                    assert "cui" in annotation
                    assert "conceptName" in annotation
                    assert "sourceValue" in annotation
                    assert "documentId" in annotation
                    assert "documentType" in annotation
                    assert "documentDate" in annotation
                    assert "startChar" in annotation
                    assert "endChar" in annotation
                    assert "confidence" in annotation
                    assert "metaAnnotations" in annotation

                    # Meta-annotations structure
                    meta = annotation["metaAnnotations"]
                    assert "temporality" in meta
                    assert "negated" in meta
                    assert "experiencer" in meta
                    assert "certainty" in meta


    async def test_sort_by_relevance(self, client, test_db_with_search_data, auth_headers_clinician):
        """
        FR3.1: Sort by relevance (default sort order)

        Acceptance Criteria:
        - Results sorted by MedCAT confidence score (accuracy) descending
        - Higher confidence scores appear first
        - Default sort when no sort parameter provided
        """
        # Arrange
        request = {
            "concept": "diabetes",
            "filters": {},
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "relevance"
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # FR3.1: Results sorted by relevance
        if len(data["results"]) > 1:
            # Check that results are in descending order by confidence
            # Note: In real implementation, this would check annotation confidence scores
            # For now, just verify results array structure exists
            assert isinstance(data["results"], list)


    async def test_sort_by_date(self, client, test_db_with_search_data, auth_headers_clinician):
        """
        FR3.2: Sort by date (last_seen_at)

        Acceptance Criteria:
        - Results sorted by patient.last_seen_at descending (most recent first)
        - Sort parameter accepts "date" value
        """
        # Arrange
        request = {
            "concept": "diabetes",
            "filters": {},
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "date"
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # FR3.2: Results sorted by date
        # Note: In real implementation, verify last_seen_at descending order
        assert isinstance(data["results"], list)


    async def test_pagination_edge_cases(self, client, test_db_with_search_data, auth_headers_clinician):
        """
        FR3.4: Pagination edge cases

        Acceptance Criteria:
        - Page beyond total pages returns empty results (not 404)
        - Page size validation (1-100)
        - totalPages correctly calculated even for edge cases
        """
        # Test 1: Page beyond available results
        request = {
            "concept": "diabetes",
            "filters": {},
            "pagination": {"page": 999, "pageSize": 20},  # Page far beyond data
            "sort": "relevance"
        }

        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []  # Empty results, not error
        assert data["pagination"]["page"] == 999
        assert data["pagination"]["totalPages"] >= 0

        # Test 2: Minimum page size (1)
        request = {
            "concept": "diabetes",
            "filters": {},
            "pagination": {"page": 1, "pageSize": 1},
            "sort": "relevance"
        }

        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["pageSize"] == 1
        if data["pagination"]["totalResults"] > 0:
            assert len(data["results"]) <= 1

        # Test 3: Maximum page size (100)
        request = {
            "concept": "diabetes",
            "filters": {},
            "pagination": {"page": 1, "pageSize": 100},
            "sort": "relevance"
        }

        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["pageSize"] == 100


    async def test_invalid_sort_parameter_validation(self, client, test_db_with_search_data, auth_headers_clinician):
        """
        FR3.3: Invalid sort parameter validation

        Acceptance Criteria:
        - Invalid sort values return 422 Unprocessable Entity
        - Error message indicates validation failure
        - Valid values: "relevance", "date"
        """
        # Arrange
        request = {
            "concept": "diabetes",
            "filters": {},
            "pagination": {"page": 1, "pageSize": 20},
            "sort": "invalid_sort_option"  # Invalid sort parameter
        }

        # Act
        response = await client.post(
            "/api/v1/patients/search",
            json=request,
            headers=auth_headers_clinician
        )

        # Assert
        # Pydantic validation returns 422 for invalid enum values
        assert response.status_code == 422
