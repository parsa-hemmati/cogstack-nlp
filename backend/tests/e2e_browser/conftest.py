"""
Pytest fixtures for browser-use AI exploratory tests.
"""
import os
import pytest
from typing import Generator

# Skip all tests if ANTHROPIC_API_KEY not set
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY environment variable not set"
)


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL for the frontend application."""
    return os.getenv("FRONTEND_URL", "http://localhost:8080")


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Base URL for the backend API."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def test_patient_id() -> str:
    """Test patient ID for timeline tests."""
    return os.getenv("TEST_PATIENT_ID", "patient-test-001")


@pytest.fixture
def llm():
    """Create Anthropic LLM instance for browser-use."""
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=os.getenv("BROWSER_USE_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=4096,
        temperature=0
    )


@pytest.fixture
def browser_config() -> dict:
    """Browser configuration for browser-use agent."""
    return {
        "headless": os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
        "timeout": int(os.getenv("BROWSER_TIMEOUT", "30000")),
        "viewport": {"width": 1280, "height": 720}
    }
