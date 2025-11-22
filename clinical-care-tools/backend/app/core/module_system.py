"""
Module System Core

Provides dynamic module loading, lifecycle management, and dependency resolution
for pluggable modules in the Clinical Care Tools application.
"""

import importlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type

from fastapi import APIRouter, FastAPI
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.module import Module

logger = logging.getLogger(__name__)


class ModuleMetadata:
    """
    Module metadata from module.json manifest file.

    Attributes:
        name: Module name (kebab-case: 'patient-search')
        display_name: Human-readable name
        version: Semantic version
        description: Module description
        dependencies: List of required module names
        permissions: List of permission strings
        routes: List of route definitions
        configuration: Default configuration
        entry_point: Python module entry point (e.g., 'patient_search.main')
    """

    def __init__(self, data: Dict[str, Any]):
        self.name: str = data["name"]
        self.display_name: str = data["display_name"]
        self.version: str = data["version"]
        self.description: str = data.get("description", "")
        self.dependencies: List[str] = data.get("dependencies", [])
        self.permissions: List[str] = data.get("permissions", [])
        self.routes: List[Dict[str, Any]] = data.get("routes", [])
        self.configuration: Dict[str, Any] = data.get("configuration", {})
        self.entry_point: str = data.get("entry_point", "__init__")

    @classmethod
    def from_json_file(cls, path: Path) -> "ModuleMetadata":
        """Load metadata from module.json file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls(data)


class ModuleInstance:
    """
    Runtime instance of a loaded module.

    Attributes:
        metadata: Module metadata
        module: Loaded Python module
        router: FastAPI router instance
        is_enabled: Whether module is enabled
    """

    def __init__(self, metadata: ModuleMetadata, module: Any, router: Optional[APIRouter] = None):
        self.metadata = metadata
        self.module = module
        self.router = router
        self.is_enabled = False

    def enable(self):
        """Enable the module."""
        if hasattr(self.module, "on_enable"):
            self.module.on_enable()
        self.is_enabled = True
        logger.info(f"Module '{self.metadata.name}' enabled")

    def disable(self):
        """Disable the module."""
        if hasattr(self.module, "on_disable"):
            self.module.on_disable()
        self.is_enabled = False
        logger.info(f"Module '{self.metadata.name}' disabled")

    def __repr__(self) -> str:
        status = "enabled" if self.is_enabled else "disabled"
        return f"<ModuleInstance({self.metadata.name}, {status})>"


class ModuleSystem:
    """
    Core module system for dynamic module loading and lifecycle management.

    Features:
        - Dynamic module discovery and loading
        - Dependency resolution
        - Lifecycle management (enable/disable)
        - Route registration
        - Configuration management
    """

    def __init__(self, app: FastAPI, modules_path: Path = None):
        """
        Initialize module system.

        Args:
            app: FastAPI application instance
            modules_path: Path to modules directory (default: app/modules)
        """
        self.app = app
        self.modules_path = modules_path or Path(__file__).parent.parent / "modules"
        self.loaded_modules: Dict[str, ModuleInstance] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}

        # Ensure modules directory exists
        self.modules_path.mkdir(exist_ok=True)

    def discover_modules(self) -> List[ModuleMetadata]:
        """
        Discover available modules in the modules directory.

        Returns:
            List of module metadata
        """
        discovered = []

        if not self.modules_path.exists():
            logger.warning(f"Modules directory not found: {self.modules_path}")
            return discovered

        for module_dir in self.modules_path.iterdir():
            if not module_dir.is_dir():
                continue

            manifest_path = module_dir / "module.json"
            if not manifest_path.exists():
                logger.debug(f"No module.json found in {module_dir}")
                continue

            try:
                metadata = ModuleMetadata.from_json_file(manifest_path)
                discovered.append(metadata)
                logger.info(f"Discovered module: {metadata.name} v{metadata.version}")
            except Exception as e:
                logger.error(f"Error loading module manifest from {manifest_path}: {e}")

        return discovered

    def load_module(self, metadata: ModuleMetadata) -> ModuleInstance:
        """
        Load a module and its dependencies.

        Args:
            metadata: Module metadata

        Returns:
            Loaded module instance

        Raises:
            ImportError: If module cannot be imported
            RuntimeError: If circular dependency detected
        """
        # Check if already loaded
        if metadata.name in self.loaded_modules:
            return self.loaded_modules[metadata.name]

        # Check dependencies
        for dep in metadata.dependencies:
            if dep not in self.loaded_modules:
                raise RuntimeError(f"Module '{metadata.name}' requires '{dep}' which is not loaded")

        # Add module path to sys.path
        module_path = self.modules_path / metadata.name.replace("-", "_")
        if str(module_path.parent) not in sys.path:
            sys.path.insert(0, str(module_path.parent))

        # Import the module
        module_name = f"{metadata.name.replace('-', '_')}.{metadata.entry_point}"
        try:
            module = importlib.import_module(module_name)
            logger.info(f"Loaded module: {metadata.name}")
        except ImportError as e:
            logger.error(f"Failed to import module '{metadata.name}': {e}")
            raise

        # Create module instance
        instance = ModuleInstance(metadata, module)

        # Load router if available
        if hasattr(module, "create_router"):
            instance.router = module.create_router()
            logger.info(f"Created router for module: {metadata.name}")

        # Store the instance
        self.loaded_modules[metadata.name] = instance

        return instance

    def register_module_routes(self, module: ModuleInstance):
        """
        Register module routes with the FastAPI application.

        Args:
            module: Module instance
        """
        if not module.router:
            return

        # Add prefix for module routes
        prefix = f"/api/v1/modules/{module.metadata.name}"
        self.app.include_router(
            module.router,
            prefix=prefix,
            tags=[module.metadata.display_name]
        )
        logger.info(f"Registered routes for module '{module.metadata.name}' at {prefix}")

    def enable_module(self, name: str, db: Session) -> bool:
        """
        Enable a module.

        Args:
            name: Module name
            db: Database session

        Returns:
            True if successful
        """
        if name not in self.loaded_modules:
            logger.error(f"Module '{name}' is not loaded")
            return False

        module = self.loaded_modules[name]

        # Update database
        db_module = db.query(Module).filter(Module.name == name).first()
        if db_module:
            db_module.is_enabled = True
            db.commit()

        # Enable the module
        module.enable()

        # Register routes if not already registered
        if module.router:
            self.register_module_routes(module)

        return True

    def disable_module(self, name: str, db: Session) -> bool:
        """
        Disable a module.

        Args:
            name: Module name
            db: Database session

        Returns:
            True if successful
        """
        if name not in self.loaded_modules:
            logger.error(f"Module '{name}' is not loaded")
            return False

        module = self.loaded_modules[name]

        # Check if other modules depend on this one
        for other_name, other_module in self.loaded_modules.items():
            if other_name != name and name in other_module.metadata.dependencies:
                if other_module.is_enabled:
                    logger.error(f"Cannot disable '{name}' - required by enabled module '{other_name}'")
                    return False

        # Update database
        db_module = db.query(Module).filter(Module.name == name).first()
        if db_module:
            db_module.is_enabled = False
            db.commit()

        # Disable the module
        module.disable()

        # NOTE: Unregister routes (requires FastAPI route management)

        return True

    def initialize_all(self, db: Session):
        """
        Initialize all modules from database and filesystem.

        Args:
            db: Database session
        """
        # Discover available modules
        discovered = self.discover_modules()

        # Build dependency graph
        for metadata in discovered:
            self._dependency_graph[metadata.name] = set(metadata.dependencies)

        # Topological sort for dependency order
        load_order = self._topological_sort()

        # Load modules in dependency order
        for name in load_order:
            metadata = next((m for m in discovered if m.name == name), None)
            if not metadata:
                continue

            try:
                # Load the module
                module = self.load_module(metadata)

                # Check database for enable status
                db_module = db.query(Module).filter(Module.name == name).first()
                if db_module and db_module.is_enabled:
                    module.enable()
                    if module.router:
                        self.register_module_routes(module)

            except Exception as e:
                logger.error(f"Failed to initialize module '{name}': {e}")

        logger.info(f"Module system initialized with {len(self.loaded_modules)} modules")

    def _topological_sort(self) -> List[str]:
        """
        Perform topological sort on dependency graph.

        Returns:
            Sorted list of module names

        Raises:
            RuntimeError: If circular dependency detected
        """
        visited = set()
        stack = []
        rec_stack = set()

        def visit(node: str):
            if node in rec_stack:
                raise RuntimeError(f"Circular dependency detected involving '{node}'")

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for dep in self._dependency_graph.get(node, set()):
                visit(dep)

            rec_stack.remove(node)
            stack.append(node)

        for node in self._dependency_graph:
            if node not in visited:
                visit(node)

        return list(reversed(stack))

    def get_module_status(self) -> Dict[str, Any]:
        """
        Get status of all loaded modules.

        Returns:
            Dictionary of module status information
        """
        status = {}
        for name, module in self.loaded_modules.items():
            status[name] = {
                "display_name": module.metadata.display_name,
                "version": module.metadata.version,
                "is_enabled": module.is_enabled,
                "dependencies": module.metadata.dependencies,
                "has_router": module.router is not None
            }
        return status


# Global module system instance
_module_system: Optional[ModuleSystem] = None


def get_module_system() -> ModuleSystem:
    """Get the global module system instance."""
    if _module_system is None:
        raise RuntimeError("Module system not initialized")
    return _module_system


def initialize_module_system(app: FastAPI, db: Session = None):
    """
    Initialize the global module system.

    Args:
        app: FastAPI application
        db: Database session (optional)
    """
    global _module_system
    _module_system = ModuleSystem(app)

    if db:
        _module_system.initialize_all(db)

    return _module_system