"""Guidelines Service for CDS Guidelines database operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.cds_guideline import CDSGuideline
from app.schemas.cds import (
    CDSGuidelineCreate,
    CDSGuidelineUpdate,
    CDSGuidelineSearchRequest,
)


class GuidelinesService:
    """Service for managing CDS Guidelines."""

    @staticmethod
    async def create_guideline(
        db: AsyncSession,
        guideline_data: CDSGuidelineCreate
    ) -> CDSGuideline:
        """Create a new CDS guideline.

        Args:
            db: Database session
            guideline_data: Guideline creation data

        Returns:
            Created CDSGuideline instance
        """
        guideline = CDSGuideline(**guideline_data.model_dump())
        db.add(guideline)
        await db.commit()
        await db.refresh(guideline)
        return guideline

    @staticmethod
    async def get_guideline_by_id(
        db: AsyncSession,
        guideline_id: UUID
    ) -> Optional[CDSGuideline]:
        """Get a guideline by ID.

        Args:
            db: Database session
            guideline_id: Guideline UUID

        Returns:
            CDSGuideline if found, None otherwise
        """
        result = await db.execute(
            select(CDSGuideline).where(CDSGuideline.id == guideline_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def search_guidelines(
        db: AsyncSession,
        search_params: CDSGuidelineSearchRequest
    ) -> tuple[List[CDSGuideline], int]:
        """Search guidelines with filters and pagination.

        Args:
            db: Database session
            search_params: Search parameters with filters

        Returns:
            Tuple of (list of guidelines, total count)
        """
        # Build base query
        query = select(CDSGuideline)

        # Apply filters
        if search_params.condition_code:
            query = query.where(CDSGuideline.condition_code == search_params.condition_code)

        if search_params.guideline_source:
            query = query.where(CDSGuideline.guideline_source == search_params.guideline_source)

        if search_params.evidence_level:
            query = query.where(CDSGuideline.evidence_level == search_params.evidence_level)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply ordering (evidence level A > B > C, then by last_updated desc)
        query = query.order_by(
            CDSGuideline.evidence_level.asc(),
            CDSGuideline.last_updated.desc()
        )

        # Apply pagination
        offset = (search_params.page - 1) * search_params.page_size
        query = query.offset(offset).limit(search_params.page_size)

        # Execute query
        result = await db.execute(query)
        guidelines = list(result.scalars().all())

        return guidelines, total

    @staticmethod
    async def list_guidelines(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[CDSGuideline], int]:
        """List all guidelines with pagination.

        Args:
            db: Database session
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (list of guidelines, total count)
        """
        # Count total guidelines
        count_query = select(func.count()).select_from(CDSGuideline)
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated guidelines
        offset = (page - 1) * page_size
        query = (
            select(CDSGuideline)
            .order_by(
                CDSGuideline.evidence_level.asc(),
                CDSGuideline.last_updated.desc()
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await db.execute(query)
        guidelines = list(result.scalars().all())

        return guidelines, total

    @staticmethod
    async def update_guideline(
        db: AsyncSession,
        guideline_id: UUID,
        guideline_data: CDSGuidelineUpdate
    ) -> Optional[CDSGuideline]:
        """Update a guideline.

        Args:
            db: Database session
            guideline_id: Guideline UUID
            guideline_data: Update data

        Returns:
            Updated CDSGuideline if found, None otherwise
        """
        guideline = await GuidelinesService.get_guideline_by_id(db, guideline_id)
        if not guideline:
            return None

        # Update fields
        update_data = guideline_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(guideline, field, value)

        await db.commit()
        await db.refresh(guideline)
        return guideline

    @staticmethod
    async def delete_guideline(
        db: AsyncSession,
        guideline_id: UUID
    ) -> bool:
        """Delete a guideline.

        Args:
            db: Database session
            guideline_id: Guideline UUID

        Returns:
            True if deleted, False if not found
        """
        guideline = await GuidelinesService.get_guideline_by_id(db, guideline_id)
        if not guideline:
            return False

        await db.delete(guideline)
        await db.commit()
        return True

    @staticmethod
    async def get_guidelines_for_condition(
        db: AsyncSession,
        condition_code: str
    ) -> List[CDSGuideline]:
        """Get all guidelines for a specific condition code.

        Args:
            db: Database session
            condition_code: ICD-10 or SNOMED CT condition code

        Returns:
            List of CDSGuideline instances ordered by evidence level
        """
        query = (
            select(CDSGuideline)
            .where(CDSGuideline.condition_code == condition_code)
            .order_by(
                CDSGuideline.evidence_level.asc(),  # A first, then B, then C
                CDSGuideline.last_updated.desc()
            )
        )

        result = await db.execute(query)
        return list(result.scalars().all())
