"""ML Model and Prediction models for analytics."""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey, BigInteger
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.core.database import Base

logger = logging.getLogger(__name__)


class AnalyticsModel(Base):
    """ML model registry for tracking trained models.

    Stores model metadata, training configuration, performance metrics,
    and deployment information.
    """

    __tablename__ = "analytics_models"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    model_type = Column(String(50), nullable=False)  # classification, regression, clustering, nlp
    version = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, server_default='draft')
    algorithm = Column(String(100), nullable=True)
    framework = Column(String(50), nullable=True)

    # Model configuration
    hyperparameters = Column(JSONB, nullable=True)
    feature_columns = Column(ARRAY(String), nullable=True)
    target_column = Column(String(100), nullable=True)
    preprocessing_config = Column(JSONB, nullable=True)

    # Model storage
    model_path = Column(String(500), nullable=True)
    model_size_bytes = Column(BigInteger, nullable=True)

    # Performance metrics
    training_metrics = Column(JSONB, nullable=True)
    validation_metrics = Column(JSONB, nullable=True)
    test_metrics = Column(JSONB, nullable=True)

    # Training information
    training_dataset_id = Column(PG_UUID(as_uuid=True), nullable=True)
    training_samples = Column(Integer, nullable=True)
    training_started_at = Column(DateTime(timezone=True), nullable=True)
    training_completed_at = Column(DateTime(timezone=True), nullable=True)
    training_duration_seconds = Column(Integer, nullable=True)

    # Deployment info
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    deployed_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    endpoint_url = Column(String(500), nullable=True)

    # Audit
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    updated_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Metadata
    tags = Column(ARRAY(String), nullable=True)
    metadata = Column(JSONB, nullable=True)

    # Relationships
    predictions = relationship("ModelPrediction", back_populates="model", lazy="dynamic")

    # Status constants
    STATUS_DRAFT = "draft"
    STATUS_TRAINING = "training"
    STATUS_ACTIVE = "active"
    STATUS_DEPRECATED = "deprecated"
    STATUS_ARCHIVED = "archived"

    # Type constants
    TYPE_CLASSIFICATION = "classification"
    TYPE_REGRESSION = "regression"
    TYPE_CLUSTERING = "clustering"
    TYPE_NLP = "nlp"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "model_type": self.model_type,
            "version": self.version,
            "status": self.status,
            "algorithm": self.algorithm,
            "framework": self.framework,
            "hyperparameters": self.hyperparameters,
            "feature_columns": self.feature_columns,
            "target_column": self.target_column,
            "preprocessing_config": self.preprocessing_config,
            "model_path": self.model_path,
            "model_size_bytes": self.model_size_bytes,
            "training_metrics": self.training_metrics,
            "validation_metrics": self.validation_metrics,
            "test_metrics": self.test_metrics,
            "training_samples": self.training_samples,
            "training_started_at": self.training_started_at.isoformat() if self.training_started_at else None,
            "training_completed_at": self.training_completed_at.isoformat() if self.training_completed_at else None,
            "training_duration_seconds": self.training_duration_seconds,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "endpoint_url": self.endpoint_url,
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    def start_training(self) -> None:
        """Mark model as training."""
        self.status = self.STATUS_TRAINING
        self.training_started_at = datetime.utcnow()

    def complete_training(
        self,
        model_path: str,
        training_metrics: Dict[str, Any],
        validation_metrics: Optional[Dict[str, Any]] = None,
        model_size_bytes: Optional[int] = None
    ) -> None:
        """Mark training as complete with metrics."""
        self.status = self.STATUS_DRAFT  # Ready for review
        self.training_completed_at = datetime.utcnow()
        self.model_path = model_path
        self.training_metrics = training_metrics
        self.validation_metrics = validation_metrics
        self.model_size_bytes = model_size_bytes

        if self.training_started_at:
            duration = self.training_completed_at - self.training_started_at
            self.training_duration_seconds = int(duration.total_seconds())

    def activate(self, deployed_by: UUID, endpoint_url: Optional[str] = None) -> None:
        """Activate model for production use."""
        self.status = self.STATUS_ACTIVE
        self.deployed_at = datetime.utcnow()
        self.deployed_by = deployed_by
        self.endpoint_url = endpoint_url

    def deprecate(self) -> None:
        """Mark model as deprecated."""
        self.status = self.STATUS_DEPRECATED

    def archive(self) -> None:
        """Archive the model."""
        self.status = self.STATUS_ARCHIVED

    def get_primary_metric(self) -> Optional[float]:
        """Get the primary performance metric based on model type."""
        if not self.validation_metrics and not self.test_metrics:
            return None

        metrics = self.test_metrics or self.validation_metrics

        if self.model_type == self.TYPE_CLASSIFICATION:
            return metrics.get("f1_score") or metrics.get("accuracy")
        elif self.model_type == self.TYPE_REGRESSION:
            return metrics.get("r2_score") or metrics.get("rmse")
        elif self.model_type == self.TYPE_NLP:
            return metrics.get("f1_score") or metrics.get("accuracy")
        else:
            return metrics.get("score")


class ModelPrediction(Base):
    """Individual prediction record from a model.

    Tracks predictions, confidence scores, and feedback for model improvement.
    """

    __tablename__ = "model_predictions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    model_id = Column(PG_UUID(as_uuid=True), ForeignKey('analytics_models.id', ondelete='CASCADE'), nullable=False)
    patient_id = Column(PG_UUID(as_uuid=True), ForeignKey('patients.id', ondelete='SET NULL'), nullable=True)
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey('documents.id', ondelete='SET NULL'), nullable=True)

    # Prediction details
    prediction_type = Column(String(50), nullable=False)
    input_data = Column(JSONB, nullable=True)
    prediction_result = Column(JSONB, nullable=False)
    confidence_score = Column(Float, nullable=True)
    probabilities = Column(JSONB, nullable=True)

    # Risk predictions specific
    risk_level = Column(String(20), nullable=True)
    risk_factors = Column(JSONB, nullable=True)

    # Feedback and validation
    actual_outcome = Column(JSONB, nullable=True)
    feedback_status = Column(String(20), nullable=True)
    feedback_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    feedback_at = Column(DateTime(timezone=True), nullable=True)
    feedback_notes = Column(Text, nullable=True)

    # Performance
    inference_time_ms = Column(Integer, nullable=True)

    # Timestamps
    predicted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    model = relationship("AnalyticsModel", back_populates="predictions")

    # Type constants
    TYPE_RISK_SCORE = "risk_score"
    TYPE_CLASSIFICATION = "classification"
    TYPE_ENTITY_EXTRACTION = "entity_extraction"
    TYPE_SIMILARITY = "similarity"

    # Risk level constants
    RISK_LOW = "low"
    RISK_MEDIUM = "medium"
    RISK_HIGH = "high"
    RISK_CRITICAL = "critical"

    # Feedback status constants
    FEEDBACK_PENDING = "pending"
    FEEDBACK_CORRECT = "correct"
    FEEDBACK_INCORRECT = "incorrect"
    FEEDBACK_PARTIAL = "partial"

    def to_dict(self) -> Dict[str, Any]:
        """Convert prediction to dictionary."""
        return {
            "id": str(self.id),
            "model_id": str(self.model_id),
            "patient_id": str(self.patient_id) if self.patient_id else None,
            "document_id": str(self.document_id) if self.document_id else None,
            "prediction_type": self.prediction_type,
            "prediction_result": self.prediction_result,
            "confidence_score": self.confidence_score,
            "probabilities": self.probabilities,
            "risk_level": self.risk_level,
            "risk_factors": self.risk_factors,
            "feedback_status": self.feedback_status,
            "feedback_notes": self.feedback_notes,
            "inference_time_ms": self.inference_time_ms,
            "predicted_at": self.predicted_at.isoformat() if self.predicted_at else None,
        }

    def add_feedback(
        self,
        feedback_by: UUID,
        feedback_status: str,
        actual_outcome: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> None:
        """Record feedback on prediction accuracy."""
        self.feedback_by = feedback_by
        self.feedback_status = feedback_status
        self.actual_outcome = actual_outcome
        self.feedback_notes = notes
        self.feedback_at = datetime.utcnow()

    def is_high_risk(self) -> bool:
        """Check if this is a high-risk prediction."""
        return self.risk_level in [self.RISK_HIGH, self.RISK_CRITICAL]

    def is_accurate(self) -> Optional[bool]:
        """Check if prediction was accurate based on feedback."""
        if self.feedback_status == self.FEEDBACK_CORRECT:
            return True
        elif self.feedback_status == self.FEEDBACK_INCORRECT:
            return False
        return None

    @classmethod
    def create_risk_prediction(
        cls,
        model_id: UUID,
        prediction_result: Dict[str, Any],
        risk_level: str,
        patient_id: Optional[UUID] = None,
        confidence_score: Optional[float] = None,
        risk_factors: Optional[List[Dict[str, Any]]] = None,
        inference_time_ms: Optional[int] = None
    ) -> "ModelPrediction":
        """Factory method for creating risk predictions."""
        return cls(
            model_id=model_id,
            patient_id=patient_id,
            prediction_type=cls.TYPE_RISK_SCORE,
            prediction_result=prediction_result,
            confidence_score=confidence_score,
            risk_level=risk_level,
            risk_factors=risk_factors,
            inference_time_ms=inference_time_ms
        )
