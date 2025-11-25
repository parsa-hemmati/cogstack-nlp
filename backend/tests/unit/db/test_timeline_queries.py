"""
Unit tests for timeline Elasticsearch query builders.

Tests query construction for date range, event type, specialty, and meta-annotation filtering.
"""
import pytest
from datetime import datetime

from app.db.timeline_queries import (
    build_patient_timeline_query,
    build_concept_filter_query,
    build_date_range_filter,
    build_meta_annotation_filter,
    build_event_type_filter,
    build_specialty_filter
)
from app.schemas.timeline import DateRange


def test_build_basic_patient_query():
    """Test basic patient timeline query (patient_id only)."""
    # Arrange
    patient_id = "patient-123"

    # Act
    query = build_patient_timeline_query(patient_id)

    # Assert
    assert query == {
        "bool": {
            "must": [
                {"term": {"patient_id": patient_id}}
            ]
        }
    }


def test_build_query_with_concept_filter():
    """Test query with concept CUI filter."""
    # Arrange
    patient_id = "patient-123"
    concept_cuis = ["C0011849", "C0020538"]

    # Act
    query = build_patient_timeline_query(patient_id, concept_filter=concept_cuis)

    # Assert
    assert {"term": {"patient_id": patient_id}} in query["bool"]["must"]
    assert {"terms": {"concept_cui": concept_cuis}} in query["bool"]["must"]


def test_build_query_with_date_range():
    """Test query with date range filter."""
    # Arrange
    patient_id = "patient-123"
    date_range = DateRange(
        start=datetime(2023, 1, 1),
        end=datetime(2023, 12, 31)
    )

    # Act
    query = build_patient_timeline_query(patient_id, date_range=date_range)

    # Assert
    assert {"term": {"patient_id": patient_id}} in query["bool"]["must"]

    # Find the range filter
    range_filter = next(
        (f for f in query["bool"]["must"] if "range" in f),
        None
    )
    assert range_filter is not None
    assert range_filter["range"]["date"]["gte"] == "2023-01-01T00:00:00"
    assert range_filter["range"]["date"]["lte"] == "2023-12-31T00:00:00"


def test_build_query_with_meta_annotations():
    """Test query with meta-annotation filters."""
    # Arrange
    patient_id = "patient-123"
    meta_annotations = {
        "Negation": "Affirmed",
        "Experiencer": "Patient",
        "Temporality": ["Current", "Recent"]  # List value (OR logic)
    }

    # Act
    query = build_patient_timeline_query(patient_id, meta_annotations=meta_annotations)

    # Assert
    must_clauses = query["bool"]["must"]

    # Single value: exact match
    assert {"term": {"meta_annotations.Negation": "Affirmed"}} in must_clauses
    assert {"term": {"meta_annotations.Experiencer": "Patient"}} in must_clauses

    # List value: OR logic (terms query)
    assert {"terms": {"meta_annotations.Temporality": ["Current", "Recent"]}} in must_clauses


def test_build_query_with_event_type_filter():
    """Test query with event type filter."""
    # Arrange
    patient_id = "patient-123"
    event_types = ["condition", "medication"]

    # Act
    query = build_patient_timeline_query(patient_id, event_types=event_types)

    # Assert
    assert {"term": {"patient_id": patient_id}} in query["bool"]["must"]
    assert {"terms": {"concept_type": event_types}} in query["bool"]["must"]


def test_build_query_with_specialty_filter():
    """Test query with clinical specialty filter."""
    # Arrange
    patient_id = "patient-123"
    specialty = "cardiology"

    # Act
    query = build_patient_timeline_query(patient_id, specialty=specialty)

    # Assert
    assert {"term": {"patient_id": patient_id}} in query["bool"]["must"]
    assert {"term": {"specialty": specialty}} in query["bool"]["must"]


def test_build_query_with_all_filters():
    """Test query with all filter types combined."""
    # Arrange
    patient_id = "patient-123"
    concept_filter = ["C0011849"]
    date_range = DateRange(
        start=datetime(2023, 1, 1),
        end=datetime(2023, 12, 31)
    )
    meta_annotations = {"Negation": "Affirmed"}
    event_types = ["condition"]
    specialty = "cardiology"

    # Act
    query = build_patient_timeline_query(
        patient_id=patient_id,
        concept_filter=concept_filter,
        date_range=date_range,
        meta_annotations=meta_annotations,
        event_types=event_types,
        specialty=specialty
    )

    # Assert
    must_clauses = query["bool"]["must"]

    # All filters should be present
    assert {"term": {"patient_id": patient_id}} in must_clauses
    assert {"terms": {"concept_cui": concept_filter}} in must_clauses
    assert {"term": {"meta_annotations.Negation": "Affirmed"}} in must_clauses
    assert {"terms": {"concept_type": event_types}} in must_clauses
    assert {"term": {"specialty": specialty}} in must_clauses

    # Date range should be present
    range_filter = next((f for f in must_clauses if "range" in f), None)
    assert range_filter is not None


def test_build_concept_filter_query_single():
    """Test building concept filter for single CUI."""
    # Act
    filter_clause = build_concept_filter_query(["C0011849"])

    # Assert
    assert filter_clause == {"terms": {"concept_cui": ["C0011849"]}}


def test_build_concept_filter_query_multiple():
    """Test building concept filter for multiple CUIs."""
    # Act
    filter_clause = build_concept_filter_query(["C0011849", "C0020538", "C0004096"])

    # Assert
    assert filter_clause == {"terms": {"concept_cui": ["C0011849", "C0020538", "C0004096"]}}


def test_build_date_range_filter():
    """Test building date range filter."""
    # Arrange
    date_range = DateRange(
        start=datetime(2022, 6, 15, 10, 30),
        end=datetime(2023, 8, 20, 14, 45)
    )

    # Act
    filter_clause = build_date_range_filter(date_range)

    # Assert
    assert filter_clause == {
        "range": {
            "date": {
                "gte": "2022-06-15T10:30:00",
                "lte": "2023-08-20T14:45:00"
            }
        }
    }


def test_build_meta_annotation_filter_single_value():
    """Test building meta-annotation filter with single value."""
    # Act
    filter_clauses = build_meta_annotation_filter({"Negation": "Affirmed"})

    # Assert
    assert filter_clauses == [
        {"term": {"meta_annotations.Negation": "Affirmed"}}
    ]


def test_build_meta_annotation_filter_list_value():
    """Test building meta-annotation filter with list value (OR logic)."""
    # Act
    filter_clauses = build_meta_annotation_filter({
        "Temporality": ["Current", "Recent"]
    })

    # Assert
    assert filter_clauses == [
        {"terms": {"meta_annotations.Temporality": ["Current", "Recent"]}}
    ]


def test_build_meta_annotation_filter_mixed():
    """Test building meta-annotation filter with both single and list values."""
    # Act
    filter_clauses = build_meta_annotation_filter({
        "Negation": "Affirmed",
        "Experiencer": "Patient",
        "Temporality": ["Current", "Recent"]
    })

    # Assert
    assert {"term": {"meta_annotations.Negation": "Affirmed"}} in filter_clauses
    assert {"term": {"meta_annotations.Experiencer": "Patient"}} in filter_clauses
    assert {"terms": {"meta_annotations.Temporality": ["Current", "Recent"]}} in filter_clauses


def test_build_event_type_filter():
    """Test building event type filter."""
    # Act
    filter_clause = build_event_type_filter(["condition", "medication", "procedure"])

    # Assert
    assert filter_clause == {
        "terms": {"concept_type": ["condition", "medication", "procedure"]}
    }


def test_build_specialty_filter():
    """Test building specialty filter."""
    # Act
    filter_clause = build_specialty_filter("cardiology")

    # Assert
    assert filter_clause == {"term": {"specialty": "cardiology"}}


def test_build_specialty_filter_case_insensitive():
    """Test specialty filter is case-insensitive."""
    # Act
    filter_clause = build_specialty_filter("Cardiology")

    # Assert
    # Should be lowercased
    assert filter_clause == {"term": {"specialty": "cardiology"}}


def test_empty_concept_filter_returns_none():
    """Test that empty concept filter returns None."""
    # Act
    filter_clause = build_concept_filter_query([])

    # Assert
    assert filter_clause is None


def test_none_concept_filter_returns_none():
    """Test that None concept filter returns None."""
    # Act
    filter_clause = build_concept_filter_query(None)

    # Assert
    assert filter_clause is None


def test_empty_meta_annotations_returns_empty_list():
    """Test that empty meta-annotations returns empty list."""
    # Act
    filter_clauses = build_meta_annotation_filter({})

    # Assert
    assert filter_clauses == []


def test_none_meta_annotations_returns_empty_list():
    """Test that None meta-annotations returns empty list."""
    # Act
    filter_clauses = build_meta_annotation_filter(None)

    # Assert
    assert filter_clauses == []
