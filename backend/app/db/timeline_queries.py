"""
Elasticsearch query builders for patient timeline.

This module provides helper functions to construct Elasticsearch queries
for filtering patient timeline data by date range, event type, specialty,
and meta-annotations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from app.schemas.timeline import DateRange


def build_patient_timeline_query(
    patient_id: str,
    concept_filter: Optional[List[str]] = None,
    date_range: Optional[DateRange] = None,
    meta_annotations: Optional[Dict[str, Any]] = None,
    event_types: Optional[List[str]] = None,
    specialty: Optional[str] = None
) -> Dict[str, Any]:
    """Build complete Elasticsearch query for patient timeline.

    Args:
        patient_id: UUID of the patient
        concept_filter: List of concept CUIs to filter by
        date_range: Date range filter (inclusive)
        meta_annotations: Meta-annotation filters (key-value pairs)
        event_types: List of event types (condition, medication, procedure, etc.)
        specialty: Clinical specialty filter (e.g., "cardiology")

    Returns:
        Elasticsearch query dict

    Example:
        >>> query = build_patient_timeline_query(
        ...     patient_id="patient-123",
        ...     concept_filter=["C0011849"],
        ...     meta_annotations={"Negation": "Affirmed"}
        ... )
    """
    # Base query: patient_id must match
    must_clauses: List[Dict[str, Any]] = [
        {"term": {"patient_id": patient_id}}
    ]

    # Add concept filter
    if concept_filter:
        concept_clause = build_concept_filter_query(concept_filter)
        if concept_clause:
            must_clauses.append(concept_clause)

    # Add date range filter
    if date_range:
        date_clause = build_date_range_filter(date_range)
        must_clauses.append(date_clause)

    # Add meta-annotation filters
    if meta_annotations:
        meta_clauses = build_meta_annotation_filter(meta_annotations)
        must_clauses.extend(meta_clauses)

    # Add event type filter
    if event_types:
        event_clause = build_event_type_filter(event_types)
        must_clauses.append(event_clause)

    # Add specialty filter
    if specialty:
        specialty_clause = build_specialty_filter(specialty)
        must_clauses.append(specialty_clause)

    return {
        "bool": {
            "must": must_clauses
        }
    }


def build_concept_filter_query(concept_cuis: Optional[List[str]]) -> Optional[Dict[str, Any]]:
    """Build concept CUI filter query.

    Args:
        concept_cuis: List of SNOMED-CT CUIs

    Returns:
        Elasticsearch terms query or None if empty

    Example:
        >>> build_concept_filter_query(["C0011849", "C0020538"])
        {"terms": {"concept_cui": ["C0011849", "C0020538"]}}
    """
    if not concept_cuis:
        return None

    return {"terms": {"concept_cui": concept_cuis}}


def build_date_range_filter(date_range: DateRange) -> Dict[str, Any]:
    """Build date range filter query.

    Args:
        date_range: DateRange with start and end dates

    Returns:
        Elasticsearch range query

    Example:
        >>> build_date_range_filter(DateRange(
        ...     start=datetime(2023, 1, 1),
        ...     end=datetime(2023, 12, 31)
        ... ))
        {"range": {"date": {"gte": "2023-01-01T00:00:00", "lte": "2023-12-31T00:00:00"}}}
    """
    return {
        "range": {
            "date": {
                "gte": date_range.start.isoformat(),
                "lte": date_range.end.isoformat()
            }
        }
    }


def build_meta_annotation_filter(
    meta_annotations: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Build meta-annotation filter queries.

    Supports both single values (exact match) and list values (OR logic).

    Args:
        meta_annotations: Dict of meta-annotation filters
            Single value: {"Negation": "Affirmed"} → exact match
            List value: {"Temporality": ["Current", "Recent"]} → OR logic

    Returns:
        List of Elasticsearch filter clauses

    Example:
        >>> build_meta_annotation_filter({
        ...     "Negation": "Affirmed",
        ...     "Temporality": ["Current", "Recent"]
        ... })
        [
            {"term": {"meta_annotations.Negation": "Affirmed"}},
            {"terms": {"meta_annotations.Temporality": ["Current", "Recent"]}}
        ]
    """
    if not meta_annotations:
        return []

    filter_clauses: List[Dict[str, Any]] = []

    for key, value in meta_annotations.items():
        field_name = f"meta_annotations.{key}"

        if isinstance(value, list):
            # List value: OR logic (match any value)
            filter_clauses.append({
                "terms": {field_name: value}
            })
        else:
            # Single value: exact match
            filter_clauses.append({
                "term": {field_name: value}
            })

    return filter_clauses


def build_event_type_filter(event_types: List[str]) -> Dict[str, Any]:
    """Build event type filter query.

    Args:
        event_types: List of event types (condition, medication, procedure, symptom, lab_result)

    Returns:
        Elasticsearch terms query

    Example:
        >>> build_event_type_filter(["condition", "medication"])
        {"terms": {"concept_type": ["condition", "medication"]}}
    """
    return {"terms": {"concept_type": event_types}}


def build_specialty_filter(specialty: str) -> Dict[str, Any]:
    """Build clinical specialty filter query.

    Args:
        specialty: Clinical specialty (e.g., "cardiology", "neurology")

    Returns:
        Elasticsearch term query

    Example:
        >>> build_specialty_filter("cardiology")
        {"term": {"specialty": "cardiology"}}
    """
    # Normalize to lowercase for case-insensitive matching
    return {"term": {"specialty": specialty.lower()}}
