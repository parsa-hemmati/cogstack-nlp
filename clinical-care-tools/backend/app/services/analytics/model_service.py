"""ModelService for ML model management and versioning."""
import logging
import os
import pickle
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.analytics.ml_model import AnalyticsModel, ModelPrediction

logger = logging.getLogger(__name__)


class ModelService:
    """Service for managing ML models in the analytics system.

    Handles model CRUD, versioning, training lifecycle, and deployment.
    """

    MODEL_STORAGE_DIR = "models"  # Would be configured from settings

    def __init__(self, db: Session):
        """Initialize model service.

        Args:
            db: Database session
        """
        self.db = db

    def create_model(
        self,
        name: str,
        model_type: str,
        version: str,
        created_by: UUID,
        description: Optional[str] = None,
        algorithm: Optional[str] = None,
        framework: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        feature_columns: Optional[List[str]] = None,
        target_column: Optional[str] = None,
        preprocessing_config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalyticsModel:
        """Create a new ML model entry.

        Args:
            name: Model name
            model_type: Type of model (classification, regression, etc.)
            version: Model version string
            created_by: User creating the model
            description: Model description
            algorithm: Algorithm used
            framework: ML framework
            hyperparameters: Model hyperparameters
            feature_columns: Input feature columns
            target_column: Target column name
            preprocessing_config: Preprocessing configuration
            tags: Tags for organization
            metadata: Additional metadata

        Returns:
            Created AnalyticsModel
        """
        model = AnalyticsModel(
            name=name,
            model_type=model_type,
            version=version,
            created_by=created_by,
            description=description,
            algorithm=algorithm,
            framework=framework,
            hyperparameters=hyperparameters,
            feature_columns=feature_columns,
            target_column=target_column,
            preprocessing_config=preprocessing_config,
            tags=tags,
            metadata=metadata
        )

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Created model: {name} v{version} (id={model.id})")
        return model

    def get_model(self, model_id: UUID) -> Optional[AnalyticsModel]:
        """Get a model by ID.

        Args:
            model_id: Model ID

        Returns:
            AnalyticsModel or None
        """
        return self.db.query(AnalyticsModel).filter(
            AnalyticsModel.id == model_id
        ).first()

    def get_model_by_name_version(
        self,
        name: str,
        version: str
    ) -> Optional[AnalyticsModel]:
        """Get a model by name and version.

        Args:
            name: Model name
            version: Model version

        Returns:
            AnalyticsModel or None
        """
        return self.db.query(AnalyticsModel).filter(
            AnalyticsModel.name == name,
            AnalyticsModel.version == version
        ).first()

    def list_models(
        self,
        model_type: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AnalyticsModel]:
        """List models with optional filtering.

        Args:
            model_type: Filter by model type
            status: Filter by status
            created_by: Filter by creator
            tags: Filter by tags (any match)
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of AnalyticsModel objects
        """
        query = self.db.query(AnalyticsModel)

        if model_type:
            query = query.filter(AnalyticsModel.model_type == model_type)
        if status:
            query = query.filter(AnalyticsModel.status == status)
        if created_by:
            query = query.filter(AnalyticsModel.created_by == created_by)
        if tags:
            query = query.filter(AnalyticsModel.tags.overlap(tags))

        return query.order_by(
            AnalyticsModel.created_at.desc()
        ).offset(offset).limit(limit).all()

    def get_active_models(self, model_type: Optional[str] = None) -> List[AnalyticsModel]:
        """Get all active (deployed) models.

        Args:
            model_type: Optional filter by type

        Returns:
            List of active models
        """
        query = self.db.query(AnalyticsModel).filter(
            AnalyticsModel.status == AnalyticsModel.STATUS_ACTIVE
        )

        if model_type:
            query = query.filter(AnalyticsModel.model_type == model_type)

        return query.order_by(AnalyticsModel.deployed_at.desc()).all()

    def get_latest_version(self, name: str) -> Optional[AnalyticsModel]:
        """Get the latest version of a model by name.

        Args:
            name: Model name

        Returns:
            Latest AnalyticsModel or None
        """
        return self.db.query(AnalyticsModel).filter(
            AnalyticsModel.name == name
        ).order_by(
            AnalyticsModel.created_at.desc()
        ).first()

    def update_model(
        self,
        model_id: UUID,
        updated_by: UUID,
        **updates
    ) -> Optional[AnalyticsModel]:
        """Update a model.

        Args:
            model_id: Model to update
            updated_by: User making the update
            **updates: Fields to update

        Returns:
            Updated model or None
        """
        model = self.get_model(model_id)
        if not model:
            return None

        allowed_fields = [
            "name", "description", "algorithm", "framework",
            "hyperparameters", "feature_columns", "target_column",
            "preprocessing_config", "tags", "metadata"
        ]

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(model, field, value)

        model.updated_by = updated_by
        self.db.commit()
        self.db.refresh(model)

        return model

    def start_training(self, model_id: UUID) -> Optional[AnalyticsModel]:
        """Mark a model as training.

        Args:
            model_id: Model to start training

        Returns:
            Updated model or None
        """
        model = self.get_model(model_id)
        if not model:
            return None

        model.start_training()
        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Started training for model: {model.name} (id={model_id})")
        return model

    def complete_training(
        self,
        model_id: UUID,
        model_path: str,
        training_metrics: Dict[str, Any],
        validation_metrics: Optional[Dict[str, Any]] = None,
        test_metrics: Optional[Dict[str, Any]] = None,
        training_samples: Optional[int] = None,
        model_size_bytes: Optional[int] = None
    ) -> Optional[AnalyticsModel]:
        """Mark training as complete with metrics.

        Args:
            model_id: Model ID
            model_path: Path to saved model
            training_metrics: Training performance metrics
            validation_metrics: Validation performance metrics
            test_metrics: Test performance metrics
            training_samples: Number of training samples
            model_size_bytes: Size of model file

        Returns:
            Updated model or None
        """
        model = self.get_model(model_id)
        if not model:
            return None

        model.complete_training(
            model_path=model_path,
            training_metrics=training_metrics,
            validation_metrics=validation_metrics,
            model_size_bytes=model_size_bytes
        )

        if test_metrics:
            model.test_metrics = test_metrics
        if training_samples:
            model.training_samples = training_samples

        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Completed training for model: {model.name} (id={model_id})")
        return model

    def activate_model(
        self,
        model_id: UUID,
        deployed_by: UUID,
        endpoint_url: Optional[str] = None
    ) -> Optional[AnalyticsModel]:
        """Activate a model for production use.

        Args:
            model_id: Model to activate
            deployed_by: User activating the model
            endpoint_url: Optional API endpoint

        Returns:
            Activated model or None
        """
        model = self.get_model(model_id)
        if not model:
            return None

        # Deprecate previous active versions of same model name
        self.db.query(AnalyticsModel).filter(
            AnalyticsModel.name == model.name,
            AnalyticsModel.status == AnalyticsModel.STATUS_ACTIVE,
            AnalyticsModel.id != model_id
        ).update({"status": AnalyticsModel.STATUS_DEPRECATED})

        model.activate(deployed_by, endpoint_url)
        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Activated model: {model.name} v{model.version} (id={model_id})")
        return model

    def deprecate_model(self, model_id: UUID) -> Optional[AnalyticsModel]:
        """Deprecate a model.

        Args:
            model_id: Model to deprecate

        Returns:
            Deprecated model or None
        """
        model = self.get_model(model_id)
        if not model:
            return None

        model.deprecate()
        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Deprecated model: {model.name} (id={model_id})")
        return model

    def archive_model(self, model_id: UUID) -> Optional[AnalyticsModel]:
        """Archive a model.

        Args:
            model_id: Model to archive

        Returns:
            Archived model or None
        """
        model = self.get_model(model_id)
        if not model:
            return None

        model.archive()
        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Archived model: {model.name} (id={model_id})")
        return model

    def delete_model(self, model_id: UUID) -> bool:
        """Delete a model and its predictions.

        Args:
            model_id: Model to delete

        Returns:
            True if deleted
        """
        model = self.get_model(model_id)
        if not model:
            return False

        # Delete model file if exists
        if model.model_path and os.path.exists(model.model_path):
            try:
                os.remove(model.model_path)
            except OSError as e:
                logger.warning(f"Failed to delete model file: {e}")

        self.db.delete(model)
        self.db.commit()

        logger.info(f"Deleted model: {model.name} (id={model_id})")
        return True

    def get_model_versions(self, name: str) -> List[AnalyticsModel]:
        """Get all versions of a model by name.

        Args:
            name: Model name

        Returns:
            List of model versions
        """
        return self.db.query(AnalyticsModel).filter(
            AnalyticsModel.name == name
        ).order_by(
            AnalyticsModel.created_at.desc()
        ).all()

    def compare_models(
        self,
        model_ids: List[UUID]
    ) -> Dict[str, Dict[str, Any]]:
        """Compare performance metrics across models.

        Args:
            model_ids: Models to compare

        Returns:
            Comparison data by model
        """
        result = {}

        for model_id in model_ids:
            model = self.get_model(model_id)
            if not model:
                continue

            result[str(model_id)] = {
                "name": model.name,
                "version": model.version,
                "status": model.status,
                "algorithm": model.algorithm,
                "training_metrics": model.training_metrics,
                "validation_metrics": model.validation_metrics,
                "test_metrics": model.test_metrics,
                "training_samples": model.training_samples,
                "training_duration_seconds": model.training_duration_seconds,
                "primary_metric": model.get_primary_metric()
            }

        return result

    def get_model_statistics(self) -> Dict[str, Any]:
        """Get overall model statistics.

        Returns:
            Statistics dictionary
        """
        total = self.db.query(func.count(AnalyticsModel.id)).scalar() or 0

        by_status = self.db.query(
            AnalyticsModel.status,
            func.count(AnalyticsModel.id)
        ).group_by(AnalyticsModel.status).all()

        by_type = self.db.query(
            AnalyticsModel.model_type,
            func.count(AnalyticsModel.id)
        ).group_by(AnalyticsModel.model_type).all()

        return {
            "total_models": total,
            "by_status": {status: count for status, count in by_status},
            "by_type": {model_type: count for model_type, count in by_type},
            "active_count": dict(by_status).get(AnalyticsModel.STATUS_ACTIVE, 0)
        }

    def load_model_artifact(self, model_id: UUID) -> Optional[Any]:
        """Load the serialized model artifact.

        Args:
            model_id: Model to load

        Returns:
            Deserialized model or None
        """
        model = self.get_model(model_id)
        if not model or not model.model_path:
            return None

        if not os.path.exists(model.model_path):
            logger.error(f"Model file not found: {model.model_path}")
            return None

        try:
            with open(model.model_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load model artifact: {e}")
            return None

    def save_model_artifact(
        self,
        model_id: UUID,
        artifact: Any
    ) -> Optional[str]:
        """Save a model artifact to storage.

        Args:
            model_id: Model ID
            artifact: Model object to save

        Returns:
            File path or None
        """
        model = self.get_model(model_id)
        if not model:
            return None

        os.makedirs(self.MODEL_STORAGE_DIR, exist_ok=True)
        file_path = f"{self.MODEL_STORAGE_DIR}/{model_id}.pkl"

        try:
            with open(file_path, 'wb') as f:
                pickle.dump(artifact, f)

            model.model_path = file_path
            model.model_size_bytes = os.path.getsize(file_path)
            self.db.commit()

            logger.info(f"Saved model artifact: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to save model artifact: {e}")
            return None
