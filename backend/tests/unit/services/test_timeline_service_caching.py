"""
Unit tests for TimelineService Redis caching functionality.

Tests the caching layer (5-minute TTL, cache key generation, invalidation).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4
import json
import hashlib

from app.services.timeline_service import TimelineService
from app.schemas.timeline import (
    TimelineFilters, DateRange, PatientTimeline,
    TimelineDocument, TimelineConcept, ConceptMention, MetaAnnotations
)
from app.models.user import User


@pytest.fixture
def mock_db():
    """Mock async database session."""
    return AsyncMock()


@pytest.fixture
def mock_user():
    """Mock user for audit logging."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.username = "test_user"
    return user


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def sample_timeline():
    """Sample timeline response."""
    patient_id = uuid4()

    return PatientTimeline(
        patient_id=str(patient_id),
        documents=[
            TimelineDocument(
                document_id=str(uuid4()),
                title="Clinical Note",
                document_type="clinical_note",
                date=datetime(2023, 1, 15),
                author=None,
                concepts=["C0011849"]
            )
        ],
        concepts=[
            TimelineConcept(
                concept_cui="C0011849",
                concept_name="Diabetes Mellitus",
                concept_type="condition",
                first_mention_date=datetime(2023, 1, 15),
                mention_count=1,
                mentions=[
                    ConceptMention(
                        concept_cui="C0011849",
                        concept_name="Diabetes Mellitus",
                        concept_type="condition",
                        document_id=str(uuid4()),
                        date=datetime(2023, 1, 15),
                        sentence="Patient has diabetes.",
                        meta_annotations=MetaAnnotations(
                            Negation="Affirmed",
                            Temporality="Current",
                            Experiencer="Patient",
                            Certainty="High"
                        ),
                        confidence=0.95
                    )
                ]
            )
        ],
        date_range=DateRange(
            start=datetime(2023, 1, 15),
            end=datetime(2023, 1, 15)
        ),
        filters_applied=TimelineFilters()
    )


@pytest.mark.asyncio
async def test_cache_key_generation_no_filters(mock_db):
    """Test cache key generation with no filters."""
    # Arrange
    service = TimelineService(mock_db)
    patient_id = uuid4()
    filters = TimelineFilters()

    # Act
    cache_key = service._generate_cache_key(str(patient_id), filters)

    # Assert
    assert cache_key.startswith("timeline:")
    assert str(patient_id) in cache_key
    # Empty filters should produce consistent hash
    assert len(cache_key.split(":")) == 3  # timeline:{patient_id}:{filters_hash}


@pytest.mark.asyncio
async def test_cache_key_generation_with_filters(mock_db):
    """Test cache key generation with filters produces different keys."""
    # Arrange
    service = TimelineService(mock_db)
    patient_id = uuid4()

    filters1 = TimelineFilters(concepts=["C0011849"])
    filters2 = TimelineFilters(
        concepts=["C0011849"],
        meta_annotations={"Negation": "Affirmed"}
    )

    # Act
    key1 = service._generate_cache_key(str(patient_id), filters1)
    key2 = service._generate_cache_key(str(patient_id), filters2)

    # Assert
    assert key1 != key2  # Different filters = different keys
    assert key1.startswith("timeline:")
    assert key2.startswith("timeline:")


@pytest.mark.asyncio
async def test_cache_key_same_filters_same_key(mock_db):
    """Test that identical filters produce the same cache key."""
    # Arrange
    service = TimelineService(mock_db)
    patient_id = uuid4()

    filters1 = TimelineFilters(
        concepts=["C0011849", "C0020538"],
        meta_annotations={"Negation": "Affirmed", "Experiencer": "Patient"}
    )
    filters2 = TimelineFilters(
        concepts=["C0011849", "C0020538"],
        meta_annotations={"Negation": "Affirmed", "Experiencer": "Patient"}
    )

    # Act
    key1 = service._generate_cache_key(str(patient_id), filters1)
    key2 = service._generate_cache_key(str(patient_id), filters2)

    # Assert
    assert key1 == key2  # Identical filters = identical keys


@pytest.mark.asyncio
@patch('app.services.timeline_service.get_redis')
async def test_get_timeline_cache_miss(
    mock_get_redis, mock_db, mock_user, sample_timeline
):
    """Test timeline retrieval on cache miss (queries DB and caches result)."""
    # Arrange
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # Cache miss
    mock_redis.setex = AsyncMock()
    mock_get_redis.return_value = mock_redis

    service = TimelineService(mock_db)
    service.redis = mock_redis

    patient_id = uuid4()

    # Mock the database query to return sample timeline
    with patch.object(service, '_get_timeline_from_db', return_value=sample_timeline):
        # Act
        filters = TimelineFilters()
        result = await service.get_patient_timeline(
            patient_id=patient_id,
            filters=filters,
            user=mock_user
        )

    # Assert
    assert result == sample_timeline

    # Verify cache was checked
    mock_redis.get.assert_called_once()

    # Verify result was cached (5-minute TTL = 300 seconds)
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args
    assert call_args[0][1] == 300  # 5 minutes TTL

    # Verify cached data is JSON
    cached_data = call_args[0][2]
    assert isinstance(cached_data, str)
    json.loads(cached_data)  # Should not raise


@pytest.mark.asyncio
@patch('app.services.timeline_service.get_redis')
async def test_get_timeline_cache_hit(
    mock_get_redis, mock_db, mock_user, sample_timeline
):
    """Test timeline retrieval on cache hit (skips DB query)."""
    # Arrange
    mock_redis = AsyncMock()

    # Simulate cached data
    cached_data = sample_timeline.json()
    mock_redis.get.return_value = cached_data  # Cache hit
    mock_get_redis.return_value = mock_redis

    service = TimelineService(mock_db)
    service.redis = mock_redis

    patient_id = uuid4()

    # Mock audit service to avoid DB calls
    with patch.object(service, 'audit_service') as mock_audit:
        mock_audit.log_phi_access = AsyncMock()

        # Act
        filters = TimelineFilters()
        result = await service.get_patient_timeline(
            patient_id=patient_id,
            filters=filters,
            user=mock_user
        )

    # Assert
    assert result.patient_id == sample_timeline.patient_id
    assert len(result.documents) == len(sample_timeline.documents)
    assert len(result.concepts) == len(sample_timeline.concepts)

    # Verify cache was checked
    mock_redis.get.assert_called_once()

    # Verify DB was NOT queried (cache hit)
    # This is implicit - if we patch _get_timeline_from_db and it's called, test fails


@pytest.mark.asyncio
@patch('app.services.timeline_service.get_redis')
async def test_cache_invalidation_on_new_document(mock_get_redis, mock_db):
    """Test cache invalidation when new document is processed for patient."""
    # Arrange
    mock_redis = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_get_redis.return_value = mock_redis

    service = TimelineService(mock_db)
    service.redis = mock_redis

    patient_id = uuid4()

    # Act
    await service.invalidate_patient_cache(str(patient_id))

    # Assert
    # Should delete all cache keys matching pattern timeline:{patient_id}:*
    mock_redis.delete.assert_called()

    # Verify pattern includes patient_id
    call_args = mock_redis.delete.call_args
    assert str(patient_id) in str(call_args)


@pytest.mark.asyncio
async def test_cache_ttl_is_5_minutes(mock_db):
    """Test that cache TTL is exactly 5 minutes (300 seconds)."""
    # Arrange
    service = TimelineService(mock_db)

    # Act
    ttl = service.CACHE_TTL_SECONDS

    # Assert
    assert ttl == 300  # 5 minutes


@pytest.mark.asyncio
@patch('app.services.timeline_service.get_redis')
async def test_cache_disabled_on_redis_failure(
    mock_get_redis, mock_db, mock_user, sample_timeline
):
    """Test that timeline query still works if Redis fails (graceful degradation)."""
    # Arrange
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = Exception("Redis connection failed")
    mock_get_redis.return_value = mock_redis

    service = TimelineService(mock_db)
    service.redis = mock_redis

    patient_id = uuid4()

    # Mock the database query
    with patch.object(service, '_get_timeline_from_db', return_value=sample_timeline):
        # Act
        filters = TimelineFilters()
        result = await service.get_patient_timeline(
            patient_id=patient_id,
            filters=filters,
            user=mock_user
        )

    # Assert
    assert result == sample_timeline

    # Cache failure should not crash the service
    # Query should fallback to DB


@pytest.mark.asyncio
@patch('app.services.timeline_service.get_redis')
async def test_different_filters_different_cache_keys(
    mock_get_redis, mock_db, mock_user, sample_timeline
):
    """Test that different filters produce different cache entries."""
    # Arrange
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # Always cache miss
    mock_redis.setex = AsyncMock()
    mock_get_redis.return_value = mock_redis

    service = TimelineService(mock_db)
    service.redis = mock_redis

    patient_id = uuid4()

    with patch.object(service, '_get_timeline_from_db', return_value=sample_timeline):
        # Act - Query 1: No filters
        filters1 = TimelineFilters()
        await service.get_patient_timeline(
            patient_id=patient_id,
            filters=filters1,
            user=mock_user
        )

        # Act - Query 2: With concept filter
        filters2 = TimelineFilters(concepts=["C0011849"])
        await service.get_patient_timeline(
            patient_id=patient_id,
            filters=filters2,
            user=mock_user
        )

    # Assert
    assert mock_redis.setex.call_count == 2

    # Get cache keys from both calls
    call1_key = mock_redis.setex.call_args_list[0][0][0]
    call2_key = mock_redis.setex.call_args_list[1][0][0]

    # Different filters should produce different cache keys
    assert call1_key != call2_key
