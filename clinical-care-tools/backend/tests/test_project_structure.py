"""
Tests for backend project structure.

Verifies that all required directories and files exist for proper package structure.
"""

import os
from pathlib import Path
import pytest


# Base directory for backend
BACKEND_DIR = Path(__file__).parent.parent


class TestProjectStructure:
    """Test backend project structure."""

    def test_backend_directory_exists(self):
        """Test that backend directory exists."""
        assert BACKEND_DIR.exists()
        assert BACKEND_DIR.is_dir()

    def test_app_directory_exists(self):
        """Test that app directory exists."""
        app_dir = BACKEND_DIR / "app"
        assert app_dir.exists()
        assert app_dir.is_dir()

    def test_required_subdirectories_exist(self):
        """Test that all required subdirectories exist."""
        required_dirs = [
            "api",
            "core",
            "models",
            "schemas",
            "services",
            "db",
            "clients",
        ]

        for dir_name in required_dirs:
            dir_path = BACKEND_DIR / "app" / dir_name
            assert dir_path.exists(), f"Directory {dir_name} does not exist"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"

    def test_init_files_exist(self):
        """Test that __init__.py exists in all packages."""
        package_dirs = [
            "app",
            "app/api",
            "app/api/v1",
            "app/api/v1/endpoints",
            "app/api/v1/routers",
            "app/core",
            "app/models",
            "app/schemas",
            "app/services",
            "app/db",
            "app/clients",
        ]

        for package in package_dirs:
            init_file = BACKEND_DIR / package / "__init__.py"
            assert init_file.exists(), f"__init__.py missing in {package}"
            assert init_file.is_file(), f"__init__.py in {package} is not a file"

    def test_requirements_file_exists(self):
        """Test that requirements.txt exists."""
        requirements = BACKEND_DIR / "requirements.txt"
        assert requirements.exists()
        assert requirements.is_file()

    def test_requirements_content(self):
        """Test that requirements.txt contains essential packages."""
        requirements = BACKEND_DIR / "requirements.txt"
        content = requirements.read_text()

        # Essential packages for FastAPI backend
        essential_packages = [
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "alembic",
            "pydantic",
            "python-jose",
            "passlib",
            "redis",
        ]

        for package in essential_packages:
            assert package in content.lower(), f"{package} not found in requirements.txt"

    def test_main_file_exists(self):
        """Test that main.py entry point exists."""
        main_file = BACKEND_DIR / "app" / "main.py"
        assert main_file.exists()
        assert main_file.is_file()

    def test_core_config_exists(self):
        """Test that core configuration module exists."""
        config_file = BACKEND_DIR / "app" / "core" / "config.py"
        assert config_file.exists()
        assert config_file.is_file()

    def test_core_database_exists(self):
        """Test that database module exists."""
        db_file = BACKEND_DIR / "app" / "core" / "database.py"
        assert db_file.exists()
        assert db_file.is_file()

    def test_python_imports_work(self):
        """Test that Python can import from app package."""
        import sys
        backend_path = str(BACKEND_DIR)
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)

        # Test core imports
        try:
            from app.core import config
            from app.core import database
            from app.core import redis_client
        except ImportError as e:
            pytest.fail(f"Failed to import from app.core: {e}")

    def test_tests_directory_exists(self):
        """Test that tests directory exists."""
        tests_dir = BACKEND_DIR / "tests"
        assert tests_dir.exists()
        assert tests_dir.is_dir()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
