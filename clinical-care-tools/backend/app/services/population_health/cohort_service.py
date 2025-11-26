"""CohortService for managing patient cohorts.

Provides CRUD operations for cohort definitions and manages
cohort membership including dynamic refresh.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.population_health.cohort import CohortDefinition, CohortMembership

logger = logging.getLogger(__name__)


class CohortService:
    """Service for managing patient cohorts.

    Handles cohort creation, membership management, and dynamic refresh.
    """

    def __init__(self, db: Session):
        """Initialize cohort service.

        Args:
            db: Database session
        """
        self.db = db

    # ==================== Cohort CRUD ====================

    def create_cohort(
        self,
        name: str,
        query_definition: Dict[str, Any],
        created_by: UUID,
        description: Optional[str] = None,
        inclusion_criteria: Optional[Dict[str, Any]] = None,
        exclusion_criteria: Optional[Dict[str, Any]] = None,
        is_dynamic: bool = True,
        is_public: bool = False
    ) -> CohortDefinition:
        """Create a new cohort definition.

        Args:
            name: Cohort name
            query_definition: ES query to find matching patients
            created_by: User creating the cohort
            description: Optional description
            inclusion_criteria: Additional inclusion rules
            exclusion_criteria: Exclusion rules
            is_dynamic: Whether to auto-refresh membership
            is_public: Whether visible to all users

        Returns:
            Created CohortDefinition
        """
        cohort = CohortDefinition(
            name=name,
            description=description,
            query_definition=query_definition,
            inclusion_criteria=inclusion_criteria,
            exclusion_criteria=exclusion_criteria,
            is_dynamic=is_dynamic,
            is_public=is_public,
            created_by=created_by
        )

        self.db.add(cohort)
        self.db.commit()
        self.db.refresh(cohort)

        logger.info(f"Created cohort: {name} (id={cohort.id})")

        # Initial population if dynamic
        if is_dynamic:
            self.refresh_cohort(cohort.id)

        return cohort

    def get_cohort(self, cohort_id: UUID) -> Optional[CohortDefinition]:
        """Get a cohort by ID.

        Args:
            cohort_id: Cohort ID

        Returns:
            CohortDefinition or None
        """
        return self.db.query(CohortDefinition).filter(
            CohortDefinition.id == cohort_id
        ).first()

    def list_cohorts(
        self,
        user_id: Optional[UUID] = None,
        include_public: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[CohortDefinition]:
        """List cohort definitions.

        Args:
            user_id: Filter to cohorts created by this user
            include_public: Include public cohorts
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of CohortDefinition objects
        """
        query = self.db.query(CohortDefinition)

        if user_id:
            if include_public:
                query = query.filter(or_(
                    CohortDefinition.created_by == user_id,
                    CohortDefinition.is_public == True
                ))
            else:
                query = query.filter(CohortDefinition.created_by == user_id)

        return query.offset(offset).limit(limit).all()

    def update_cohort(
        self,
        cohort_id: UUID,
        **updates
    ) -> Optional[CohortDefinition]:
        """Update a cohort definition.

        Args:
            cohort_id: Cohort to update
            **updates: Fields to update

        Returns:
            Updated cohort or None
        """
        cohort = self.get_cohort(cohort_id)
        if not cohort:
            return None

        allowed_fields = [
            "name", "description", "query_definition",
            "inclusion_criteria", "exclusion_criteria",
            "is_dynamic", "is_public"
        ]

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(cohort, field, value)

        self.db.commit()
        self.db.refresh(cohort)

        # Refresh membership if query changed
        if "query_definition" in updates and cohort.is_dynamic:
            self.refresh_cohort(cohort_id)

        return cohort

    def delete_cohort(self, cohort_id: UUID) -> bool:
        """Delete a cohort definition.

        Args:
            cohort_id: Cohort to delete

        Returns:
            True if deleted, False if not found
        """
        cohort = self.get_cohort(cohort_id)
        if not cohort:
            return False

        self.db.delete(cohort)
        self.db.commit()

        logger.info(f"Deleted cohort: {cohort.name}")
        return True

    # ==================== Membership Management ====================

    def refresh_cohort(self, cohort_id: UUID) -> int:
        """Refresh cohort membership by re-running the query.

        Args:
            cohort_id: Cohort to refresh

        Returns:
            Number of patients in cohort after refresh
        """
        cohort = self.get_cohort(cohort_id)
        if not cohort:
            return 0

        # Execute the query to find matching patients
        matching_patients = self._execute_cohort_query(cohort.query_definition)

        # Apply inclusion/exclusion criteria
        if cohort.inclusion_criteria:
            matching_patients = self._apply_inclusion_criteria(
                matching_patients, cohort.inclusion_criteria
            )
        if cohort.exclusion_criteria:
            matching_patients = self._apply_exclusion_criteria(
                matching_patients, cohort.exclusion_criteria
            )

        # Update membership
        existing_ids = set(
            m.patient_id for m in self.db.query(CohortMembership).filter(
                CohortMembership.cohort_id == cohort_id
            ).all()
        )

        new_ids = set(p["id"] for p in matching_patients)

        # Remove patients no longer matching
        to_remove = existing_ids - new_ids
        if to_remove:
            self.db.query(CohortMembership).filter(
                and_(
                    CohortMembership.cohort_id == cohort_id,
                    CohortMembership.patient_id.in_(to_remove)
                )
            ).delete(synchronize_session=False)

        # Add new matching patients
        to_add = new_ids - existing_ids
        for patient_id in to_add:
            patient_data = next(p for p in matching_patients if p["id"] == patient_id)
            membership = CohortMembership(
                cohort_id=cohort_id,
                patient_id=patient_id,
                match_score=patient_data.get("score"),
                metadata=patient_data.get("match_metadata")
            )
            self.db.add(membership)

        # Update cohort stats
        cohort.patient_count = len(new_ids)
        cohort.last_refreshed = datetime.utcnow()

        self.db.commit()

        logger.info(f"Refreshed cohort {cohort.name}: {len(new_ids)} patients")
        return len(new_ids)

    def add_patient_to_cohort(
        self,
        cohort_id: UUID,
        patient_id: UUID,
        added_by: UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[CohortMembership]:
        """Manually add a patient to a cohort.

        Args:
            cohort_id: Cohort to add to
            patient_id: Patient to add
            added_by: User adding the patient
            metadata: Optional metadata

        Returns:
            CohortMembership or None
        """
        # Check if already a member
        existing = self.db.query(CohortMembership).filter(
            and_(
                CohortMembership.cohort_id == cohort_id,
                CohortMembership.patient_id == patient_id
            )
        ).first()

        if existing:
            return existing

        membership = CohortMembership(
            cohort_id=cohort_id,
            patient_id=patient_id,
            added_by=added_by,
            metadata=metadata
        )

        self.db.add(membership)

        # Update count
        cohort = self.get_cohort(cohort_id)
        if cohort:
            cohort.patient_count = (cohort.patient_count or 0) + 1

        self.db.commit()
        self.db.refresh(membership)

        return membership

    def remove_patient_from_cohort(
        self,
        cohort_id: UUID,
        patient_id: UUID
    ) -> bool:
        """Remove a patient from a cohort.

        Args:
            cohort_id: Cohort to remove from
            patient_id: Patient to remove

        Returns:
            True if removed, False if not found
        """
        membership = self.db.query(CohortMembership).filter(
            and_(
                CohortMembership.cohort_id == cohort_id,
                CohortMembership.patient_id == patient_id
            )
        ).first()

        if not membership:
            return False

        self.db.delete(membership)

        # Update count
        cohort = self.get_cohort(cohort_id)
        if cohort and cohort.patient_count:
            cohort.patient_count = max(0, cohort.patient_count - 1)

        self.db.commit()
        return True

    def get_cohort_patients(
        self,
        cohort_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[CohortMembership]:
        """Get patients in a cohort.

        Args:
            cohort_id: Cohort ID
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of CohortMembership objects
        """
        return self.db.query(CohortMembership).filter(
            CohortMembership.cohort_id == cohort_id
        ).offset(offset).limit(limit).all()

    def get_patient_cohorts(self, patient_id: UUID) -> List[CohortDefinition]:
        """Get all cohorts a patient belongs to.

        Args:
            patient_id: Patient ID

        Returns:
            List of CohortDefinition objects
        """
        memberships = self.db.query(CohortMembership).filter(
            CohortMembership.patient_id == patient_id
        ).all()

        cohort_ids = [m.cohort_id for m in memberships]
        return self.db.query(CohortDefinition).filter(
            CohortDefinition.id.in_(cohort_ids)
        ).all()

    # ==================== Query Execution ====================

    def _execute_cohort_query(
        self,
        query_definition: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute the cohort query to find matching patients.

        This would integrate with Elasticsearch or the patient search service.

        Args:
            query_definition: Query in ES format

        Returns:
            List of matching patient records with IDs
        """
        # Placeholder - would integrate with search service
        # from app.services.elasticsearch.search_query_builder import SearchQueryBuilder
        # builder = SearchQueryBuilder()
        # results = builder.execute(query_definition)
        # return results

        logger.info(f"Executing cohort query: {query_definition}")
        return []

    def _apply_inclusion_criteria(
        self,
        patients: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply inclusion criteria to filter patients.

        Args:
            patients: List of patient records
            criteria: Inclusion criteria

        Returns:
            Filtered list of patients
        """
        # Placeholder for inclusion logic
        return patients

    def _apply_exclusion_criteria(
        self,
        patients: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply exclusion criteria to filter patients.

        Args:
            patients: List of patient records
            criteria: Exclusion criteria

        Returns:
            Filtered list of patients
        """
        # Placeholder for exclusion logic
        return patients

    # ==================== Comparison ====================

    def compare_cohorts(
        self,
        cohort_id_a: UUID,
        cohort_id_b: UUID
    ) -> Dict[str, Any]:
        """Compare two cohorts.

        Args:
            cohort_id_a: First cohort
            cohort_id_b: Second cohort

        Returns:
            Comparison statistics
        """
        patients_a = set(
            m.patient_id for m in self.get_cohort_patients(cohort_id_a, limit=10000)
        )
        patients_b = set(
            m.patient_id for m in self.get_cohort_patients(cohort_id_b, limit=10000)
        )

        overlap = patients_a & patients_b
        only_a = patients_a - patients_b
        only_b = patients_b - patients_a

        return {
            "cohort_a_count": len(patients_a),
            "cohort_b_count": len(patients_b),
            "overlap_count": len(overlap),
            "only_in_a_count": len(only_a),
            "only_in_b_count": len(only_b),
            "jaccard_similarity": len(overlap) / len(patients_a | patients_b) if patients_a | patients_b else 0,
        }
