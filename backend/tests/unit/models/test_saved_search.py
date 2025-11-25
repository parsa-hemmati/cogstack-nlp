"""
Unit Tests for SavedSearch Model

Tests SQLAlchemy model for saved_searches table.
Follows TDD approach: Write tests first, then implement.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError


@pytest.mark.asyncio
async def test_create_saved_search_with_valid_data():
    """Test creating SavedSearch with valid data"""
    from app.models.saved_search import SavedSearch

    # Arrange
    search = SavedSearch(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="COVID-19 Patients",
        description="Patients with COVID-19 diagnosis",
        query="COVID-19",
        filters={"Negation": "Affirmed", "Experiencer": "Patient"},
        is_shared=False,
        execution_count=0
    )

    # Assert
    assert search.id is not None
    assert search.user_id is not None
    assert search.name == "COVID-19 Patients"
    assert search.description == "Patients with COVID-19 diagnosis"
    assert search.query == "COVID-19"
    assert search.filters == {"Negation": "Affirmed", "Experiencer": "Patient"}
    assert search.is_shared is False
    assert search.execution_count == 0
    assert isinstance(search.created_at, datetime)
    assert isinstance(search.updated_at, datetime)


@pytest.mark.asyncio
async def test_saved_search_default_values():
    """Test SavedSearch model default values"""
    from app.models.saved_search import SavedSearch

    # Arrange
    search = SavedSearch(
        user_id=uuid.uuid4(),
        name="Test Search",
        query="test query"
    )

    # Assert
    assert search.id is not None  # UUID generated
    assert search.description is None  # Optional field
    assert search.filters is None  # Optional field
    assert search.is_shared is False  # Default value
    assert search.execution_count == 0  # Default value
    assert search.created_at is not None
    assert search.updated_at is not None


@pytest.mark.asyncio
async def test_saved_search_repr():
    """Test SavedSearch string representation"""
    from app.models.saved_search import SavedSearch

    # Arrange
    user_id = uuid.uuid4()
    search = SavedSearch(
        user_id=user_id,
        name="My Search",
        query="diabetes"
    )

    # Act
    repr_str = repr(search)

    # Assert
    assert "SavedSearch" in repr_str
    assert "My Search" in repr_str
    assert str(user_id) in repr_str


@pytest.mark.asyncio
async def test_saved_search_to_dict():
    """Test SavedSearch to_dict serialization"""
    from app.models.saved_search import SavedSearch

    # Arrange
    search_id = uuid.uuid4()
    user_id = uuid.uuid4()
    search = SavedSearch(
        id=search_id,
        user_id=user_id,
        name="Diabetes Search",
        description="Type 2 diabetes patients",
        query="type 2 diabetes",
        filters={"Negation": "Affirmed"},
        is_shared=True,
        execution_count=5
    )

    # Act
    result = search.to_dict()

    # Assert
    assert result["id"] == str(search_id)
    assert result["user_id"] == str(user_id)
    assert result["name"] == "Diabetes Search"
    assert result["description"] == "Type 2 diabetes patients"
    assert result["query"] == "type 2 diabetes"
    assert result["filters"] == {"Negation": "Affirmed"}
    assert result["is_shared"] is True
    assert result["execution_count"] == 5
    assert "created_at" in result
    assert "updated_at" in result


@pytest.mark.asyncio
async def test_saved_search_increment_execution_count():
    """Test incrementing execution count"""
    from app.models.saved_search import SavedSearch

    # Arrange
    search = SavedSearch(
        user_id=uuid.uuid4(),
        name="Test",
        query="test",
        execution_count=0
    )

    # Act
    search.execution_count += 1
    search.execution_count += 1

    # Assert
    assert search.execution_count == 2


@pytest.mark.asyncio
async def test_saved_search_filters_jsonb():
    """Test filters field supports complex JSONB data"""
    from app.models.saved_search import SavedSearch

    # Arrange
    complex_filters = {
        "Negation": "Affirmed",
        "Temporality": "Current",
        "Experiencer": "Patient",
        "Certainty": "Certain",
        "date_range": {
            "start": "2023-01-01",
            "end": "2023-12-31"
        },
        "departments": ["Cardiology", "Endocrinology"]
    }

    search = SavedSearch(
        user_id=uuid.uuid4(),
        name="Complex Filter Search",
        query="test",
        filters=complex_filters
    )

    # Assert
    assert search.filters == complex_filters
    assert search.filters["Negation"] == "Affirmed"
    assert search.filters["date_range"]["start"] == "2023-01-01"
    assert "Cardiology" in search.filters["departments"]
