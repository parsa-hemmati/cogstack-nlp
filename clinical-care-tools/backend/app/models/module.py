"""
Module Model.

Stores metadata for available modules (patient-search, timeline-view, etc.).

Modules represent discrete functional units that can be enabled/disabled dynamically.
Each module has its own configuration, permissions, and UI components.

Module Registry:
- patient-search: Search patients by clinical concepts
- timeline-view: Visualize patient timeline
- clinical-decision-support: CDS Hooks integration
- (Future modules can be added)

Attributes:
    id: Unique module identifier (UUID)
    name: Unique module name (slug format: "patient-search")
    display_name: Human-readable module name ("Patient Search")
    description: Module description (nullable)
    version: Module version (semantic versioning: "1.0.0")
    enabled: Whether module is currently active
    config: Module-specific configuration (JSONB - flexible schema)
    icon: Vuetify icon name (e.g., "mdi-account-search")
    permissions: Required permissions to access module (ARRAY)
    created_at: Module registration timestamp
    updated_at: Last configuration update timestamp

Example:
    >>> module = Module(
    ...     name="patient-search",
    ...     display_name="Patient Search",
    ...     description="Search for patients by clinical concepts",
    ...     version="1.0.0",
    ...     enabled=True,
    ...     config={"max_results": 100},
    ...     icon="mdi-account-search",
    ...     permissions=["search_patients"]
    ... )
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Module(Base):
    """
    Module model for dynamic module registry.

    Modules can be enabled/disabled dynamically and have their own
    configuration, permissions, and UI routes.

    Relationships:
        - None (standalone registry)

    Indexes:
        - name (unique): For fast module lookup by name

    Example:
        >>> # Create patient search module
        >>> module = Module(
        ...     name="patient-search",
        ...     display_name="Patient Search",
        ...     enabled=True,
        ...     config={"max_results": 100}
        ... )
        >>>
        >>> # Disable module
        >>> module.enabled = False
        >>>
        >>> # Update configuration
        >>> module.config["max_results"] = 200
    """

    __tablename__ = "modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Module identification
    name = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )  # e.g., "patient-search"

    display_name = Column(
        String(200),
        nullable=False
    )  # e.g., "Patient Search"

    description = Column(
        String(1000),
        nullable=True
    )  # Module description for UI

    version = Column(
        String(20),
        nullable=False,
        default="1.0.0"
    )  # Semantic versioning

    # Module state
    enabled = Column(
        Boolean,
        nullable=False,
        default=True
    )  # Is module currently active?

    # Module configuration (JSONB - flexible schema)
    config = Column(
        JSON,
        nullable=False,
        default=dict
    )  # Module-specific settings

    # UI metadata
    icon = Column(
        String(50),
        nullable=True
    )  # Vuetify icon name (e.g., "mdi-account-search")

    # Access control
    permissions = Column(
        ARRAY(String(100)),
        nullable=False,
        default=list
    )  # Required permissions to access module

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<Module("
            f"name={self.name}, "
            f"display_name={self.display_name}, "
            f"enabled={self.enabled}, "
            f"version={self.version}"
            f")>"
        )
