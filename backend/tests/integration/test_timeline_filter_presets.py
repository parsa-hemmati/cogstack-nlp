"""Integration tests for timeline filter preset API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.timeline_filter_preset import TimelineFilterPreset


@pytest.mark.asyncio
async def test_create_filter_preset(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict
):
    """Test creating a new filter preset."""
    preset_data = {
        "name": "Diabetes Management",
        "filters": {
            "concept_cuis": ["C0011849", "C0011860"],
            "meta_annotations": {
                "Negation": "Affirmed",
                "Experiencer": "Patient",
                "Temporality": ["Current", "Recent"]
            },
            "document_types": ["clinical_note", "lab_result"]
        },
        "is_default": True
    }

    response = await async_client.post(
        "/api/v1/timeline/filters",
        json=preset_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Diabetes Management"
    assert data["user_id"] == str(test_user.id)
    assert data["is_default"] is True
    assert "id" in data
    assert "created_at" in data
    assert data["filters"]["concept_cuis"] == ["C0011849", "C0011860"]


@pytest.mark.asyncio
async def test_create_preset_duplicate_name(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test creating preset with duplicate name fails."""
    # Create first preset
    preset1 = TimelineFilterPreset(
        user_id=test_user.id,
        name="Diabetes Management",
        filters={"concept_cuis": ["C0011849"]},
        is_default=False
    )
    db_session.add(preset1)
    await db_session.commit()

    # Try to create second preset with same name
    preset_data = {
        "name": "Diabetes Management",
        "filters": {"concept_cuis": ["C0020538"]},
        "is_default": False
    }

    response = await async_client.post(
        "/api/v1/timeline/filters",
        json=preset_data,
        headers=auth_headers
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_filter_presets(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test listing user's filter presets."""
    # Create 3 presets
    presets = [
        TimelineFilterPreset(
            user_id=test_user.id,
            name="Preset 1",
            filters={"concept_cuis": ["C0011849"]},
            is_default=True
        ),
        TimelineFilterPreset(
            user_id=test_user.id,
            name="Preset 2",
            filters={"concept_cuis": ["C0020538"]},
            is_default=False
        ),
        TimelineFilterPreset(
            user_id=test_user.id,
            name="Preset 3",
            filters={"concept_cuis": ["C0004238"]},
            is_default=False
        )
    ]
    for preset in presets:
        db_session.add(preset)
    await db_session.commit()

    response = await async_client.get(
        "/api/v1/timeline/filters",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["presets"]) == 3

    # Default preset should be first
    assert data["presets"][0]["name"] == "Preset 1"
    assert data["presets"][0]["is_default"] is True


@pytest.mark.asyncio
async def test_list_presets_only_own(
    async_client: AsyncClient,
    test_user: User,
    test_user_2: User,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test user can only list their own presets."""
    # Create preset for test_user
    preset1 = TimelineFilterPreset(
        user_id=test_user.id,
        name="User 1 Preset",
        filters={"concept_cuis": ["C0011849"]},
        is_default=False
    )
    db_session.add(preset1)

    # Create preset for test_user_2
    preset2 = TimelineFilterPreset(
        user_id=test_user_2.id,
        name="User 2 Preset",
        filters={"concept_cuis": ["C0020538"]},
        is_default=False
    )
    db_session.add(preset2)
    await db_session.commit()

    # Query as test_user (auth_headers)
    response = await async_client.get(
        "/api/v1/timeline/filters",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["presets"][0]["name"] == "User 1 Preset"


@pytest.mark.asyncio
async def test_get_filter_preset_by_id(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test getting a specific filter preset by ID."""
    preset = TimelineFilterPreset(
        user_id=test_user.id,
        name="My Preset",
        filters={"concept_cuis": ["C0011849"]},
        is_default=False
    )
    db_session.add(preset)
    await db_session.commit()
    await db_session.refresh(preset)

    response = await async_client.get(
        f"/api/v1/timeline/filters/{preset.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(preset.id)
    assert data["name"] == "My Preset"


@pytest.mark.asyncio
async def test_get_preset_not_found(
    async_client: AsyncClient,
    auth_headers: dict
):
    """Test getting non-existent preset returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await async_client.get(
        f"/api/v1/timeline/filters/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_filter_preset(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test updating a filter preset."""
    preset = TimelineFilterPreset(
        user_id=test_user.id,
        name="Old Name",
        filters={"concept_cuis": ["C0011849"]},
        is_default=False
    )
    db_session.add(preset)
    await db_session.commit()
    await db_session.refresh(preset)

    update_data = {
        "name": "New Name",
        "filters": {"concept_cuis": ["C0020538", "C0011860"]},
        "is_default": True
    }

    response = await async_client.put(
        f"/api/v1/timeline/filters/{preset.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["filters"]["concept_cuis"] == ["C0020538", "C0011860"]
    assert data["is_default"] is True


@pytest.mark.asyncio
async def test_update_preset_partial(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test partial update of filter preset."""
    preset = TimelineFilterPreset(
        user_id=test_user.id,
        name="Original Name",
        filters={"concept_cuis": ["C0011849"]},
        is_default=False
    )
    db_session.add(preset)
    await db_session.commit()
    await db_session.refresh(preset)

    # Only update name
    update_data = {"name": "Updated Name"}

    response = await async_client.put(
        f"/api/v1/timeline/filters/{preset.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["filters"]["concept_cuis"] == ["C0011849"]  # Unchanged
    assert data["is_default"] is False  # Unchanged


@pytest.mark.asyncio
async def test_update_preset_sets_default_unsets_others(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test setting preset as default un-sets other defaults."""
    # Create 2 presets, first one is default
    preset1 = TimelineFilterPreset(
        user_id=test_user.id,
        name="Preset 1",
        filters={"concept_cuis": ["C0011849"]},
        is_default=True
    )
    preset2 = TimelineFilterPreset(
        user_id=test_user.id,
        name="Preset 2",
        filters={"concept_cuis": ["C0020538"]},
        is_default=False
    )
    db_session.add(preset1)
    db_session.add(preset2)
    await db_session.commit()
    await db_session.refresh(preset1)
    await db_session.refresh(preset2)

    # Set preset2 as default
    update_data = {"is_default": True}

    response = await async_client.put(
        f"/api/v1/timeline/filters/{preset2.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["is_default"] is True

    # Verify preset1 is no longer default
    await db_session.refresh(preset1)
    assert preset1.is_default is False


@pytest.mark.asyncio
async def test_delete_filter_preset(
    async_client: AsyncClient,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test deleting a filter preset."""
    preset = TimelineFilterPreset(
        user_id=test_user.id,
        name="To Delete",
        filters={"concept_cuis": ["C0011849"]},
        is_default=False
    )
    db_session.add(preset)
    await db_session.commit()
    await db_session.refresh(preset)

    preset_id = preset.id

    response = await async_client.delete(
        f"/api/v1/timeline/filters/{preset_id}",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify preset is deleted
    response = await async_client.get(
        f"/api/v1/timeline/filters/{preset_id}",
        headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_preset_not_found(
    async_client: AsyncClient,
    auth_headers: dict
):
    """Test deleting non-existent preset returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await async_client.delete(
        f"/api/v1/timeline/filters/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_preset_requires_auth(async_client: AsyncClient):
    """Test creating preset without authentication fails."""
    preset_data = {
        "name": "Test",
        "filters": {"concept_cuis": []},
        "is_default": False
    }

    response = await async_client.post(
        "/api/v1/timeline/filters",
        json=preset_data
    )

    assert response.status_code == 401
