"""
Module Model

Represents installed modules in the system.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, Boolean, func, JSON
from sqlalchemy.orm import mapped_column, Mapped

from app.models import Base


class Module(Base):
    """
    Installed module model for plugin system.

    Modules represent optional functionality that can be enabled/disabled
    without code changes. Each module has its own API routes, permissions, and configuration.

    Attributes:
        id: Unique module identifier (UUID)
        name: Module name (unique, kebab-case: 'patient-search')
        display_name: Human-readable name ('Patient Search')
        description: Module description
        version: Semantic version (e.g., '1.0.0')
        is_enabled: Whether module is active
        configuration: Module-specific configuration as JSON
        permissions: Array of permission strings (e.g., ['patient_search.view', 'patient_search.search'])
        routes: Array of route definitions (for frontend registration)
        installed_at: When module was installed
        installed_by: User who installed module
        updated_at: When module configuration was last updated
        updated_by: User who last updated module

    Notes:
        - Module routes are dynamically registered at application startup
        - Permissions follow pattern: 'module-name.action' (e.g., 'patient-search.view')
        - Configuration includes module-specific settings (API keys, thresholds, etc.)
        - Modules can be enabled/disabled without restart
    """

    __tablename__ = "modules"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Module Identity
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Kebab-case name: 'patient-search', 'timeline', 'cds', 'cohort'",
    )
    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable: 'Patient Search', 'Timeline View'",
    )
    description: Mapped[str] = mapped_column(String(2000), nullable=False, default="")

    # Version & Status
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Semantic versioning (e.g., '1.0.0')",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # Configuration
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default={},
        comment="Module-specific configuration (API keys, thresholds, feature flags)",
    )

    # Permissions (for access control)
    permissions: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="Array of permission strings: ['patient_search.view', 'patient_search.search']",
    )

    # Routes (for frontend registration)
    routes: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="Array of route definitions for frontend registration",
    )

    # Audit
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    installed_by: Mapped[UUID] = mapped_column(nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )
    updated_by: Mapped[Optional[UUID]] = mapped_column(nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_modules_name", "name"),
        Index("idx_modules_enabled", "is_enabled"),
    )

    def __repr__(self) -> str:
        """String representation of Module."""
        status = "enabled" if self.is_enabled else "disabled"
        return f"<Module(name={self.name}, version={self.version}, status={status})>"
