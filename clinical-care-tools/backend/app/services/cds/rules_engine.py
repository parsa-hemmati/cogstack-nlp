"""CDS Rules Engine for evaluating business rules against patient data."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.cds_rule import CDSRule
from app.schemas.cds import CDSRecommendation


class RulesEngine:
    """Engine for evaluating CDS rules against patient data.

    Evaluates IF-THEN rules in priority order (highest first) and generates
    recommendations when conditions are met.
    """

    @staticmethod
    async def get_active_rules(db: AsyncSession) -> List[CDSRule]:
        """Get all active rules ordered by priority (highest first).

        Args:
            db: Database session

        Returns:
            List of active CDSRule instances
        """
        query = (
            select(CDSRule)
            .where(CDSRule.active == True)
            .order_by(CDSRule.priority.desc())  # Highest priority first
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_rules_by_ids(db: AsyncSession, rule_ids: List[UUID]) -> List[CDSRule]:
        """Get specific rules by IDs.

        Args:
            db: Database session
            rule_ids: List of rule UUIDs

        Returns:
            List of CDSRule instances
        """
        query = (
            select(CDSRule)
            .where(CDSRule.id.in_(rule_ids))
            .where(CDSRule.active == True)
            .order_by(CDSRule.priority.desc())
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    def evaluate_rule(rule: CDSRule, patient_data: Dict[str, Any]) -> bool:
        """Evaluate a single rule's conditions against patient data.

        Uses the CDSRule.evaluate_conditions() method which implements
        basic condition logic (equals, greater_than, less_than, etc.).

        For production, consider using the business-rules library for
        more sophisticated rule evaluation.

        Args:
            rule: CDSRule to evaluate
            patient_data: Dictionary of patient attributes

        Returns:
            True if all conditions are met, False otherwise
        """
        return rule.evaluate_conditions(patient_data)

    @staticmethod
    async def evaluate_rules(
        db: AsyncSession,
        patient_data: Dict[str, Any],
        rule_ids: Optional[List[UUID]] = None
    ) -> List[CDSRecommendation]:
        """Evaluate rules against patient data and generate recommendations.

        Args:
            db: Database session
            patient_data: Patient data to evaluate rules against
            rule_ids: Optional list of specific rule IDs to evaluate (if None, evaluate all active rules)

        Returns:
            List of recommendations for rules that triggered
        """
        # Get rules to evaluate
        if rule_ids:
            rules = await RulesEngine.get_rules_by_ids(db, rule_ids)
        else:
            rules = await RulesEngine.get_active_rules(db)

        # Evaluate each rule and collect recommendations
        recommendations = []

        for rule in rules:
            # Evaluate conditions
            if RulesEngine.evaluate_rule(rule, patient_data):
                # Rule triggered - create recommendation
                recommendation = CDSRecommendation(
                    rule_id=rule.id,
                    rule_name=rule.rule_name,
                    priority=rule.priority,
                    actions=rule.actions,  # JSONB actions list
                    triggered_at=datetime.utcnow()
                )
                recommendations.append(recommendation)

        return recommendations

    @staticmethod
    async def evaluate_rules_for_condition(
        db: AsyncSession,
        condition_code: str,
        patient_data: Dict[str, Any]
    ) -> List[CDSRecommendation]:
        """Evaluate rules relevant to a specific condition code.

        This is a convenience method for filtering rules by condition before evaluation.

        Args:
            db: Database session
            condition_code: ICD-10 or SNOMED CT condition code
            patient_data: Patient data to evaluate

        Returns:
            List of recommendations for rules that triggered
        """
        # Get active rules and filter by condition_code in patient_data
        patient_data_with_condition = {**patient_data, "condition_code": condition_code}

        # Evaluate all active rules with the condition included
        return await RulesEngine.evaluate_rules(db, patient_data_with_condition)
