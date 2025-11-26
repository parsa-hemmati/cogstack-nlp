"""Prediction schemas for analytics API."""
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PredictionCreate(BaseModel):
    """Schema for creating a prediction."""

    model_id: UUID
    prediction_type: str
    prediction_result: Dict[str, Any]
    patient_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    input_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    probabilities: Optional[Dict[str, float]] = None
    risk_level: Optional[str] = None
    risk_factors: Optional[List[Dict[str, Any]]] = None
    inference_time_ms: Optional[int] = None


class PredictionExecute(BaseModel):
    """Schema for executing a prediction."""

    input_data: Dict[str, Any]
    patient_id: Optional[UUID] = None
    document_id: Optional[UUID] = None


class PredictionFeedback(BaseModel):
    """Schema for prediction feedback."""

    feedback_status: str = Field(..., description="correct, incorrect, or partial")
    actual_outcome: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class PredictionResponse(BaseModel):
    """Schema for prediction response."""

    id: UUID
    model_id: UUID
    patient_id: Optional[UUID]
    document_id: Optional[UUID]
    prediction_type: str
    prediction_result: Dict[str, Any]
    confidence_score: Optional[float]
    probabilities: Optional[Dict[str, float]]
    risk_level: Optional[str]
    risk_factors: Optional[List[Dict[str, Any]]]
    feedback_status: Optional[str]
    feedback_notes: Optional[str]
    inference_time_ms: Optional[int]
    predicted_at: datetime

    class Config:
        from_attributes = True


class PredictionStatisticsResponse(BaseModel):
    """Schema for prediction statistics."""

    period_days: int
    total_predictions: int
    average_daily: float
    risk_distribution: Dict[str, int]
    type_distribution: Dict[str, int]
    average_confidence: Optional[float]
    average_inference_time_ms: Optional[float]


class PatientRiskSummary(BaseModel):
    """Schema for patient risk summary."""

    patient_id: str
    total_predictions: int
    highest_risk: Optional[str]
    risk_counts: Dict[str, int]
    latest_prediction: Optional[Dict[str, Any]]


class ModelAccuracyResponse(BaseModel):
    """Schema for model accuracy based on feedback."""

    total_with_feedback: int
    accuracy: Optional[float]
    correct: int
    incorrect: int
    partial: int
