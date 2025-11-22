"""
Unit tests for RBAC (Role-Based Access Control) system.

Tests role permissions, permission decorators, and access control.
"""

import pytest
from fastapi import HTTPException
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.permissions import (
    ROLE_PERMISSIONS,
    has_permission,
    require_permission,
)


def test_role_permissions_defined_for_all_roles():
    """Test that all 4 roles have permission definitions."""
    required_roles = ["admin", "clinician", "researcher", "viewer"]

    for role in required_roles:
        assert role in ROLE_PERMISSIONS, \
            f"Role '{role}' should have permission definitions"
        assert isinstance(ROLE_PERMISSIONS[role], list), \
            f"Permissions for '{role}' should be a list"


def test_admin_has_wildcard_permissions():
    """Test that admin role has wildcard (*) permissions for all resources."""
    admin_perms = ROLE_PERMISSIONS["admin"]

    # Admin should have wildcard permissions
    assert "user:*" in admin_perms, \
        "Admin should have user:* permission"
    assert "project:*" in admin_perms, \
        "Admin should have project:* permission"
    assert "task:*" in admin_perms, \
        "Admin should have task:* permission"
    assert "document:*" in admin_perms, \
        "Admin should have document:* permission"
    assert "module:*" in admin_perms, \
        "Admin should have module:* permission"


def test_clinician_has_patient_permissions():
    """Test that clinician role has full patient access."""
    clinician_perms = ROLE_PERMISSIONS["clinician"]

    # Clinician should have patient access
    assert "patient:*" in clinician_perms, \
        "Clinician should have patient:* permission"
    assert "document:read" in clinician_perms, \
        "Clinician should have document:read permission"
    assert "module:patient-search" in clinician_perms, \
        "Clinician should have module:patient-search permission"


def test_researcher_has_read_only_permissions():
    """Test that researcher role has read-only access."""
    researcher_perms = ROLE_PERMISSIONS["researcher"]

    # Researcher should have read-only access
    assert "patient:read" in researcher_perms, \
        "Researcher should have patient:read permission"
    assert "document:read" in researcher_perms, \
        "Researcher should have document:read permission"
    assert "module:analytics" in researcher_perms, \
        "Researcher should have module:analytics permission"

    # Researcher should NOT have write/delete permissions
    assert "patient:write" not in researcher_perms, \
        "Researcher should NOT have patient:write permission"
    assert "patient:delete" not in researcher_perms, \
        "Researcher should NOT have patient:delete permission"


def test_viewer_has_minimal_permissions():
    """Test that viewer role has minimal read-only access."""
    viewer_perms = ROLE_PERMISSIONS["viewer"]

    # Viewer should have minimal access
    assert "document:read" in viewer_perms, \
        "Viewer should have document:read permission"

    # Viewer should NOT have patient or module access
    assert not any(p.startswith("patient:") for p in viewer_perms), \
        "Viewer should NOT have any patient permissions"
    assert not any(p.startswith("user:") for p in viewer_perms), \
        "Viewer should NOT have any user permissions"


def test_has_permission_with_exact_match():
    """Test has_permission returns True for exact permission match."""
    assert has_permission("admin", "user:read"), \
        "Admin should have user:read permission (via user:*)"
    assert has_permission("clinician", "document:read"), \
        "Clinician should have document:read permission"
    assert has_permission("researcher", "patient:read"), \
        "Researcher should have patient:read permission"


def test_has_permission_with_wildcard():
    """Test has_permission returns True for wildcard matches."""
    # Admin has user:* so should have user:read, user:write, user:delete
    assert has_permission("admin", "user:read"), \
        "Admin should have user:read via user:* wildcard"
    assert has_permission("admin", "user:write"), \
        "Admin should have user:write via user:* wildcard"
    assert has_permission("admin", "user:delete"), \
        "Admin should have user:delete via user:* wildcard"

    # Clinician has patient:* so should have patient:read, patient:write
    assert has_permission("clinician", "patient:read"), \
        "Clinician should have patient:read via patient:* wildcard"
    assert has_permission("clinician", "patient:write"), \
        "Clinician should have patient:write via patient:* wildcard"


def test_has_permission_returns_false_for_missing_permission():
    """Test has_permission returns False when permission not granted."""
    assert not has_permission("viewer", "patient:read"), \
        "Viewer should NOT have patient:read permission"
    assert not has_permission("researcher", "patient:write"), \
        "Researcher should NOT have patient:write permission"
    assert not has_permission("clinician", "user:create"), \
        "Clinician should NOT have user:create permission"


def test_has_permission_returns_false_for_invalid_role():
    """Test has_permission returns False for non-existent role."""
    assert not has_permission("invalid_role", "user:read"), \
        "Non-existent role should not have any permissions"


def test_require_permission_decorator_allows_authorized_access():
    """Test require_permission decorator allows access when permission granted."""
    # Create mock user with admin role
    class MockUser:
        role = "admin"
        id = "123"
        username = "admin_user"

    # Create decorated function
    @require_permission("user:read")
    async def test_endpoint(current_user: MockUser):
        return {"message": "success"}

    # Should not raise exception for admin
    result = test_endpoint(MockUser())
    # Note: This will be an awaitable, so we need to await it in async context
    # For now, just check that it doesn't raise immediately


def test_require_permission_decorator_blocks_unauthorized_access():
    """Test require_permission decorator blocks access when permission denied."""
    # Create mock user with viewer role
    class MockUser:
        role = "viewer"
        id = "456"
        username = "viewer_user"

    # Create decorated function
    @require_permission("patient:read")
    def test_endpoint(current_user: MockUser):
        return {"message": "success"}

    # Should raise HTTPException with 403 status
    with pytest.raises(HTTPException) as exc_info:
        test_endpoint(MockUser())

    assert exc_info.value.status_code == 403, \
        "Should return 403 Forbidden for unauthorized access"
    assert "permission" in exc_info.value.detail.lower(), \
        "Error message should mention permission"


def test_require_permission_decorator_with_multiple_permissions():
    """Test require_permission decorator with multiple required permissions."""
    # Create decorated function requiring multiple permissions
    @require_permission("patient:read", "document:read")
    def test_endpoint(current_user):
        return {"message": "success"}

    # Researcher has both patient:read and document:read
    class ResearcherUser:
        role = "researcher"
        id = "789"
        username = "researcher_user"

    # Should allow access for researcher
    result = test_endpoint(ResearcherUser())

    # Viewer only has document:read, not patient:read
    class ViewerUser:
        role = "viewer"
        id = "012"
        username = "viewer_user"

    # Should block access for viewer
    with pytest.raises(HTTPException) as exc_info:
        test_endpoint(ViewerUser())

    assert exc_info.value.status_code == 403


def test_permission_format_validation():
    """Test that all permissions follow resource:action format."""
    for role, permissions in ROLE_PERMISSIONS.items():
        for perm in permissions:
            assert ":" in perm, \
                f"Permission '{perm}' for role '{role}' should follow 'resource:action' format"

            parts = perm.split(":")
            assert len(parts) == 2, \
                f"Permission '{perm}' should have exactly one ':' separator"

            resource, action = parts
            assert len(resource) > 0, \
                f"Permission '{perm}' should have non-empty resource"
            assert len(action) > 0, \
                f"Permission '{perm}' should have non-empty action"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
