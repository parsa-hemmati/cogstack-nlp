"""
Module Schemas

Pydantic models for module configuration and API requests/responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ModuleConfig(BaseModel):
    """
    Module configuration schema.

    Used for module-specific settings that can be modified at runtime.
    """

    # Common configuration fields
    enabled_features: List[str] = Field(
        default=[],
        description="List of enabled feature flags",
    )

    api_timeout: int = Field(
        default=30,
        description="API timeout in seconds",
        ge=1,
        le=300,
    )

    max_results: int = Field(
        default=100,
        description="Maximum number of results to return",
        ge=1,
        le=1000,
    )

    # Module-specific configuration (JSON object)
    custom_config: Dict[str, Any] = Field(
        default={},
        description="Module-specific configuration",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "enabled_features": ["advanced_filters", "export_csv"],
                "api_timeout": 30,
                "max_results": 100,
                "custom_config": {
                    "confidence_threshold": 0.7,
                    "use_cache": True,
                }
            }
        }
    }


class ModuleStatus(BaseModel):
    """
    Module status information.

    Provides runtime status and health information for a module.
    """

    name: str = Field(description="Module name (kebab-case)")
    display_name: str = Field(description="Human-readable name")
    version: str = Field(description="Module version")
    is_enabled: bool = Field(description="Whether module is enabled")
    is_healthy: bool = Field(default=True, description="Health check status")

    dependencies: List[str] = Field(
        default=[],
        description="List of required module dependencies",
    )

    permissions: List[str] = Field(
        default=[],
        description="List of permissions provided by module",
    )

    routes: List[Dict[str, Any]] = Field(
        default=[],
        description="List of routes registered by module",
    )

    last_health_check: Optional[datetime] = Field(
        default=None,
        description="Last health check timestamp",
    )

    error_message: Optional[str] = Field(
        default=None,
        description="Error message if unhealthy",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "patient-search",
                "display_name": "Patient Search",
                "version": "1.0.0",
                "is_enabled": True,
                "is_healthy": True,
                "dependencies": [],
                "permissions": ["patient_search.view", "patient_search.search"],
                "routes": [
                    {"path": "/search", "methods": ["POST"]},
                    {"path": "/concepts", "methods": ["GET"]},
                ],
                "last_health_check": "2024-01-01T12:00:00Z",
                "error_message": None,
            }
        }
    }


class ModuleCreateRequest(BaseModel):
    """
    Request to create/install a new module.
    """

    name: str = Field(
        description="Module name (kebab-case)",
        pattern="^[a-z][a-z0-9-]*$",
        min_length=2,
        max_length=100,
    )

    display_name: str = Field(
        description="Human-readable name",
        min_length=2,
        max_length=255,
    )

    description: str = Field(
        default="",
        description="Module description",
        max_length=2000,
    )

    version: str = Field(
        description="Semantic version",
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9-]+)?$",
    )

    configuration: ModuleConfig = Field(
        default_factory=ModuleConfig,
        description="Initial module configuration",
    )


class ModuleUpdateRequest(BaseModel):
    """
    Request to update module configuration.
    """

    display_name: Optional[str] = Field(
        default=None,
        description="Updated display name",
        min_length=2,
        max_length=255,
    )

    description: Optional[str] = Field(
        default=None,
        description="Updated description",
        max_length=2000,
    )

    configuration: Optional[ModuleConfig] = Field(
        default=None,
        description="Updated configuration",
    )


class ModuleEnableRequest(BaseModel):
    """
    Request to enable/disable a module.
    """

    enabled: bool = Field(description="Enable (true) or disable (false)")
    force: bool = Field(
        default=False,
        description="Force operation even if dependencies not met",
    )


class ModuleResponse(BaseModel):
    """
    Module information response.
    """

    id: UUID
    name: str
    display_name: str
    description: str
    version: str
    is_enabled: bool
    configuration: Dict[str, Any]
    permissions: List[str]
    routes: List[Dict[str, Any]]
    installed_at: datetime
    installed_by: UUID
    updated_at: datetime
    updated_by: Optional[UUID]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "patient-search",
                "display_name": "Patient Search",
                "description": "Search and filter patients using medical concepts",
                "version": "1.0.0",
                "is_enabled": True,
                "configuration": {
                    "enabled_features": ["meta_annotations", "export"],
                    "confidence_threshold": 0.7,
                },
                "permissions": ["patient_search.view", "patient_search.search"],
                "routes": [
                    {"path": "/search", "methods": ["POST"]},
                    {"path": "/concepts", "methods": ["GET"]},
                ],
                "installed_at": "2024-01-01T10:00:00Z",
                "installed_by": "550e8400-e29b-41d4-a716-446655440001",
                "updated_at": "2024-01-01T10:00:00Z",
                "updated_by": None,
            }
        }
    }


class ModuleListResponse(BaseModel):
    """
    List of modules response.
    """

    modules: List[ModuleResponse]
    total: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "modules": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "patient-search",
                        "display_name": "Patient Search",
                        "description": "Search and filter patients using medical concepts",
                        "version": "1.0.0",
                        "is_enabled": True,
                        "configuration": {},
                        "permissions": ["patient_search.view"],
                        "routes": [],
                        "installed_at": "2024-01-01T10:00:00Z",
                        "installed_by": "550e8400-e29b-41d4-a716-446655440001",
                        "updated_at": "2024-01-01T10:00:00Z",
                        "updated_by": None,
                    }
                ],
                "total": 1,
            }
        }
    }