"""ML Model schemas for analytics API."""
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ModelCreate(BaseModel):
    """Schema for creating a new ML model."""

    name: str = Field(..., min_length=1, max_length=255)
    model_type: str = Field(..., description="classification, regression, clustering, or nlp")
    version: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    algorithm: Optional[str] = None
    framework: Optional[str] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    feature_columns: Optional[List[str]] = None
    target_column: Optional[str] = None
    preprocessing_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ModelUpdate(BaseModel):
    """Schema for updating an ML model."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    algorithm: Optional[str] = None
    framework: Optional[str] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    feature_columns: Optional[List[str]] = None
    target_column: Optional[str] = None
    preprocessing_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ModelTrainingComplete(BaseModel):
    """Schema for completing model training."""

    model_path: str
    training_metrics: Dict[str, Any]
    validation_metrics: Optional[Dict[str, Any]] = None
    test_metrics: Optional[Dict[str, Any]] = None
    training_samples: Optional[int] = None
    model_size_bytes: Optional[int] = None


class ModelActivate(BaseModel):
    """Schema for activating a model."""

    endpoint_url: Optional[str] = None


class ModelResponse(BaseModel):
    """Schema for model response."""

    id: UUID
    name: str
    description: Optional[str]
    model_type: str
    version: str
    status: str
    algorithm: Optional[str]
    framework: Optional[str]
    hyperparameters: Optional[Dict[str, Any]]
    feature_columns: Optional[List[str]]
    target_column: Optional[str]
    preprocessing_config: Optional[Dict[str, Any]]
    model_path: Optional[str]
    model_size_bytes: Optional[int]
    training_metrics: Optional[Dict[str, Any]]
    validation_metrics: Optional[Dict[str, Any]]
    test_metrics: Optional[Dict[str, Any]]
    training_samples: Optional[int]
    training_started_at: Optional[datetime]
    training_completed_at: Optional[datetime]
    training_duration_seconds: Optional[int]
    deployed_at: Optional[datetime]
    endpoint_url: Optional[str]
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    tags: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class ModelComparisonResponse(BaseModel):
    """Schema for model comparison response."""

    models: Dict[str, Dict[str, Any]]


class ModelStatisticsResponse(BaseModel):
    """Schema for model statistics response."""

    total_models: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    active_count: int
