"""
Tests for Module System

Tests the core module system functionality including:
- Module discovery and loading
- Dependency resolution
- Lifecycle management
- Route registration
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.core.module_system import (
    ModuleMetadata,
    ModuleInstance,
    ModuleSystem,
    initialize_module_system,
    get_module_system,
)
from app.models.module import Module


class TestModuleMetadata:
    """Test ModuleMetadata class."""

    def test_init_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "name": "test-module",
            "display_name": "Test Module",
            "version": "1.0.0",
            "description": "Test module description",
            "dependencies": ["dep1", "dep2"],
            "permissions": ["test.read", "test.write"],
            "routes": [{"path": "/test", "methods": ["GET"]}],
            "configuration": {"key": "value"},
            "entry_point": "main",
        }

        metadata = ModuleMetadata(data)

        assert metadata.name == "test-module"
        assert metadata.display_name == "Test Module"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test module description"
        assert metadata.dependencies == ["dep1", "dep2"]
        assert metadata.permissions == ["test.read", "test.write"]
        assert len(metadata.routes) == 1
        assert metadata.configuration == {"key": "value"}
        assert metadata.entry_point == "main"

    def test_from_json_file(self, tmp_path):
        """Test loading metadata from JSON file."""
        module_json = tmp_path / "module.json"
        data = {
            "name": "test-module",
            "display_name": "Test Module",
            "version": "1.0.0",
        }
        module_json.write_text(json.dumps(data))

        metadata = ModuleMetadata.from_json_file(module_json)

        assert metadata.name == "test-module"
        assert metadata.display_name == "Test Module"
        assert metadata.version == "1.0.0"

    def test_defaults(self):
        """Test default values for optional fields."""
        data = {
            "name": "test-module",
            "display_name": "Test Module",
            "version": "1.0.0",
        }

        metadata = ModuleMetadata(data)

        assert metadata.description == ""
        assert metadata.dependencies == []
        assert metadata.permissions == []
        assert metadata.routes == []
        assert metadata.configuration == {}
        assert metadata.entry_point == "__init__"


class TestModuleInstance:
    """Test ModuleInstance class."""

    def test_init(self):
        """Test module instance initialization."""
        metadata = ModuleMetadata({
            "name": "test-module",
            "display_name": "Test Module",
            "version": "1.0.0",
        })
        module = Mock()
        router = Mock()

        instance = ModuleInstance(metadata, module, router)

        assert instance.metadata == metadata
        assert instance.module == module
        assert instance.router == router
        assert instance.is_enabled == False

    def test_enable(self):
        """Test enabling a module."""
        metadata = ModuleMetadata({
            "name": "test-module",
            "display_name": "Test Module",
            "version": "1.0.0",
        })
        module = Mock()
        module.on_enable = Mock()

        instance = ModuleInstance(metadata, module)
        instance.enable()

        assert instance.is_enabled == True
        module.on_enable.assert_called_once()

    def test_enable_without_hook(self):
        """Test enabling a module without on_enable hook."""
        metadata = ModuleMetadata({
            "name": "test-module",
            "display_name": "Test Module",
            "version": "1.0.0",
        })
        module = Mock(spec=[])  # No on_enable method

        instance = ModuleInstance(metadata, module)
        instance.enable()  # Should not raise

        assert instance.is_enabled == True

    def test_disable(self):
        """Test disabling a module."""
        metadata = ModuleMetadata({
            "name": "test-module",
            "display_name": "Test Module",
            "version": "1.0.0",
        })
        module = Mock()
        module.on_disable = Mock()

        instance = ModuleInstance(metadata, module)
        instance.is_enabled = True
        instance.disable()

        assert instance.is_enabled == False
        module.on_disable.assert_called_once()


class TestModuleSystem:
    """Test ModuleSystem class."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app for testing."""
        return FastAPI()

    @pytest.fixture
    def module_system(self, app, tmp_path):
        """Create module system for testing."""
        modules_path = tmp_path / "modules"
        modules_path.mkdir()
        return ModuleSystem(app, modules_path)

    def test_init(self, app, tmp_path):
        """Test module system initialization."""
        modules_path = tmp_path / "modules"
        system = ModuleSystem(app, modules_path)

        assert system.app == app
        assert system.modules_path == modules_path
        assert system.loaded_modules == {}
        assert modules_path.exists()

    def test_discover_modules(self, module_system, tmp_path):
        """Test discovering modules."""
        # Create test module directories
        module1_dir = module_system.modules_path / "module1"
        module1_dir.mkdir()
        module1_json = module1_dir / "module.json"
        module1_json.write_text(json.dumps({
            "name": "module1",
            "display_name": "Module 1",
            "version": "1.0.0",
        }))

        module2_dir = module_system.modules_path / "module2"
        module2_dir.mkdir()
        module2_json = module2_dir / "module.json"
        module2_json.write_text(json.dumps({
            "name": "module2",
            "display_name": "Module 2",
            "version": "2.0.0",
        }))

        # Directory without module.json (should be skipped)
        invalid_dir = module_system.modules_path / "invalid"
        invalid_dir.mkdir()

        # File instead of directory (should be skipped)
        (module_system.modules_path / "file.txt").touch()

        discovered = module_system.discover_modules()

        assert len(discovered) == 2
        assert any(m.name == "module1" for m in discovered)
        assert any(m.name == "module2" for m in discovered)

    def test_discover_modules_empty_directory(self, module_system):
        """Test discovering modules in empty directory."""
        discovered = module_system.discover_modules()
        assert discovered == []

    @patch("app.core.module_system.importlib.import_module")
    def test_load_module(self, mock_import, module_system):
        """Test loading a module."""
        metadata = ModuleMetadata({
            "name": "test-module",
            "display_name": "Test Module",
            "version": "1.0.0",
            "entry_point": "__init__",
        })

        mock_module = Mock()
        mock_module.create_router = Mock(return_value=Mock())
        mock_import.return_value = mock_module

        instance = module_system.load_module(metadata)

        assert instance.metadata == metadata
        assert instance.module == mock_module
        assert instance.router is not None
        assert "test-module" in module_system.loaded_modules
        mock_import.assert_called_once_with("test_module.__init__")

    def test_load_module_already_loaded(self, module_system):
        """Test loading an already loaded module."""
        metadata = ModuleMetadata({
            "name": "test-module",
            "display_name": "Test Module",
            "version": "1.0.0",
        })

        instance = ModuleInstance(metadata, Mock())
        module_system.loaded_modules["test-module"] = instance

        result = module_system.load_module(metadata)

        assert result == instance

    def test_load_module_missing_dependency(self, module_system):
        """Test loading module with missing dependency."""
        metadata = ModuleMetadata({
            "name": "test-module",
            "display_name": "Test Module",
            "version": "1.0.0",
            "dependencies": ["missing-dep"],
        })

        with pytest.raises(RuntimeError) as exc_info:
            module_system.load_module(metadata)

        assert "requires 'missing-dep'" in str(exc_info.value)

    def test_register_module_routes(self, module_system, app):
        """Test registering module routes."""
        metadata = ModuleMetadata({
            "name": "test-module",
            "display_name": "Test Module",
            "version": "1.0.0",
        })

        router = Mock()
        instance = ModuleInstance(metadata, Mock(), router)

        with patch.object(app, "include_router") as mock_include:
            module_system.register_module_routes(instance)

            mock_include.assert_called_once_with(
                router,
                prefix="/api/v1/modules/test-module",
                tags=["Test Module"]
            )

    def test_enable_module(self, module_system):
        """Test enabling a module."""
        metadata = ModuleMetadata({
            "name": "test-module",
            "display_name": "Test Module",
            "version": "1.0.0",
        })

        instance = ModuleInstance(metadata, Mock())
        module_system.loaded_modules["test-module"] = instance

        db = Mock(spec=Session)
        db_module = Mock(spec=Module)
        db.query().filter().first.return_value = db_module

        result = module_system.enable_module("test-module", db)

        assert result == True
        assert instance.is_enabled == True
        assert db_module.is_enabled == True
        db.commit.assert_called_once()

    def test_enable_module_not_loaded(self, module_system):
        """Test enabling a module that's not loaded."""
        db = Mock(spec=Session)
        result = module_system.enable_module("unknown-module", db)
        assert result == False

    def test_disable_module(self, module_system):
        """Test disabling a module."""
        metadata = ModuleMetadata({
            "name": "test-module",
            "display_name": "Test Module",
            "version": "1.0.0",
        })

        instance = ModuleInstance(metadata, Mock())
        instance.is_enabled = True
        module_system.loaded_modules["test-module"] = instance

        db = Mock(spec=Session)
        db_module = Mock(spec=Module)
        db.query().filter().first.return_value = db_module

        result = module_system.disable_module("test-module", db)

        assert result == True
        assert instance.is_enabled == False
        assert db_module.is_enabled == False
        db.commit.assert_called_once()

    def test_disable_module_with_dependent(self, module_system):
        """Test disabling a module that has dependents."""
        # Module 1 (dependency)
        metadata1 = ModuleMetadata({
            "name": "module1",
            "display_name": "Module 1",
            "version": "1.0.0",
        })
        instance1 = ModuleInstance(metadata1, Mock())
        instance1.is_enabled = True
        module_system.loaded_modules["module1"] = instance1

        # Module 2 (depends on module1)
        metadata2 = ModuleMetadata({
            "name": "module2",
            "display_name": "Module 2",
            "version": "1.0.0",
            "dependencies": ["module1"],
        })
        instance2 = ModuleInstance(metadata2, Mock())
        instance2.is_enabled = True
        module_system.loaded_modules["module2"] = instance2

        db = Mock(spec=Session)
        result = module_system.disable_module("module1", db)

        assert result == False
        assert instance1.is_enabled == True  # Should remain enabled

    def test_topological_sort(self, module_system):
        """Test topological sorting of dependencies."""
        # Create dependency graph: A -> B -> C, D -> B
        module_system._dependency_graph = {
            "A": {"B"},
            "B": {"C"},
            "C": set(),
            "D": {"B"},
        }

        sorted_modules = module_system._topological_sort()

        # C should come before B, B before A and D
        assert sorted_modules.index("C") < sorted_modules.index("B")
        assert sorted_modules.index("B") < sorted_modules.index("A")
        assert sorted_modules.index("B") < sorted_modules.index("D")

    def test_topological_sort_circular_dependency(self, module_system):
        """Test topological sort with circular dependency."""
        # Create circular dependency: A -> B -> C -> A
        module_system._dependency_graph = {
            "A": {"B"},
            "B": {"C"},
            "C": {"A"},
        }

        with pytest.raises(RuntimeError) as exc_info:
            module_system._topological_sort()

        assert "Circular dependency" in str(exc_info.value)

    def test_get_module_status(self, module_system):
        """Test getting module status."""
        metadata = ModuleMetadata({
            "name": "test-module",
            "display_name": "Test Module",
            "version": "1.0.0",
            "dependencies": ["dep1"],
        })

        instance = ModuleInstance(metadata, Mock(), Mock())
        instance.is_enabled = True
        module_system.loaded_modules["test-module"] = instance

        status = module_system.get_module_status()

        assert "test-module" in status
        assert status["test-module"]["display_name"] == "Test Module"
        assert status["test-module"]["version"] == "1.0.0"
        assert status["test-module"]["is_enabled"] == True
        assert status["test-module"]["dependencies"] == ["dep1"]
        assert status["test-module"]["has_router"] == True


class TestModuleSystemGlobal:
    """Test global module system functions."""

    def test_get_module_system_not_initialized(self):
        """Test getting module system when not initialized."""
        import app.core.module_system as ms
        ms._module_system = None

        with pytest.raises(RuntimeError) as exc_info:
            get_module_system()

        assert "not initialized" in str(exc_info.value)

    def test_initialize_module_system(self):
        """Test initializing global module system."""
        app = FastAPI()
        db = Mock(spec=Session)

        with patch("app.core.module_system.ModuleSystem") as MockModuleSystem:
            mock_system = Mock()
            MockModuleSystem.return_value = mock_system

            result = initialize_module_system(app, db)

            assert result == mock_system
            MockModuleSystem.assert_called_once_with(app)
            mock_system.initialize_all.assert_called_once_with(db)