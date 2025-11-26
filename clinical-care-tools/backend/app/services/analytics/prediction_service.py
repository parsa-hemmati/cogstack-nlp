"""PredictionService for executing predictions and tracking feedback."""
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.analytics.ml_model import AnalyticsModel, ModelPrediction

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for executing predictions and managing feedback.

    Handles prediction execution, result storage, and feedback collection.
    """

    def __init__(self, db: Session):
        """Initialize prediction service.

        Args:
            db: Database session
        """
        self.db = db

    def create_prediction(
        self,
        model_id: UUID,
        prediction_type: str,
        prediction_result: Dict[str, Any],
        patient_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        input_data: Optional[Dict[str, Any]] = None,
        confidence_score: Optional[float] = None,
        probabilities: Optional[Dict[str, float]] = None,
        risk_level: Optional[str] = None,
        risk_factors: Optional[List[Dict[str, Any]]] = None,
        inference_time_ms: Optional[int] = None
    ) -> ModelPrediction:
        """Create a new prediction record.

        Args:
            model_id: Model that made the prediction
            prediction_type: Type of prediction
            prediction_result: The prediction output
            patient_id: Optional patient context
            document_id: Optional document context
            input_data: Sanitized input features
            confidence_score: Prediction confidence
            probabilities: Class probabilities
            risk_level: Risk level for risk predictions
            risk_factors: Contributing risk factors
            inference_time_ms: Time to generate prediction

        Returns:
            Created ModelPrediction
        """
        prediction = ModelPrediction(
            model_id=model_id,
            prediction_type=prediction_type,
            prediction_result=prediction_result,
            patient_id=patient_id,
            document_id=document_id,
            input_data=input_data,
            confidence_score=confidence_score,
            probabilities=probabilities,
            risk_level=risk_level,
            risk_factors=risk_factors,
            inference_time_ms=inference_time_ms
        )

        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)

        logger.debug(f"Created prediction for model {model_id}: {prediction_type}")
        return prediction

    def execute_prediction(
        self,
        model: AnalyticsModel,
        input_data: Dict[str, Any],
        patient_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None
    ) -> ModelPrediction:
        """Execute a prediction using a loaded model.

        Args:
            model: The model to use
            input_data: Input features
            patient_id: Optional patient context
            document_id: Optional document context

        Returns:
            ModelPrediction with results
        """
        start_time = time.time()

        # Placeholder - would load and execute actual model
        # In production, this would:
        # 1. Load model artifact
        # 2. Preprocess input data
        # 3. Execute prediction
        # 4. Post-process output

        prediction_result = {
            "predicted_class": "positive",
            "raw_output": 0.75
        }
        confidence_score = 0.75
        probabilities = {"positive": 0.75, "negative": 0.25}

        inference_time_ms = int((time.time() - start_time) * 1000)

        # Determine risk level for risk predictions
        risk_level = None
        risk_factors = None
        if model.model_type == AnalyticsModel.TYPE_CLASSIFICATION:
            if confidence_score >= 0.8:
                risk_level = ModelPrediction.RISK_HIGH
            elif confidence_score >= 0.6:
                risk_level = ModelPrediction.RISK_MEDIUM
            else:
                risk_level = ModelPrediction.RISK_LOW

            # Extract risk factors (would be model-specific)
            risk_factors = [
                {"factor": "sample_factor", "contribution": 0.3}
            ]

        return self.create_prediction(
            model_id=model.id,
            prediction_type=ModelPrediction.TYPE_CLASSIFICATION,
            prediction_result=prediction_result,
            patient_id=patient_id,
            document_id=document_id,
            input_data=self._sanitize_input(input_data),
            confidence_score=confidence_score,
            probabilities=probabilities,
            risk_level=risk_level,
            risk_factors=risk_factors,
            inference_time_ms=inference_time_ms
        )

    def _sanitize_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data to remove PHI before storage.

        Args:
            input_data: Raw input data

        Returns:
            Sanitized input (feature values only)
        """
        # In production, would remove or hash PHI fields
        sensitive_fields = ["name", "dob", "ssn", "mrn", "address", "phone", "email"]
        return {k: v for k, v in input_data.items() if k.lower() not in sensitive_fields}

    def get_prediction(self, prediction_id: UUID) -> Optional[ModelPrediction]:
        """Get a prediction by ID.

        Args:
            prediction_id: Prediction ID

        Returns:
            ModelPrediction or None
        """
        return self.db.query(ModelPrediction).filter(
            ModelPrediction.id == prediction_id
        ).first()

    def list_predictions(
        self,
        model_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        prediction_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        feedback_status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ModelPrediction]:
        """List predictions with optional filtering.

        Args:
            model_id: Filter by model
            patient_id: Filter by patient
            document_id: Filter by document
            prediction_type: Filter by type
            risk_level: Filter by risk level
            feedback_status: Filter by feedback status
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of ModelPrediction objects
        """
        query = self.db.query(ModelPrediction)

        if model_id:
            query = query.filter(ModelPrediction.model_id == model_id)
        if patient_id:
            query = query.filter(ModelPrediction.patient_id == patient_id)
        if document_id:
            query = query.filter(ModelPrediction.document_id == document_id)
        if prediction_type:
            query = query.filter(ModelPrediction.prediction_type == prediction_type)
        if risk_level:
            query = query.filter(ModelPrediction.risk_level == risk_level)
        if feedback_status:
            query = query.filter(ModelPrediction.feedback_status == feedback_status)
        if start_date:
            query = query.filter(ModelPrediction.predicted_at >= start_date)
        if end_date:
            query = query.filter(ModelPrediction.predicted_at <= end_date)

        return query.order_by(
            ModelPrediction.predicted_at.desc()
        ).offset(offset).limit(limit).all()

    def get_high_risk_predictions(
        self,
        model_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[ModelPrediction]:
        """Get high and critical risk predictions.

        Args:
            model_id: Optional filter by model
            limit: Maximum results

        Returns:
            List of high-risk predictions
        """
        query = self.db.query(ModelPrediction).filter(
            ModelPrediction.risk_level.in_([
                ModelPrediction.RISK_HIGH,
                ModelPrediction.RISK_CRITICAL
            ])
        )

        if model_id:
            query = query.filter(ModelPrediction.model_id == model_id)

        return query.order_by(
            ModelPrediction.predicted_at.desc()
        ).limit(limit).all()

    def add_feedback(
        self,
        prediction_id: UUID,
        feedback_by: UUID,
        feedback_status: str,
        actual_outcome: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> Optional[ModelPrediction]:
        """Add feedback to a prediction.

        Args:
            prediction_id: Prediction to update
            feedback_by: User providing feedback
            feedback_status: Feedback status
            actual_outcome: Actual outcome if known
            notes: Additional notes

        Returns:
            Updated prediction or None
        """
        prediction = self.get_prediction(prediction_id)
        if not prediction:
            return None

        prediction.add_feedback(
            feedback_by=feedback_by,
            feedback_status=feedback_status,
            actual_outcome=actual_outcome,
            notes=notes
        )

        self.db.commit()
        self.db.refresh(prediction)

        logger.info(f"Added feedback to prediction {prediction_id}: {feedback_status}")
        return prediction

    def get_predictions_needing_feedback(
        self,
        model_id: Optional[UUID] = None,
        days_old: int = 7,
        limit: int = 50
    ) -> List[ModelPrediction]:
        """Get predictions that need feedback.

        Args:
            model_id: Optional filter by model
            days_old: Minimum age in days
            limit: Maximum results

        Returns:
            List of predictions needing feedback
        """
        cutoff = datetime.utcnow() - timedelta(days=days_old)

        query = self.db.query(ModelPrediction).filter(
            and_(
                ModelPrediction.feedback_status.is_(None),
                ModelPrediction.predicted_at < cutoff
            )
        )

        if model_id:
            query = query.filter(ModelPrediction.model_id == model_id)

        return query.order_by(
            ModelPrediction.predicted_at
        ).limit(limit).all()

    def calculate_model_accuracy(
        self,
        model_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculate accuracy metrics for a model based on feedback.

        Args:
            model_id: Model to analyze
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Accuracy metrics
        """
        query = self.db.query(ModelPrediction).filter(
            ModelPrediction.model_id == model_id,
            ModelPrediction.feedback_status.isnot(None)
        )

        if start_date:
            query = query.filter(ModelPrediction.predicted_at >= start_date)
        if end_date:
            query = query.filter(ModelPrediction.predicted_at <= end_date)

        predictions = query.all()

        if not predictions:
            return {
                "total_with_feedback": 0,
                "accuracy": None,
                "correct": 0,
                "incorrect": 0,
                "partial": 0
            }

        correct = sum(1 for p in predictions if p.feedback_status == ModelPrediction.FEEDBACK_CORRECT)
        incorrect = sum(1 for p in predictions if p.feedback_status == ModelPrediction.FEEDBACK_INCORRECT)
        partial = sum(1 for p in predictions if p.feedback_status == ModelPrediction.FEEDBACK_PARTIAL)

        total = len(predictions)
        accuracy = (correct + (partial * 0.5)) / total * 100 if total > 0 else None

        return {
            "total_with_feedback": total,
            "accuracy": round(accuracy, 2) if accuracy else None,
            "correct": correct,
            "incorrect": incorrect,
            "partial": partial
        }

    def get_prediction_statistics(
        self,
        model_id: Optional[UUID] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get prediction statistics for a time period.

        Args:
            model_id: Optional filter by model
            days: Number of days to analyze

        Returns:
            Statistics dictionary
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(ModelPrediction).filter(
            ModelPrediction.predicted_at >= start_date
        )

        if model_id:
            query = query.filter(ModelPrediction.model_id == model_id)

        total = query.count()

        # Risk level distribution
        risk_distribution = self.db.query(
            ModelPrediction.risk_level,
            func.count(ModelPrediction.id)
        ).filter(
            ModelPrediction.predicted_at >= start_date,
            ModelPrediction.risk_level.isnot(None)
        )

        if model_id:
            risk_distribution = risk_distribution.filter(ModelPrediction.model_id == model_id)

        risk_distribution = risk_distribution.group_by(
            ModelPrediction.risk_level
        ).all()

        # Prediction type distribution
        type_distribution = self.db.query(
            ModelPrediction.prediction_type,
            func.count(ModelPrediction.id)
        ).filter(
            ModelPrediction.predicted_at >= start_date
        )

        if model_id:
            type_distribution = type_distribution.filter(ModelPrediction.model_id == model_id)

        type_distribution = type_distribution.group_by(
            ModelPrediction.prediction_type
        ).all()

        # Average confidence and inference time
        avg_stats = self.db.query(
            func.avg(ModelPrediction.confidence_score),
            func.avg(ModelPrediction.inference_time_ms)
        ).filter(
            ModelPrediction.predicted_at >= start_date
        )

        if model_id:
            avg_stats = avg_stats.filter(ModelPrediction.model_id == model_id)

        avg_confidence, avg_inference_time = avg_stats.first()

        return {
            "period_days": days,
            "total_predictions": total,
            "average_daily": round(total / days, 1) if days > 0 else 0,
            "risk_distribution": {level: count for level, count in risk_distribution if level},
            "type_distribution": {ptype: count for ptype, count in type_distribution},
            "average_confidence": round(avg_confidence, 3) if avg_confidence else None,
            "average_inference_time_ms": round(avg_inference_time, 1) if avg_inference_time else None
        }

    def get_patient_predictions(
        self,
        patient_id: UUID,
        limit: int = 20
    ) -> List[ModelPrediction]:
        """Get all predictions for a patient.

        Args:
            patient_id: Patient ID
            limit: Maximum results

        Returns:
            List of predictions for the patient
        """
        return self.db.query(ModelPrediction).filter(
            ModelPrediction.patient_id == patient_id
        ).order_by(
            ModelPrediction.predicted_at.desc()
        ).limit(limit).all()

    def get_patient_risk_summary(self, patient_id: UUID) -> Dict[str, Any]:
        """Get risk summary for a patient across all models.

        Args:
            patient_id: Patient ID

        Returns:
            Risk summary dictionary
        """
        predictions = self.db.query(ModelPrediction).filter(
            ModelPrediction.patient_id == patient_id,
            ModelPrediction.risk_level.isnot(None)
        ).order_by(
            ModelPrediction.predicted_at.desc()
        ).limit(100).all()

        if not predictions:
            return {
                "patient_id": str(patient_id),
                "total_predictions": 0,
                "highest_risk": None,
                "risk_counts": {}
            }

        risk_counts = {}
        for p in predictions:
            risk_counts[p.risk_level] = risk_counts.get(p.risk_level, 0) + 1

        # Determine highest risk level
        risk_priority = {
            ModelPrediction.RISK_CRITICAL: 4,
            ModelPrediction.RISK_HIGH: 3,
            ModelPrediction.RISK_MEDIUM: 2,
            ModelPrediction.RISK_LOW: 1
        }

        highest_risk = max(risk_counts.keys(), key=lambda x: risk_priority.get(x, 0))
        latest_prediction = predictions[0] if predictions else None

        return {
            "patient_id": str(patient_id),
            "total_predictions": len(predictions),
            "highest_risk": highest_risk,
            "risk_counts": risk_counts,
            "latest_prediction": latest_prediction.to_dict() if latest_prediction else None
        }

    def delete_old_predictions(self, days: int = 365) -> int:
        """Delete predictions older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of predictions deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        count = self.db.query(ModelPrediction).filter(
            ModelPrediction.predicted_at < cutoff
        ).delete()

        self.db.commit()

        logger.info(f"Deleted {count} predictions older than {days} days")
        return count
