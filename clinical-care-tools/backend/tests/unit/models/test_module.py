"""
Module Model Unit Tests.

Tests for the Module database model (Task 4.1).

Module Registry:
- Stores metadata for available modules (patient-search, timeline-view, etc.)
- Enables/disables modules dynamically
- Stores module configuration as JSONB
- Permissions array for access control

Test Coverage:
- Module creation with all fields
- Module enabled/disabled state
- Configuration JSONB storage
- Permissions array
- Seed modules (patient-search, timeline-view, clinical-decision-support)
"""

import pytest
from datetime import datetime
from app.models.module import Module


class TestModuleModel:
    """Test Module model creation and validation."""

    def test_create_module_with_all_fields(self):
        """
        Test: Create module with all fields.

        Expected: Module created with name, display_name, description,
        version, enabled, config (JSONB), icon, permissions.
        """
        module = Module(
            name="patient-search",
            display_name="Patient Search",
            description="Search for patients by clinical concepts",
            version="1.0.0",
            enabled=True,
            config={
                "max_results": 100,
                "default_filters": {
                    "Negation": "Affirmed",
                    "Experiencer": "Patient"
                }
            },
            icon="mdi-account-search",
            permissions=["search_patients", "view_patient_timeline"]
        )

        assert module.name == "patient-search"
        assert module.display_name == "Patient Search"
        assert module.description == "Search for patients by clinical concepts"
        assert module.version == "1.0.0"
        assert module.enabled is True
        assert module.config["max_results"] == 100
        assert module.config["default_filters"]["Negation"] == "Affirmed"
        assert module.icon == "mdi-account-search"
        assert "search_patients" in module.permissions
        assert len(module.permissions) == 2

    def test_create_module_minimal_fields(self):
        """
        Test: Create module with minimal required fields.

        Expected: Module created with only name, display_name.
        Other fields use defaults.
        """
        module = Module(
            name="timeline-view",
            display_name="Patient Timeline"
        )

        assert module.name == "timeline-view"
        assert module.display_name == "Patient Timeline"
        assert module.description is None  # Nullable
        assert module.version == "1.0.0"  # Default
        assert module.enabled is True  # Default enabled
        assert module.config == {}  # Default empty config
        assert module.icon is None  # Nullable
        assert module.permissions == []  # Default empty permissions

    def test_module_enabled_state(self):
        """
        Test: Module enabled/disabled state.

        Expected: Can toggle module enabled flag.
        """
        module = Module(
            name="test-module",
            display_name="Test Module",
            enabled=False
        )

        assert module.enabled is False

        # Enable module
        module.enabled = True
        assert module.enabled is True

        # Disable module
        module.enabled = False
        assert module.enabled is False

    def test_module_config_jsonb(self):
        """
        Test: Module configuration stored as JSONB.

        Expected: Complex nested configuration stored and retrieved correctly.
        """
        config = {
            "features": {
                "meta_annotations": True,
                "fuzzy_matching": True
            },
            "limits": {
                "max_results": 100,
                "max_page_size": 50
            },
            "ui_settings": {
                "theme": "light",
                "language": "en-GB"
            }
        }

        module = Module(
            name="test-module",
            display_name="Test Module",
            config=config
        )

        assert module.config["features"]["meta_annotations"] is True
        assert module.config["limits"]["max_results"] == 100
        assert module.config["ui_settings"]["language"] == "en-GB"

        # Update config
        module.config["limits"]["max_results"] = 200
        assert module.config["limits"]["max_results"] == 200

    def test_module_permissions_array(self):
        """
        Test: Module permissions stored as array.

        Expected: Permissions list can be added, removed, queried.
        """
        module = Module(
            name="test-module",
            display_name="Test Module",
            permissions=["read", "write"]
        )

        assert "read" in module.permissions
        assert "write" in module.permissions
        assert len(module.permissions) == 2

        # Add permission
        module.permissions.append("delete")
        assert "delete" in module.permissions
        assert len(module.permissions) == 3

        # Remove permission
        module.permissions.remove("write")
        assert "write" not in module.permissions
        assert len(module.permissions) == 2

    def test_module_unique_name_constraint(self):
        """
        Test: Module name must be unique.

        Expected: Cannot create two modules with same name (database constraint).
        """
        # NOTE: This test requires database session
        # Will be tested in integration tests
        pass

    def test_module_timestamps(self):
        """
        Test: Module has created_at and updated_at timestamps.

        Expected: Timestamps auto-set on creation and update.
        """
        module = Module(
            name="test-module",
            display_name="Test Module"
        )

        # Timestamps should be set (by database default)
        # In unit test without DB, may be None
        # Integration test will verify timestamps


class TestSeedModules:
    """Test seed modules for core functionality."""

    def test_patient_search_seed_module(self):
        """
        Test: patient-search seed module structure.

        Expected: Module with name, display_name, description, icon, permissions.
        """
        module = Module(
            name="patient-search",
            display_name="Patient Search",
            description="Search for patients by clinical concepts with meta-annotation filtering",
            version="1.0.0",
            enabled=True,
            config={
                "max_results": 100,
                "default_filters": {
                    "Negation": "Affirmed",
                    "Experiencer": "Patient",
                    "Temporality": "Current"
                }
            },
            icon="mdi-account-search",
            permissions=["search_patients", "view_search_results"]
        )

        assert module.name == "patient-search"
        assert module.enabled is True
        assert "search_patients" in module.permissions

    def test_timeline_view_seed_module(self):
        """
        Test: timeline-view seed module structure.

        Expected: Module for patient timeline visualization.
        """
        module = Module(
            name="timeline-view",
            display_name="Patient Timeline",
            description="Visualize patient's clinical history on an interactive timeline",
            version="1.0.0",
            enabled=True,
            config={
                "default_view": "chronological",
                "show_meta_annotations": True
            },
            icon="mdi-timeline",
            permissions=["view_patient_timeline", "view_patient_documents"]
        )

        assert module.name == "timeline-view"
        assert module.config["default_view"] == "chronological"
        assert "view_patient_timeline" in module.permissions

    def test_clinical_decision_support_seed_module(self):
        """
        Test: clinical-decision-support seed module structure.

        Expected: Module for CDS integration.
        """
        module = Module(
            name="clinical-decision-support",
            display_name="Clinical Decision Support",
            description="Integrate with CDS Hooks for clinical alerts and recommendations",
            version="1.0.0",
            enabled=False,  # Disabled by default (Phase 7 feature)
            config={
                "cds_hooks_url": None,
                "enabled_hooks": []
            },
            icon="mdi-lightbulb",
            permissions=["view_cds_alerts", "manage_cds_config"]
        )

        assert module.name == "clinical-decision-support"
        assert module.enabled is False  # Not yet ready
        assert module.config["cds_hooks_url"] is None
