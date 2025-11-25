"""
Test Project Structure
Tests that all required directories and files exist for the backend project.
"""
import os
from pathlib import Path

import pytest


# Base directory for the backend project
BACKEND_DIR = Path(__file__).parent.parent
APP_DIR = BACKEND_DIR / "app"


class TestProjectStructure:
    """Test that the backend project structure is correct."""

    def test_backend_directory_exists(self):
        """Test that backend directory exists."""
        assert BACKEND_DIR.exists(), "backend/ directory should exist"
        assert BACKEND_DIR.is_dir(), "backend/ should be a directory"

    def test_app_directory_exists(self):
        """Test that app directory exists."""
        assert APP_DIR.exists(), "backend/app/ directory should exist"
        assert APP_DIR.is_dir(), "backend/app/ should be a directory"

    @pytest.mark.parametrize(
        "subdir",
        [
            "api",
            "api/v1",
            "api/v1/endpoints",
            "core",
            "models",
            "schemas",
            "services",
            "db",
        ],
    )
    def test_subdirectories_exist(self, subdir):
        """Test that all required subdirectories exist."""
        dir_path = APP_DIR / subdir
        assert dir_path.exists(), f"backend/app/{subdir}/ should exist"
        assert dir_path.is_dir(), f"backend/app/{subdir}/ should be a directory"

    @pytest.mark.parametrize(
        "package_path",
        [
            ".",
            "api",
            "api/v1",
            "api/v1/endpoints",
            "core",
            "models",
            "schemas",
            "services",
            "db",
        ],
    )
    def test_init_files_exist(self, package_path):
        """Test that __init__.py exists in all packages."""
        if package_path == ".":
            init_path = APP_DIR / "__init__.py"
        else:
            init_path = APP_DIR / package_path / "__init__.py"

        assert init_path.exists(), f"{init_path} should exist"
        assert init_path.is_file(), f"{init_path} should be a file"

    def test_requirements_file_exists(self):
        """Test that requirements.txt exists."""
        requirements_path = BACKEND_DIR / "requirements.txt"
        assert requirements_path.exists(), "requirements.txt should exist"
        assert requirements_path.is_file(), "requirements.txt should be a file"

    def test_requirements_contains_fastapi(self):
        """Test that requirements.txt contains FastAPI."""
        requirements_path = BACKEND_DIR / "requirements.txt"
        content = requirements_path.read_text()
        assert "fastapi" in content.lower(), "requirements.txt should include fastapi"
        assert "sqlalchemy" in content.lower(), "requirements.txt should include sqlalchemy"
        assert "alembic" in content.lower(), "requirements.txt should include alembic"

    def test_tests_directory_exists(self):
        """Test that tests directory exists."""
        tests_dir = BACKEND_DIR / "tests"
        assert tests_dir.exists(), "backend/tests/ should exist"
        assert tests_dir.is_dir(), "backend/tests/ should be a directory"

    def test_alembic_directory_exists(self):
        """Test that alembic directory exists."""
        alembic_dir = BACKEND_DIR / "alembic"
        assert alembic_dir.exists(), "backend/alembic/ should exist"
        assert alembic_dir.is_dir(), "backend/alembic/ should be a directory"

    def test_python_imports_work(self):
        """Test that Python can import from app package."""
        # Add backend to Python path temporarily
        import sys

        sys.path.insert(0, str(BACKEND_DIR))

        try:
            # Test imports
            import app
            import app.api
            import app.core
            import app.models
            import app.schemas
            import app.services
            import app.db

            assert app is not None, "app package should be importable"
            assert app.api is not None, "app.api package should be importable"
            assert app.core is not None, "app.core package should be importable"
            assert app.models is not None, "app.models package should be importable"
            assert app.schemas is not None, "app.schemas package should be importable"
            assert app.services is not None, "app.services package should be importable"
            assert app.db is not None, "app.db package should be importable"
        finally:
            # Clean up sys.path
            sys.path.remove(str(BACKEND_DIR))
