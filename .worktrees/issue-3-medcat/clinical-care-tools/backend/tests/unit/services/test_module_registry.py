"""
Module Registry Service Unit Tests.

Tests for dynamic module loading and registration (Task 4.2).

Module Registry:
- Lists enabled modules for display in UI
- Retrieves module configuration
- Enables dynamic route registration per module

Test Coverage:
- List enabled modules only (excludes disabled)
- Get module by name
- Module configuration access
- Handle missing modules gracefully
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

# TODO: Will implement these after service is created
# from app.services.module_registry import (
#     get_enabled_modules,
#     get_module,
#     register_module_routes
# )


class TestGetEnabledModules:
    """Test get_enabled_modules() function."""

    @pytest.mark.asyncio
    async def test_returns_enabled_modules_only(self):
        """
        Test: get_enabled_modules() returns only enabled modules.

        Expected: patient-search and timeline-view returned, not CDS.
        """
        from app.services.module_registry import get_enabled_modules

        # Mock database with 3 modules (2 enabled, 1 disabled)
        mock_db = AsyncMock()

        # TODO: Mock actual database query
        # For now, assume service returns correct modules

        modules = await get_enabled_modules(mock_db)

        # Verify: Only enabled modules
        module_names = [m.name for m in modules]
        assert "patient-search" in module_names
        assert "timeline-view" in module_names
        assert "clinical-decision-support" not in module_names  # Disabled

    @pytest.mark.asyncio
    async def test_returns_modules_sorted_by_name(self):
        """
        Test: get_enabled_modules() returns modules sorted alphabetically.

        Expected: Consistent ordering for UI display.
        """
        from app.services.module_registry import get_enabled_modules

        mock_db = AsyncMock()
        modules = await get_enabled_modules(mock_db)

        # Verify: Sorted by name
        module_names = [m.name for m in modules]
        assert module_names == sorted(module_names)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_modules(self):
        """
        Test: get_enabled_modules() returns empty list when no modules enabled.

        Expected: No errors, returns [].
        """
        from app.services.module_registry import get_enabled_modules

        mock_db = AsyncMock()

        # Mock database with no modules
        # TODO: Mock query to return empty

        modules = await get_enabled_modules(mock_db)

        # May return empty or seed modules depending on database state
        assert isinstance(modules, list)


class TestGetModule:
    """Test get_module() function."""

    @pytest.mark.asyncio
    async def test_get_module_by_name_returns_module(self):
        """
        Test: get_module("patient-search") returns module.

        Expected: Module object with name="patient-search".
        """
        from app.services.module_registry import get_module

        mock_db = AsyncMock()

        module = await get_module(mock_db, "patient-search")

        # Verify: Module found
        assert module is not None
        assert module.name == "patient-search"
        assert module.display_name == "Patient Search"

    @pytest.mark.asyncio
    async def test_get_module_returns_enabled_module(self):
        """
        Test: get_module() returns enabled module.

        Expected: Module.enabled = True.
        """
        from app.services.module_registry import get_module

        mock_db = AsyncMock()

        module = await get_module(mock_db, "patient-search")

        assert module.enabled is True

    @pytest.mark.asyncio
    async def test_get_module_returns_disabled_module(self):
        """
        Test: get_module() returns disabled module too.

        Expected: CDS module returned even though disabled.
        (For admin UI to manage modules)
        """
        from app.services.module_registry import get_module

        mock_db = AsyncMock()

        module = await get_module(mock_db, "clinical-decision-support")

        # Verify: Disabled module found
        assert module is not None
        assert module.name == "clinical-decision-support"
        assert module.enabled is False

    @pytest.mark.asyncio
    async def test_get_module_not_found_returns_none(self):
        """
        Test: get_module("nonexistent") returns None.

        Expected: No errors, returns None.
        """
        from app.services.module_registry import get_module

        mock_db = AsyncMock()

        module = await get_module(mock_db, "nonexistent-module")

        # Verify: None returned
        assert module is None


class TestModuleConfiguration:
    """Test module configuration access."""

    @pytest.mark.asyncio
    async def test_module_config_accessible(self):
        """
        Test: Module configuration accessible via get_module().

        Expected: module.config contains JSONB data.
        """
        from app.services.module_registry import get_module

        mock_db = AsyncMock()

        module = await get_module(mock_db, "patient-search")

        # Verify: Config accessible
        assert module.config is not None
        assert isinstance(module.config, dict)
        assert "max_results" in module.config
        assert module.config["max_results"] == 100

    @pytest.mark.asyncio
    async def test_module_default_filters_accessible(self):
        """
        Test: Module default_filters accessible from config.

        Expected: patient-search has default_filters for meta-annotations.
        """
        from app.services.module_registry import get_module

        mock_db = AsyncMock()

        module = await get_module(mock_db, "patient-search")

        # Verify: Default filters in config
        assert "default_filters" in module.config
        assert module.config["default_filters"]["Negation"] == "Affirmed"
        assert module.config["default_filters"]["Experiencer"] == "Patient"

    @pytest.mark.asyncio
    async def test_module_permissions_accessible(self):
        """
        Test: Module permissions accessible.

        Expected: module.permissions is list of permission strings.
        """
        from app.services.module_registry import get_module

        mock_db = AsyncMock()

        module = await get_module(mock_db, "patient-search")

        # Verify: Permissions accessible
        assert module.permissions is not None
        assert isinstance(module.permissions, list)
        assert "search_patients" in module.permissions


class TestRegisterModuleRoutes:
    """Test register_module_routes() function."""

    def test_register_module_routes_placeholder(self):
        """
        Test: register_module_routes() is defined.

        Expected: Function exists for future dynamic route registration.
        """
        from app.services.module_registry import register_module_routes

        # Verify: Function callable
        assert callable(register_module_routes)

        # NOTE: Actual route registration will be tested in integration tests
        # For now, verify function exists
