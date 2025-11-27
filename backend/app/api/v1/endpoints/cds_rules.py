"""CDS Rules API Endpoints.

Provides endpoints for managing and evaluating clinical decision support rules
with IF-THEN logic stored as JSONB.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.cds_rule import CDSRule
from app.services.cds.rules_engine import RulesEngine
from app.schemas.cds import (
    CDSRuleCreate,
    CDSRuleUpdate,
    CDSRuleResponse,
    CDSRuleListResponse,
    CDSRuleEvaluationRequest,
    CDSRuleEvaluationResponse,
)
from app.services.audit_logger import audit_logger
from sqlalchemy import select, func


router = APIRouter(prefix="/cds/rules", tags=["cds-rules"])


@router.get("", response_model=CDSRuleListResponse)
async def list_rules(
    active_only: bool = Query(True, description="Filter to active rules only"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (1-100)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("clinician", "admin")),
):
    """List CDS rules with pagination.

    Returns rules ordered by priority (highest first).

    Args:
        active_only: Filter to active rules only (default True)
        page: Page number (1-indexed)
        page_size: Items per page (1-100)
        db: Database session
        current_user: Authenticated user with clinician/admin role

    Returns:
        Paginated list of CDS rules
    """
    # Build query
    query = select(CDSRule)
    if active_only:
        query = query.where(CDSRule.active == True)

    query = query.order_by(CDSRule.priority.desc())

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    rules = list(result.scalars().all())

    # Audit log
    await audit_logger.log(
        db=db,
        user_id=current_user.id,
        action="CDS_RULES_LIST",
        resource_type="cds_rules",
        details={"page": page, "page_size": page_size, "active_only": active_only}
    )

    # Calculate pages
    pages = (total + page_size - 1) // page_size

    return CDSRuleListResponse(
        items=[CDSRuleResponse.model_validate(r) for r in rules],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{rule_id}", response_model=CDSRuleResponse)
async def get_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("clinician", "admin")),
):
    """Get a specific CDS rule by ID.

    Args:
        rule_id: Rule UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        CDS rule details

    Raises:
        HTTPException: 404 if rule not found
    """
    # Get rule
    result = await db.execute(
        select(CDSRule).where(CDSRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Audit log
    await audit_logger.log(
        db=db,
        user_id=current_user.id,
        action="CDS_RULE_VIEW",
        resource_type="cds_rules",
        resource_id=str(rule_id)
    )

    return CDSRuleResponse.model_validate(rule)


@router.post("", response_model=CDSRuleResponse, status_code=201)
async def create_rule(
    rule_data: CDSRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),  # Only admins can create rules
):
    """Create a new CDS rule.

    Requires admin role. Used for defining clinical decision support logic.

    Args:
        rule_data: Rule creation data (conditions, actions, priority)
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Created rule

    Raises:
        HTTPException: 400 if rule name already exists
    """
    try:
        rule = CDSRule.from_dict(rule_data.model_dump())
        db.add(rule)
        await db.commit()
        await db.refresh(rule)

        # Audit log
        await audit_logger.log(
            db=db,
            user_id=current_user.id,
            action="CDS_RULE_CREATE",
            resource_type="cds_rules",
            resource_id=str(rule.id),
            details={"rule_name": rule.rule_name, "priority": rule.priority}
        )

        return CDSRuleResponse.model_validate(rule)

    except Exception as e:
        # Likely unique constraint violation
        if "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="Rule with this name already exists"
            )
        raise


@router.put("/{rule_id}", response_model=CDSRuleResponse)
async def update_rule(
    rule_id: UUID,
    rule_data: CDSRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Update a CDS rule.

    Requires admin role.

    Args:
        rule_id: Rule UUID
        rule_data: Update data
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Updated rule

    Raises:
        HTTPException: 404 if rule not found
    """
    # Get rule
    result = await db.execute(
        select(CDSRule).where(CDSRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Update fields
    update_data = rule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)

    # Audit log
    await audit_logger.log(
        db=db,
        user_id=current_user.id,
        action="CDS_RULE_UPDATE",
        resource_type="cds_rules",
        resource_id=str(rule_id),
        details=update_data
    )

    return CDSRuleResponse.model_validate(rule)


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Delete a CDS rule.

    Requires admin role.

    Args:
        rule_id: Rule UUID
        db: Database session
        current_user: Authenticated admin user

    Raises:
        HTTPException: 404 if rule not found
    """
    # Get rule
    result = await db.execute(
        select(CDSRule).where(CDSRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    await db.delete(rule)
    await db.commit()

    # Audit log
    await audit_logger.log(
        db=db,
        user_id=current_user.id,
        action="CDS_RULE_DELETE",
        resource_type="cds_rules",
        resource_id=str(rule_id)
    )

    return None


@router.post("/evaluate", response_model=CDSRuleEvaluationResponse)
async def evaluate_rules(
    eval_request: CDSRuleEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("clinician", "admin")),
):
    """Evaluate CDS rules against patient data.

    Evaluates active rules (or specified rules) against patient data
    and returns triggered recommendations ordered by priority.

    Args:
        eval_request: Patient data and optional rule IDs to evaluate
        db: Database session
        current_user: Authenticated user

    Returns:
        List of recommendations for rules that triggered
    """
    # Evaluate rules
    recommendations = await RulesEngine.evaluate_rules(
        db=db,
        patient_data=eval_request.patient_data,
        rule_ids=eval_request.rule_ids
    )

    # Get counts
    if eval_request.rule_ids:
        evaluated_count = len(eval_request.rule_ids)
    else:
        active_rules = await RulesEngine.get_active_rules(db)
        evaluated_count = len(active_rules)

    triggered_count = len(recommendations)

    # Audit log (important for clinical decision tracking)
    await audit_logger.log(
        db=db,
        user_id=current_user.id,
        action="CDS_RULES_EVALUATE",
        resource_type="cds_rules",
        details={
            "evaluated_rules_count": evaluated_count,
            "triggered_rules_count": triggered_count,
            "patient_data_fields": list(eval_request.patient_data.keys()),
        }
    )

    return CDSRuleEvaluationResponse(
        recommendations=recommendations,
        evaluated_rules_count=evaluated_count,
        triggered_rules_count=triggered_count
    )
