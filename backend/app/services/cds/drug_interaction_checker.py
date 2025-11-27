"""Drug Interaction Checker Service.

Checks for drug-drug interactions using NHS dm+d medication codes.
Uses drug_interactions database table populated from OpenFDA or commercial sources.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.cds.drug_interaction import DrugInteraction
from app.models.cds.nhs_dmd_medication import NHSDMDMedication

logger = logging.getLogger(__name__)


class DrugInteractionResult:
    """Result of drug interaction check."""

    def __init__(
        self,
        drug_a_code: str,
        drug_a_name: str,
        drug_b_code: str,
        drug_b_name: str,
        interaction_type: str,
        severity: int,
        description: str,
        evidence_level: Optional[str] = None,
        source: Optional[str] = None,
    ):
        self.drug_a_code = drug_a_code
        self.drug_a_name = drug_a_name
        self.drug_b_code = drug_b_code
        self.drug_b_name = drug_b_name
        self.interaction_type = interaction_type
        self.severity = severity
        self.description = description
        self.evidence_level = evidence_level
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "drug_a": {
                "code": self.drug_a_code,
                "name": self.drug_a_name,
            },
            "drug_b": {
                "code": self.drug_b_code,
                "name": self.drug_b_name,
            },
            "interaction_type": self.interaction_type,
            "severity": self.severity,
            "description": self.description,
            "evidence_level": self.evidence_level,
            "source": self.source,
        }


class DrugInteractionChecker:
    """Service for checking drug-drug interactions."""

    @staticmethod
    async def check_interactions(
        db: AsyncSession,
        new_medication_code: str,
        current_medication_codes: List[str],
        min_severity: int = 2,  # Default: check for major (2) and contraindicated (1)
    ) -> List[DrugInteractionResult]:
        """Check for drug interactions between new medication and current medications.

        Args:
            db: Database session
            new_medication_code: dm+d code for new medication to check
            current_medication_codes: List of dm+d codes for current medications
            min_severity: Minimum severity to include (1=contraindicated, 2=major, 3=moderate, 4=minor)

        Returns:
            List of DrugInteractionResult objects for interactions found

        Example:
            # Check if new medication (Warfarin) interacts with current meds (Aspirin, Metformin)
            interactions = await checker.check_interactions(
                db,
                new_medication_code="322166004",  # Warfarin
                current_medication_codes=["322259000", "322301000"],  # Aspirin, Metformin
                min_severity=2  # Only major and contraindicated
            )
            # Returns: [interaction_result] if Warfarin-Aspirin interaction exists
        """
        if not current_medication_codes:
            logger.debug(f"No current medications to check against {new_medication_code}")
            return []

        logger.info(
            f"Checking interactions for new medication {new_medication_code} "
            f"against {len(current_medication_codes)} current medications"
        )

        interactions = []

        for current_code in current_medication_codes:
            # Check both directions (A-B and B-A) since interactions are bidirectional
            interaction = await DrugInteractionChecker._check_interaction_pair(
                db, new_medication_code, current_code, min_severity
            )

            if interaction:
                interactions.append(interaction)

        logger.info(
            f"Found {len(interactions)} interactions for {new_medication_code} "
            f"(severity >= {min_severity})"
        )

        # Sort by severity (most severe first)
        interactions.sort(key=lambda x: x.severity)

        return interactions

    @staticmethod
    async def _check_interaction_pair(
        db: AsyncSession,
        drug_a_code: str,
        drug_b_code: str,
        min_severity: int,
    ) -> Optional[DrugInteractionResult]:
        """Check for interaction between two specific drugs.

        Args:
            db: Database session
            drug_a_code: dm+d code for first drug
            drug_b_code: dm+d code for second drug
            min_severity: Minimum severity to include

        Returns:
            DrugInteractionResult if interaction found, None otherwise
        """
        # Query drug_interactions table for bidirectional match
        # (A-B) OR (B-A) since interactions work both ways
        query = (
            select(DrugInteraction)
            .where(
                and_(
                    or_(
                        and_(
                            DrugInteraction.drug_a_code == drug_a_code,
                            DrugInteraction.drug_b_code == drug_b_code,
                        ),
                        and_(
                            DrugInteraction.drug_a_code == drug_b_code,
                            DrugInteraction.drug_b_code == drug_a_code,
                        ),
                    ),
                    DrugInteraction.severity <= min_severity,  # Lower severity number = more severe
                )
            )
            .order_by(DrugInteraction.severity.asc())  # Most severe first
            .limit(1)
        )

        result = await db.execute(query)
        interaction = result.scalar_one_or_none()

        if not interaction:
            return None

        # Fetch medication names for better error messages
        drug_a_name = await DrugInteractionChecker._get_medication_name(db, drug_a_code)
        drug_b_name = await DrugInteractionChecker._get_medication_name(db, drug_b_code)

        return DrugInteractionResult(
            drug_a_code=drug_a_code,
            drug_a_name=drug_a_name or drug_a_code,
            drug_b_code=drug_b_code,
            drug_b_name=drug_b_name or drug_b_code,
            interaction_type=interaction.interaction_type,
            severity=interaction.severity,
            description=interaction.description,
            evidence_level=interaction.evidence_level,
            source=interaction.source,
        )

    @staticmethod
    async def _get_medication_name(db: AsyncSession, dm_d_code: str) -> Optional[str]:
        """Get medication name from NHS dm+d database.

        Args:
            db: Database session
            dm_d_code: dm+d code

        Returns:
            Medication name if found, None otherwise
        """
        query = select(NHSDMDMedication.name).where(NHSDMDMedication.dm_d_code == dm_d_code)

        result = await db.execute(query)
        name = result.scalar_one_or_none()

        return name

    @staticmethod
    async def get_medication_by_code(
        db: AsyncSession, dm_d_code: str
    ) -> Optional[Dict[str, Any]]:
        """Get medication details from NHS dm+d database.

        Args:
            db: Database session
            dm_d_code: dm+d code

        Returns:
            Medication details dict if found, None otherwise
        """
        query = select(NHSDMDMedication).where(NHSDMDMedication.dm_d_code == dm_d_code)

        result = await db.execute(query)
        medication = result.scalar_one_or_none()

        if not medication:
            return None

        return {
            "dm_d_code": medication.dm_d_code,
            "name": medication.name,
            "form": medication.form,
            "strength": medication.strength,
            "unit": medication.unit,
            "vtm_id": medication.vtm_id,
            "vmp_id": medication.vmp_id,
            "amp_id": medication.amp_id,
            "is_active": medication.is_active,
        }

    @staticmethod
    async def search_medications(
        db: AsyncSession,
        search_term: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search medications by name.

        Args:
            db: Database session
            search_term: Search term (medication name)
            limit: Maximum results to return

        Returns:
            List of medication details dicts

        Example:
            # Search for "paracetamol"
            results = await checker.search_medications(db, "paracetamol")
            # Returns: [{"dm_d_code": "322236009", "name": "Paracetamol 500mg tablets", ...}, ...]
        """
        query = (
            select(NHSDMDMedication)
            .where(
                and_(
                    NHSDMDMedication.name.ilike(f"%{search_term}%"),
                    NHSDMDMedication.is_active == True,
                )
            )
            .order_by(NHSDMDMedication.name)
            .limit(limit)
        )

        result = await db.execute(query)
        medications = result.scalars().all()

        return [
            {
                "dm_d_code": med.dm_d_code,
                "name": med.name,
                "form": med.form,
                "strength": med.strength,
                "unit": med.unit,
            }
            for med in medications
        ]


# Singleton instance (optional - can also inject)
_drug_interaction_checker: Optional[DrugInteractionChecker] = None


def get_drug_interaction_checker() -> DrugInteractionChecker:
    """Get global drug interaction checker instance (singleton pattern).

    Returns:
        DrugInteractionChecker instance
    """
    global _drug_interaction_checker
    if _drug_interaction_checker is None:
        _drug_interaction_checker = DrugInteractionChecker()
    return _drug_interaction_checker
