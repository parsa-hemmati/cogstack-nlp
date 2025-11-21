"""
Integration tests for Timeline API endpoint (Task #001).

Tests POST /api/v1/timeline/patient/{patient_id} with filters, pagination, and auth.

PRD Specification: Task file .claude/ccpm/epics/timeline-module/001.md
Test Coverage: Timeline retrieval API endpoint
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestTimelineAPI:
    """
    Integration tests for POST /api/v1/timeline/patient/{patient_id}.

    Acceptance Criteria:
    - Endpoint returns correct events for patient_id
    - Filtering works (date range, event types, specialty)
    - Pagination works correctly
    - Response time <500ms for 1,000 events
    - Audit log entry created for each request
    - All error cases handled
    """

    async def test_get_patient_timeline_success(
        self,
        client: AsyncClient,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test POST /api/v1/timeline/patient/{patient_id} returns timeline successfully.

        Acceptance Criteria:
        - POST returns 200 OK
        - Response includes patient_id, patient_name, events, total_events, metadata
        - Events are chronologically ordered
        - Default filters applied (all event types)
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request_data = {
            "date_range": {
                "start": "2023-01-01T00:00:00Z",
                "end": "2023-12-31T23:59:59Z"
            },
            "event_types": ["diagnosis", "procedure", "medication", "lab", "visit"],
            "page": 1,
            "page_size": 100
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_data,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "patient_id" in data
        assert "patient_name" in data
        assert "events" in data
        assert "total_events" in data
        assert "metadata" in data
        assert isinstance(data["events"], list)
        assert data["total_events"] >= 0

        # Verify chronological ordering
        if len(data["events"]) > 1:
            dates = [datetime.fromisoformat(event["date"].replace("Z", "+00:00")) for event in data["events"]]
            assert dates == sorted(dates), "Events should be in chronological order"

    async def test_timeline_date_range_filter(
        self,
        client: AsyncClient,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test date range filtering works correctly.

        Acceptance Criteria:
        - Only events within date range are returned
        - Events outside date range are excluded
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        start_date = datetime(2023, 6, 1, 0, 0, 0)
        end_date = datetime(2023, 6, 30, 23, 59, 59)

        request_data = {
            "date_range": {
                "start": start_date.isoformat() + "Z",
                "end": end_date.isoformat() + "Z"
            },
            "event_types": ["diagnosis", "procedure", "medication", "lab", "visit"],
            "page": 1,
            "page_size": 100
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_data,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify all events are within date range
        for event in data["events"]:
            event_date = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
            assert start_date <= event_date <= end_date

    async def test_timeline_event_types_filter(
        self,
        client: AsyncClient,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test event_types filtering works correctly.

        Acceptance Criteria:
        - Only specified event types are returned
        - Other event types are excluded
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request_data = {
            "date_range": {
                "start": "2023-01-01T00:00:00Z",
                "end": "2023-12-31T23:59:59Z"
            },
            "event_types": ["diagnosis", "medication"],  # Only these two
            "page": 1,
            "page_size": 100
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_data,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify only specified event types are returned
        for event in data["events"]:
            assert event["event_type"] in ["diagnosis", "medication"]

    async def test_timeline_specialty_filter(
        self,
        client: AsyncClient,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test specialty_filter works correctly.

        Acceptance Criteria:
        - Only events from specified specialty are returned
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request_data = {
            "date_range": {
                "start": "2023-01-01T00:00:00Z",
                "end": "2023-12-31T23:59:59Z"
            },
            "event_types": ["diagnosis", "procedure", "medication", "lab", "visit"],
            "specialty_filter": "cardiology",
            "page": 1,
            "page_size": 100
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_data,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify all events are from cardiology specialty
        for event in data["events"]:
            if "specialty" in event:
                assert event["specialty"].lower() == "cardiology"

    async def test_timeline_pagination(
        self,
        client: AsyncClient,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test pagination works correctly.

        Acceptance Criteria:
        - Page 1 returns first N events
        - Page 2 returns next N events
        - page_size limits results
        - total_events reflects total count
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]

        # Request page 1
        request_page1 = {
            "date_range": {
                "start": "2023-01-01T00:00:00Z",
                "end": "2023-12-31T23:59:59Z"
            },
            "event_types": ["diagnosis", "procedure", "medication", "lab", "visit"],
            "page": 1,
            "page_size": 10
        }

        # Act
        response_page1 = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_page1,
            headers=auth_headers_clinician
        )

        # Assert page 1
        assert response_page1.status_code == 200
        data_page1 = response_page1.json()
        assert len(data_page1["events"]) <= 10

        # If there are more events, test page 2
        if data_page1["total_events"] > 10:
            request_page2 = {**request_page1, "page": 2}
            response_page2 = await client.post(
                f"/api/v1/timeline/patient/{patient_id}",
                json=request_page2,
                headers=auth_headers_clinician
            )

            assert response_page2.status_code == 200
            data_page2 = response_page2.json()

            # Verify page 1 and page 2 have different events
            if data_page1["events"] and data_page2["events"]:
                page1_ids = {event["id"] for event in data_page1["events"]}
                page2_ids = {event["id"] for event in data_page2["events"]}
                assert page1_ids.isdisjoint(page2_ids), "Pages should have different events"

    async def test_timeline_requires_authentication(
        self,
        client: AsyncClient,
        test_db_with_timeline_data
    ):
        """
        Test endpoint requires authentication.

        Acceptance Criteria:
        - Request without JWT token returns 401 Unauthorized
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request_data = {
            "date_range": {
                "start": "2023-01-01T00:00:00Z",
                "end": "2023-12-31T23:59:59Z"
            },
            "event_types": ["diagnosis"],
            "page": 1,
            "page_size": 100
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_data
        )

        # Assert
        assert response.status_code == 401

    async def test_timeline_requires_authorization(
        self,
        client: AsyncClient,
        auth_headers_researcher,
        test_db_with_timeline_data
    ):
        """
        Test endpoint checks user has access to patient (RBAC).

        Acceptance Criteria:
        - User without access to patient returns 403 Forbidden
        """
        # Arrange
        patient_id = uuid4()  # Patient user doesn't have access to
        request_data = {
            "date_range": {
                "start": "2023-01-01T00:00:00Z",
                "end": "2023-12-31T23:59:59Z"
            },
            "event_types": ["diagnosis"],
            "page": 1,
            "page_size": 100
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_data,
            headers=auth_headers_researcher
        )

        # Assert
        # Note: May return 404 if patient not found, or 403 if access denied
        assert response.status_code in [403, 404]

    async def test_timeline_patient_not_found(
        self,
        client: AsyncClient,
        auth_headers_clinician
    ):
        """
        Test returns 404 for non-existent patient.

        Acceptance Criteria:
        - Request for non-existent patient_id returns 404 Not Found
        """
        # Arrange
        patient_id = uuid4()
        request_data = {
            "date_range": {
                "start": "2023-01-01T00:00:00Z",
                "end": "2023-12-31T23:59:59Z"
            },
            "event_types": ["diagnosis"],
            "page": 1,
            "page_size": 100
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_data,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 404

    async def test_timeline_invalid_date_range(
        self,
        client: AsyncClient,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test returns 400 for invalid date range (start > end).

        Acceptance Criteria:
        - Invalid date range returns 400 Bad Request
        - Error message describes the validation issue
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request_data = {
            "date_range": {
                "start": "2023-12-31T23:59:59Z",
                "end": "2023-01-01T00:00:00Z"  # End before start
            },
            "event_types": ["diagnosis"],
            "page": 1,
            "page_size": 100
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_data,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 400

    async def test_timeline_invalid_page(
        self,
        client: AsyncClient,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test returns 400 for invalid pagination parameters.

        Acceptance Criteria:
        - page < 1 returns 400 Bad Request
        - page_size < 1 returns 400 Bad Request
        - page_size > 10000 returns 400 Bad Request
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]

        # Test page < 1
        request_data_page = {
            "date_range": {
                "start": "2023-01-01T00:00:00Z",
                "end": "2023-12-31T23:59:59Z"
            },
            "event_types": ["diagnosis"],
            "page": 0,
            "page_size": 100
        }

        response = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_data_page,
            headers=auth_headers_clinician
        )

        assert response.status_code == 400

        # Test page_size < 1
        request_data_size_low = {
            "date_range": {
                "start": "2023-01-01T00:00:00Z",
                "end": "2023-12-31T23:59:59Z"
            },
            "event_types": ["diagnosis"],
            "page": 1,
            "page_size": 0
        }

        response = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_data_size_low,
            headers=auth_headers_clinician
        )

        assert response.status_code == 400

        # Test page_size > 10000
        request_data_size_high = {
            "date_range": {
                "start": "2023-01-01T00:00:00Z",
                "end": "2023-12-31T23:59:59Z"
            },
            "event_types": ["diagnosis"],
            "page": 1,
            "page_size": 10001
        }

        response = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_data_size_high,
            headers=auth_headers_clinician
        )

        assert response.status_code == 400

    async def test_timeline_creates_audit_log(
        self,
        client: AsyncClient,
        auth_headers_clinician,
        test_db_with_timeline_data,
        test_db
    ):
        """
        Test HIPAA audit log is created for every timeline access.

        Acceptance Criteria:
        - Audit log entry created with user_id, patient_id, timestamp, action="VIEW_TIMELINE"
        - IP address captured
        """
        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request_data = {
            "date_range": {
                "start": "2023-01-01T00:00:00Z",
                "end": "2023-12-31T23:59:59Z"
            },
            "event_types": ["diagnosis"],
            "page": 1,
            "page_size": 100
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_data,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 200

        # Verify audit log entry was created
        from sqlalchemy import select
        from app.models.audit_log import AuditLog

        async with test_db() as session:
            result = await session.execute(
                select(AuditLog)
                .where(AuditLog.action == "VIEW_TIMELINE")
                .where(AuditLog.details.contains(str(patient_id)))
                .order_by(AuditLog.created_at.desc())
                .limit(1)
            )
            audit_entry = result.scalar_one_or_none()

            assert audit_entry is not None
            assert "VIEW_TIMELINE" in audit_entry.action
            assert str(patient_id) in audit_entry.details

    async def test_timeline_no_phi_in_errors(
        self,
        client: AsyncClient,
        auth_headers_clinician
    ):
        """
        Test error messages don't expose PHI.

        Acceptance Criteria:
        - Error responses don't include patient identifiable information
        - Generic error messages are returned
        """
        # Arrange
        patient_id = uuid4()
        request_data = {
            "date_range": {
                "start": "2023-01-01T00:00:00Z",
                "end": "2023-12-31T23:59:59Z"
            },
            "event_types": ["diagnosis"],
            "page": 1,
            "page_size": 100
        }

        # Act
        response = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_data,
            headers=auth_headers_clinician
        )

        # Assert
        assert response.status_code == 404
        data = response.json()

        # Error message should be generic
        assert "detail" in data
        # Should not contain patient_id or PHI
        assert str(patient_id) not in str(data["detail"])

    async def test_timeline_response_time_under_500ms(
        self,
        client: AsyncClient,
        auth_headers_clinician,
        test_db_with_timeline_data
    ):
        """
        Test response time is under 500ms for 1,000 events.

        Acceptance Criteria:
        - Response time < 500ms for timeline with 1,000 events
        """
        import time

        # Arrange
        patient_id = test_db_with_timeline_data["patient_id"]
        request_data = {
            "date_range": {
                "start": "2023-01-01T00:00:00Z",
                "end": "2023-12-31T23:59:59Z"
            },
            "event_types": ["diagnosis", "procedure", "medication", "lab", "visit"],
            "page": 1,
            "page_size": 1000
        }

        # Act
        start_time = time.time()
        response = await client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            json=request_data,
            headers=auth_headers_clinician
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert response.status_code == 200
        assert elapsed_time < 0.5, f"Response time {elapsed_time:.3f}s exceeded 500ms threshold"
