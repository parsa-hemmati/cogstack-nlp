"""NHS dm+d Medication Model.

SQLAlchemy model for NHS Dictionary of Medicines and Devices (dm+d) medication database.
"""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import TIMESTAMP
from app.core.database import Base


class NHSDMDMedication(Base):
    """NHS dm+d Medication Model.

    Represents a medication from the NHS Dictionary of Medicines and Devices.
    Source: NHS Digital TRUD (https://isd.digital.nhs.uk/trud3/user/guest/group/0/pack/6)
    """

    __tablename__ = "nhs_dmd_medications"
    __table_args__ = {"comment": "NHS Dictionary of Medicines and Devices (dm+d) medication database"}

    # Primary Key
    dm_d_code = Column(
        String(18),
        primary_key=True,
        nullable=False,
        comment="SNOMED CT dm+d code (18-digit)",
    )

    # Medication Details
    name = Column(String(500), nullable=False, comment="Medication name")
    form = Column(String(200), nullable=True, comment="Form (Tablet, Capsule, Injection, etc.)")
    strength = Column(String(100), nullable=True, comment="Strength (e.g., 500mg, 10mg/ml)")
    unit = Column(String(50), nullable=True, comment="Unit (mg, ml, etc.)")

    # dm+d Hierarchy IDs
    vtm_id = Column(String(18), nullable=True, comment="Virtual Therapeutic Moiety ID")
    vmp_id = Column(String(18), nullable=True, comment="Virtual Medicinal Product ID")
    amp_id = Column(String(18), nullable=True, comment="Actual Medicinal Product ID")

    # Status
    is_active = Column(Boolean, nullable=False, default=True, comment="Is medication currently active")
    last_updated = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="now()",
        comment="Last update timestamp",
    )

    def __repr__(self) -> str:
        return f"<NHSDMDMedication(code={self.dm_d_code}, name={self.name})>"
