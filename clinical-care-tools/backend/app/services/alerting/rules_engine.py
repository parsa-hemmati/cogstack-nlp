"""AlertRulesEngine for evaluating alert conditions.

This service evaluates patient data against configured alert rules
and triggers alerts when conditions are met.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func

from app.models.alerting.alert_rule import AlertRule
from app.models.alerting.triggered_alert import TriggeredAlert

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    """Evaluates individual conditions against patient data."""

    # Supported operators
    OPERATORS = {
        "equals": lambda a, b: a == b,
        "not_equals": lambda a, b: a != b,
        "greater_than": lambda a, b: float(a) > float(b) if a is not None else False,
        "less_than": lambda a, b: float(a) < float(b) if a is not None else False,
        "greater_than_or_equals": lambda a, b: float(a) >= float(b) if a is not None else False,
        "less_than_or_equals": lambda a, b: float(a) <= float(b) if a is not None else False,
        "contains": lambda a, b: b in str(a) if a is not None else False,
        "not_contains": lambda a, b: b not in str(a) if a is not None else False,
        "in": lambda a, b: a in b if isinstance(b, list) else a == b,
        "not_in": lambda a, b: a not in b if isinstance(b, list) else a != b,
        "is_null": lambda a, b: a is None,
        "is_not_null": lambda a, b: a is not None,
        "starts_with": lambda a, b: str(a).startswith(b) if a is not None else False,
        "ends_with": lambda a, b: str(a).endswith(b) if a is not None else False,
        "regex_match": lambda a, b: bool(__import__('re').match(b, str(a))) if a is not None else False,
    }

    def evaluate(self, condition: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Evaluate a single condition against data.

        Args:
            condition: Condition definition with field, operator, value
            data: Data to evaluate against

        Returns:
            True if condition matches, False otherwise
        """
        field = condition.get("field", "")
        operator = condition.get("operator", "equals")
        expected_value = condition.get("value")

        # Get actual value from data (supports nested paths like "patient.age")
        actual_value = self._get_nested_value(data, field)

        # Get operator function
        op_func = self.OPERATORS.get(operator)
        if not op_func:
            logger.warning(f"Unknown operator: {operator}")
            return False

        try:
            return op_func(actual_value, expected_value)
        except (TypeError, ValueError) as e:
            logger.warning(f"Error evaluating condition: {e}")
            return False

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation.

        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., "patient.vitals.blood_pressure")

        Returns:
            Value at path or None if not found
        """
        keys = path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value


class AlertRulesEngine:
    """Engine for evaluating alert rules and triggering alerts.

    Evaluates patient data against configured alert rules and creates
    triggered alerts when conditions are met.

    Example rule conditions JSON:
    {
        "match_type": "all",  # "all" = AND, "any" = OR
        "conditions": [
            {"field": "lab_results.potassium", "operator": "greater_than", "value": 5.5},
            {"field": "medications", "operator": "contains", "value": "potassium"}
        ]
    }
    """

    def __init__(self, db: AsyncSession):
        """Initialize the rules engine.

        Args:
            db: Async database session
        """
        self.db = db
        self.condition_evaluator = ConditionEvaluator()

    async def get_active_rules(self) -> List[AlertRule]:
        """Get all active alert rules.

        Returns:
            List of enabled AlertRule objects
        """
        from sqlalchemy import select
        result = await self.db.execute(select(AlertRule).filter(AlertRule.enabled == True))
        return result.scalars().all()

    async def evaluate_rules(
        self,
        data: Dict[str, Any],
        patient_id: Optional[UUID] = None,
        rule_ids: Optional[List[UUID]] = None
    ) -> List[TriggeredAlert]:
        """Evaluate data against alert rules and return triggered alerts.

        Args:
            data: Data to evaluate (e.g., patient record, lab results)
            patient_id: Optional patient ID for the alert
            rule_ids: Optional list of specific rules to evaluate

        Returns:
            List of newly triggered alerts
        """
        from sqlalchemy import select
        
        triggered_alerts = []

        # Get rules to evaluate
        if rule_ids:
            result = await self.db.execute(
                select(AlertRule).filter(
                    and_(AlertRule.id.in_(rule_ids), AlertRule.enabled == True)
                )
            )
            rules = result.scalars().all()
        else:
            rules = await self.get_active_rules()

        for rule in rules:
            if self._evaluate_rule(rule, data):
                # Check if we should suppress duplicate alerts
                if not await self._should_suppress(rule.id, patient_id):
                    alert = await self._create_triggered_alert(rule, data, patient_id)
                    triggered_alerts.append(alert)
                    logger.info(f"Alert triggered: rule={rule.name}, patient={patient_id}")

        return triggered_alerts

    def _evaluate_rule(self, rule: AlertRule, data: Dict[str, Any]) -> bool:
        """Evaluate a single rule against data.

        Args:
            rule: AlertRule to evaluate
            data: Data to evaluate against

        Returns:
            True if rule conditions are met, False otherwise
        """
        conditions_config = rule.conditions
        match_type = conditions_config.get("match_type", "all")
        conditions = conditions_config.get("conditions", [])

        if not conditions:
            return False

        results = [
            self.condition_evaluator.evaluate(condition, data)
            for condition in conditions
        ]

        if match_type == "all":
            return all(results)
        elif match_type == "any":
            return any(results)
        else:
            logger.warning(f"Unknown match_type: {match_type}")
            return False

    async def _should_suppress(
        self,
        rule_id: UUID,
        patient_id: Optional[UUID],
        suppression_minutes: int = 60
    ) -> bool:
        """Check if alert should be suppressed due to recent duplicate.

        Prevents alert fatigue by suppressing duplicate alerts within
        a configurable time window.

        Args:
            rule_id: Rule that triggered
            patient_id: Patient ID (if applicable)
            suppression_minutes: Minutes to suppress duplicates

        Returns:
            True if should suppress, False otherwise
        """
        from datetime import timedelta
        from sqlalchemy import select, func

        cutoff = datetime.utcnow() - timedelta(minutes=suppression_minutes)

        query = select(func.count(TriggeredAlert.id)).filter(
            and_(
                TriggeredAlert.rule_id == rule_id,
                TriggeredAlert.triggered_at > cutoff,
                TriggeredAlert.status.in_(["new", "acknowledged"])
            )
        )

        if patient_id:
            query = query.filter(TriggeredAlert.patient_id == patient_id)

        result = await self.db.execute(query)
        count = result.scalar() or 0
        return count > 0

    async def _create_triggered_alert(
        self,
        rule: AlertRule,
        trigger_data: Dict[str, Any],
        patient_id: Optional[UUID]
    ) -> TriggeredAlert:
        """Create a new triggered alert.

        Args:
            rule: Rule that triggered
            trigger_data: Data that caused the trigger
            patient_id: Patient ID (if applicable)

        Returns:
            New TriggeredAlert instance
        """
        alert = TriggeredAlert(
            rule_id=rule.id,
            patient_id=patient_id,
            severity=rule.severity,
            status="new",
            trigger_data=trigger_data,
            triggered_at=datetime.utcnow()
        )

        self.db.add(alert)
        await self.db.flush()  # Get the ID without committing

        return alert

    async def evaluate_patient(self, patient_id: UUID) -> List[TriggeredAlert]:
        """Evaluate all active rules against a patient's current data.

        This method fetches the patient's data and evaluates it against
        all active alert rules.

        Args:
            patient_id: Patient to evaluate

        Returns:
            List of triggered alerts
        """
        # Fetch patient data (would integrate with patient service)
        patient_data = await self._fetch_patient_data(patient_id)

        if not patient_data:
            logger.warning(f"No data found for patient: {patient_id}")
            return []

        return await self.evaluate_rules(patient_data, patient_id)

    async def _fetch_patient_data(self, patient_id: UUID) -> Optional[Dict[str, Any]]:
        """Fetch patient data for evaluation.

        This would integrate with the patient service to fetch current
        patient data including demographics, vitals, labs, medications, etc.

        Args:
            patient_id: Patient ID

        Returns:
            Patient data dictionary or None
        """
        # Placeholder - would integrate with actual patient service
        # from app.services.patient_service import PatientService
        # patient_service = PatientService(self.db)
        # return patient_service.get_patient_full_record(patient_id)

        logger.info(f"Fetching patient data for: {patient_id}")
        return None

    async def test_rule(self, rule_id: UUID, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test a rule against sample data without triggering alerts.

        Useful for validating rule configurations before enabling.

        Args:
            rule_id: Rule to test
            test_data: Sample data to test against

        Returns:
            Test results with match status and condition details
        """
        from sqlalchemy import select
        result = await self.db.execute(select(AlertRule).filter(AlertRule.id == rule_id))
        rule = result.scalar_one_or_none()

        if not rule:
            return {"error": "Rule not found", "matched": False}

        conditions_config = rule.conditions
        conditions = conditions_config.get("conditions", [])
        match_type = conditions_config.get("match_type", "all")

        # Evaluate each condition individually
        condition_results = []
        for condition in conditions:
            result = self.condition_evaluator.evaluate(condition, test_data)
            condition_results.append({
                "condition": condition,
                "matched": result,
                "actual_value": self.condition_evaluator._get_nested_value(
                    test_data, condition.get("field", "")
                )
            })

        # Determine overall match
        if match_type == "all":
            overall_matched = all(r["matched"] for r in condition_results)
        else:
            overall_matched = any(r["matched"] for r in condition_results)

        return {
            "rule_id": str(rule_id),
            "rule_name": rule.name,
            "matched": overall_matched,
            "match_type": match_type,
            "condition_results": condition_results
        }
