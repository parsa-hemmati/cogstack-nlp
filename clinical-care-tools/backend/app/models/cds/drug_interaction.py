"""Drug Interaction Model.

SQLAlchemy model for drug-drug interaction database.
"""

from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from app.core.database import Base
import uuid


class DrugInteraction(Base):
    """Drug Interaction Model.

    Represents a drug-drug interaction between two medications (identified by dm+d codes).
    """

    __tablename__ = "drug_interactions"
    __table_args__ = {"comment": "Drug-drug interaction database"}

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Interaction ID",
    )

    # Drug Codes (dm+d)
    drug_a_code = Column(String(18), nullable=False, comment="dm+d code for first drug")
    drug_b_code = Column(String(18), nullable=False, comment="dm+d code for second drug")

    # Interaction Details
    interaction_type = Column(
        String(100),
        nullable=True,
        comment="Interaction type (contraindicated, major, moderate, minor)",
    )
    severity = Column(
        Integer,
        nullable=True,
        comment="Severity level (1=contraindicated, 2=major, 3=moderate, 4=minor)",
    )
    description = Column(Text, nullable=True, comment="Clinical guidance for the interaction")
    evidence_level = Column(String(1), nullable=True, comment="Evidence level (A, B, C)")

    # Data Source
    source = Column(String(200), nullable=True, comment="Data source (OpenFDA, Micromedex, etc.)")

    # Timestamps
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="now()",
        comment="Creation timestamp",
    )
    last_updated = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="now()",
        comment="Last update timestamp",
    )

    def __repr__(self) -> str:
        return (
            f"<DrugInteraction(id={self.id}, "
            f"drug_a={self.drug_a_code}, "
            f"drug_b={self.drug_b_code}, "
            f"severity={self.severity})>"
        )
