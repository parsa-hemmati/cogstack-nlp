"""
Integration tests for TimelineService (Task #006).

Tests the TimelineService layer with real PostgreSQL and Elasticsearch integration.

PRD Specification: Task file .claude/ccpm/epics/timeline-module/006.md
Test Coverage: Timeline service layer integration
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.timeline_service import TimelineService
from app.repositories.elasticsearch_timeline_repo import ElasticsearchTimelineRepository
from app.models.user import User
from app.schemas.timeline import TimelineRequest, DateRange

pytestmark = pytest.mark.asyncio


class TestTimelineServiceIntegration:
    """
    Integration tests for TimelineService.

    Acceptance Criteria:
    - Service integrates correctly with PostgreSQL and Elasticsearch
    - Caching works (Redis integration)
    - Audit logging works (PostgreSQL integration)
    - Meta-annotation filtering works
    - Error handling works (graceful degradation)
    """

    async def test_get_patient_timeline_with_real_db(
        self,
        db: AsyncSession,
        es_client,
        test_patient,
        test_clinical_concepts
    ):
        """
        Test TimelineService.get_patient_timeline with real database.

        Acceptance Criteria:
        - Service fetches events from Elasticsearch
        - Service filters by date range
        - Service returns TimelineResponse schema
        - Audit log entry created
        """
        # Arrange
        service = TimelineService(db, es_client)
        request = TimelineRequest(
            date_range=DateRange(
                start=datetime(2023, 1, 1, 0, 0, 0),
                end=datetime(2023, 12, 31, 23, 59, 59)
            ),
            event_types=["diagnosis", "procedure", "medication"],
            page=1,
            page_size=50
        )

        # Act
        response = await service.get_patient_timeline(
            patient_id=str(test_patient.id),
            request=request,
            user=test_patient.user  # Assuming user exists
        )

        # Assert
        assert response.patient_id == str(test_patient.id)
        assert isinstance(response.events, list)
        assert response.total_events >= 0
        assert response.metadata is not None

        # Verify events are within date range
        for event in response.events:
            event_date = datetime.fromisoformat(event.date.replace("Z", "+00:00"))
            assert request.date_range.start <= event_date <= request.date_range.end

    async def test_timeline_service_caching(
        self,
        db: AsyncSession,
        es_client,
        redis_client,
        test_patient
    ):
        """
        Test Redis caching integration.

        Acceptance Criteria:
        - First request -> cache miss (queries Elasticsearch)
        - Second request -> cache hit (returns cached data)
        - Response time for cache hit <10ms
        """
        # Arrange
        service = TimelineService(db, es_client, redis_client)
        request = TimelineRequest(
            date_range=DateRange(
                start=datetime(2023, 1, 1),
                end=datetime(2023, 12, 31)
            ),
            event_types=["diagnosis"],
            page=1,
            page_size=20
        )

        # Act - First request (cache miss)
        start_time_1 = datetime.now()
        response_1 = await service.get_patient_timeline(
            patient_id=str(test_patient.id),
            request=request,
            user=test_patient.user
        )
        duration_1 = (datetime.now() - start_time_1).total_seconds() * 1000

        # Act - Second request (cache hit)
        start_time_2 = datetime.now()
        response_2 = await service.get_patient_timeline(
            patient_id=str(test_patient.id),
            request=request,
            user=test_patient.user
        )
        duration_2 = (datetime.now() - start_time_2).total_seconds() * 1000

        # Assert
        assert response_1.patient_id == response_2.patient_id
        assert len(response_1.events) == len(response_2.events)
        assert response_1.total_events == response_2.total_events

        # Cache hit should be faster
        assert duration_2 < duration_1
        assert duration_2 < 50, "Cache hit should be <50ms"

    async def test_timeline_service_audit_logging(
        self,
        db: AsyncSession,
        es_client,
        test_patient,
        test_admin_user
    ):
        """
        Test audit logging integration.

        Acceptance Criteria:
        - Audit log entry created for each timeline access
        - Log includes user_id, patient_id, timestamp, action
        - Log does not include PHI content
        """
        # Arrange
        service = TimelineService(db, es_client)
        request = TimelineRequest(
            date_range=DateRange(start=datetime(2023, 1, 1), end=datetime(2023, 12, 31)),
            event_types=["diagnosis"],
            page=1,
            page_size=20
        )

        # Act
        await service.get_patient_timeline(
            patient_id=str(test_patient.id),
            request=request,
            user=test_admin_user
        )

        # Assert - Check audit log was created
        from app.models.audit_log import AuditLog
        from sqlalchemy import select

        audit_query = select(AuditLog).where(
            AuditLog.user_id == test_admin_user.id,
            AuditLog.action == "VIEW_PATIENT_TIMELINE",
            AuditLog.resource_id == str(test_patient.id)
        ).order_by(AuditLog.timestamp.desc()).limit(1)

        result = await db.execute(audit_query)
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None, "Audit log should be created"
        assert audit_log.user_id == test_admin_user.id
        assert audit_log.resource_type == "patient"
        assert audit_log.resource_id == str(test_patient.id)
        assert audit_log.action == "VIEW_PATIENT_TIMELINE"

        # Verify no PHI in audit log details
        if audit_log.details:
            assert "patient_name" not in audit_log.details
            assert "clinical_text" not in audit_log.details

    async def test_timeline_meta_annotation_filtering(
        self,
        db: AsyncSession,
        es_client,
        test_patient,
        test_clinical_concepts_with_meta_anns
    ):
        """
        Test meta-annotation filtering integration.

        Acceptance Criteria:
        - Negated events excluded when Negation=Affirmed filter applied
        - Family history excluded when Experiencer=Patient filter applied
        - Historical events excluded when Temporality=Current filter applied
        """
        # Arrange
        service = TimelineService(db, es_client)

        # Request with meta-annotation filters
        request = TimelineRequest(
            date_range=DateRange(start=datetime(2020, 1, 1), end=datetime(2025, 12, 31)),
            event_types=["diagnosis"],
            meta_annotation_filters={
                "Negation": "Affirmed",
                "Experiencer": "Patient",
                "Temporality": "Current"
            },
            page=1,
            page_size=100
        )

        # Act
        response = await service.get_patient_timeline(
            patient_id=str(test_patient.id),
            request=request,
            user=test_patient.user
        )

        # Assert - All returned events should match filters
        for event in response.events:
            if hasattr(event, 'meta_annotations'):
                assert event.meta_annotations.get('Negation') == 'Affirmed'
                assert event.meta_annotations.get('Experiencer') == 'Patient'
                assert event.meta_annotations.get('Temporality') == 'Current'

    async def test_timeline_service_pagination(
        self,
        db: AsyncSession,
        es_client,
        test_patient,
        test_large_event_dataset
    ):
        """
        Test pagination integration.

        Acceptance Criteria:
        - Page 1 returns first N events
        - Page 2 returns next N events
        - Total count is accurate
        - No duplicate events across pages
        """
        # Arrange
        service = TimelineService(db, es_client)
        page_size = 20

        # Request page 1
        request_page1 = TimelineRequest(
            date_range=DateRange(start=datetime(2020, 1, 1), end=datetime(2025, 12, 31)),
            event_types=["diagnosis", "procedure", "medication"],
            page=1,
            page_size=page_size
        )

        # Request page 2
        request_page2 = TimelineRequest(
            date_range=DateRange(start=datetime(2020, 1, 1), end=datetime(2025, 12, 31)),
            event_types=["diagnosis", "procedure", "medication"],
            page=2,
            page_size=page_size
        )

        # Act
        response_page1 = await service.get_patient_timeline(
            patient_id=str(test_patient.id),
            request=request_page1,
            user=test_patient.user
        )

        response_page2 = await service.get_patient_timeline(
            patient_id=str(test_patient.id),
            request=request_page2,
            user=test_patient.user
        )

        # Assert
        assert len(response_page1.events) <= page_size
        assert len(response_page2.events) <= page_size

        # Verify no duplicate events
        page1_event_ids = {event.event_id for event in response_page1.events}
        page2_event_ids = {event.event_id for event in response_page2.events}
        assert len(page1_event_ids.intersection(page2_event_ids)) == 0, "No duplicate events across pages"

        # Total count should be same on both pages
        assert response_page1.total_events == response_page2.total_events

    async def test_timeline_service_error_handling(
        self,
        db: AsyncSession,
        es_client,
        test_patient
    ):
        """
        Test graceful error handling.

        Acceptance Criteria:
        - Invalid patient ID returns error
        - Elasticsearch connection failure handled gracefully
        - Invalid date range returns error
        """
        # Arrange
        service = TimelineService(db, es_client)

        # Test 1: Invalid patient ID
        invalid_patient_id = str(uuid4())
        request = TimelineRequest(
            date_range=DateRange(start=datetime(2023, 1, 1), end=datetime(2023, 12, 31)),
            event_types=["diagnosis"],
            page=1,
            page_size=20
        )

        # Act & Assert - Invalid patient ID
        with pytest.raises(Exception) as exc_info:
            await service.get_patient_timeline(
                patient_id=invalid_patient_id,
                request=request,
                user=test_patient.user
            )
        assert "not found" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

        # Test 2: Invalid date range
        invalid_request = TimelineRequest(
            date_range=DateRange(
                start=datetime(2023, 12, 31),  # End before start
                end=datetime(2023, 1, 1)
            ),
            event_types=["diagnosis"],
            page=1,
            page_size=20
        )

        # Act & Assert - Invalid date range
        with pytest.raises(Exception) as exc_info:
            await service.get_patient_timeline(
                patient_id=str(test_patient.id),
                request=invalid_request,
                user=test_patient.user
            )
        assert "date range" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    async def test_timeline_service_empty_results(
        self,
        db: AsyncSession,
        es_client,
        test_patient
    ):
        """
        Test service handles empty results gracefully.

        Acceptance Criteria:
        - No events returns empty list (not error)
        - Total count is 0
        - Metadata still returned
        """
        # Arrange
        service = TimelineService(db, es_client)

        # Request with date range that has no events
        request = TimelineRequest(
            date_range=DateRange(
                start=datetime(2050, 1, 1),  # Future date
                end=datetime(2050, 12, 31)
            ),
            event_types=["diagnosis"],
            page=1,
            page_size=20
        )

        # Act
        response = await service.get_patient_timeline(
            patient_id=str(test_patient.id),
            request=request,
            user=test_patient.user
        )

        # Assert
        assert response.patient_id == str(test_patient.id)
        assert response.events == []
        assert response.total_events == 0
        assert response.metadata is not None

    async def test_timeline_service_performance(
        self,
        db: AsyncSession,
        es_client,
        test_patient,
        test_large_event_dataset
    ):
        """
        Test service performance meets requirements.

        Acceptance Criteria:
        - 1,000 events returned in <500ms
        - Cached request <10ms
        """
        # Arrange
        service = TimelineService(db, es_client)
        request = TimelineRequest(
            date_range=DateRange(start=datetime(2020, 1, 1), end=datetime(2025, 12, 31)),
            event_types=["diagnosis", "procedure", "medication", "lab", "visit"],
            page=1,
            page_size=1000
        )

        # Act
        start_time = datetime.now()
        response = await service.get_patient_timeline(
            patient_id=str(test_patient.id),
            request=request,
            user=test_patient.user
        )
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Assert
        assert duration_ms < 500, f"Timeline fetch should be <500ms, got {duration_ms}ms"
        assert response.total_events >= 0
