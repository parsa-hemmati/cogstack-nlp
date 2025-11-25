#!/usr/bin/env python3
"""
Evaluate MedCAT PHI Detection Model.

This script evaluates a fine-tuned MedCAT PHI detection model on the
i2b2 2014 test set and generates performance metrics.

Metrics Calculated:
- Overall: Precision, Recall, F1 Score, Accuracy
- Per-Category: Precision, Recall, F1 for each of 18 HIPAA identifiers
- Confusion Matrix
- Error Analysis (false positives/negatives)

Usage:
    python scripts/ml/evaluate_phi_model.py \
        --model /models/medcat_phi_v1.0.model \
        --test-data /path/to/i2b2_2014/test \
        --output-dir /reports/evaluation

Requirements:
    1. Trained PHI detection model
    2. i2b2 2014 test set (195 notes)
    3. MedCAT library
"""
import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

# MedCAT imports (will be available after Phase 3 MedCAT installation)
try:
    from medcat.cat import CAT
except ImportError:
    print(
        "⚠️  MedCAT not installed. Install with: pip install medcat\n"
        "   This is expected during scaffolding phase."
    )

    class CAT:
        pass


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 18 HIPAA Safe Harbor Identifiers
PHI_CATEGORIES = [
    "NAME",
    "LOCATION",
    "DATE",
    "PHONE",
    "FAX",
    "EMAIL",
    "NHS_NUMBER",
    "MRN",
    "HEALTH_PLAN_ID",
    "ACCOUNT_NUMBER",
    "CERTIFICATE_NUMBER",
    "VEHICLE_ID",
    "DEVICE_ID",
    "URL",
    "IP_ADDRESS",
    "BIOMETRIC_ID",
    "PHOTO_METADATA",
    "UNIQUE_ID",
]


class PHIEvaluator:
    """
    Evaluator for PHI detection model performance.

    Calculates metrics, generates reports, and analyzes errors.
    """

    def __init__(self, model_path: str, test_data_dir: str, output_dir: str):
        """
        Initialize evaluator.

        Args:
            model_path: Path to trained MedCAT model
            test_data_dir: Path to i2b2 test set
            output_dir: Path to save evaluation results
        """
        self.model_path = model_path
        self.test_data_dir = Path(test_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load model
        logger.info(f"Loading model from {model_path}")
        # TODO: Load MedCAT model
        # self.model = CAT.load_model_pack(model_path)
        logger.warning("⚠️  Model loading not implemented - requires trained model")

        # Load test data
        self.test_samples = self._load_test_data()
        logger.info(f"Loaded {len(self.test_samples)} test samples")

        # Metrics storage
        self.predictions = []
        self.ground_truth = []

    def _load_test_data(self) -> List[Dict]:
        """
        Load test set annotations.

        Returns:
            List of test samples with text and ground truth entities
        """
        # TODO: Load i2b2 test set
        logger.warning("⚠️  _load_test_data() not implemented - requires i2b2 dataset")
        return []

    def predict(self, text: str) -> List[Dict]:
        """
        Run PHI detection on text.

        Args:
            text: Clinical text

        Returns:
            List of detected PHI entities
        """
        # TODO: Run model inference
        # entities = self.model.get_entities(text)
        # return [e for e in entities if self._is_phi_entity(e)]
        return []

    def evaluate(self) -> Dict:
        """
        Evaluate model on test set.

        Returns:
            Dictionary of evaluation metrics
        """
        logger.info("Running evaluation on test set...")

        # Predict on test set
        for sample in self.test_samples:
            text = sample["text"]
            ground_truth_entities = sample["entities"]

            # Predict
            predicted_entities = self.predict(text)

            # Store for metrics calculation
            self.predictions.append(predicted_entities)
            self.ground_truth.append(ground_truth_entities)

        # Calculate metrics
        metrics = {
            "overall": self._calculate_overall_metrics(),
            "per_category": self._calculate_per_category_metrics(),
            "confusion_matrix": self._generate_confusion_matrix(),
            "error_analysis": self._analyze_errors(),
            "performance": self._benchmark_performance(),
        }

        # Save metrics
        self._save_metrics(metrics)

        # Generate visualizations
        self._generate_visualizations(metrics)

        return metrics

    def _calculate_overall_metrics(self) -> Dict:
        """
        Calculate overall precision, recall, F1 score.

        Returns:
            Dictionary with overall metrics
        """
        # TODO: Implement metrics calculation
        logger.info("Calculating overall metrics...")

        # Placeholder values (replace after implementation)
        metrics = {
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "accuracy": 0.0,
            "total_predictions": 0,
            "total_ground_truth": 0,
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
        }

        logger.info(
            f"Overall Metrics: Precision={metrics['precision']:.3f}, "
            f"Recall={metrics['recall']:.3f}, F1={metrics['f1_score']:.3f}"
        )

        return metrics

    def _calculate_per_category_metrics(self) -> Dict:
        """
        Calculate precision, recall, F1 for each PHI category.

        Returns:
            Dictionary mapping category to metrics
        """
        # TODO: Implement per-category metrics
        logger.info("Calculating per-category metrics...")

        per_category = {}
        for category in PHI_CATEGORIES:
            per_category[category] = {
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "support": 0,  # Number of ground truth examples
            }

        return per_category

    def _generate_confusion_matrix(self) -> np.ndarray:
        """
        Generate confusion matrix for PHI categories.

        Returns:
            NumPy array (confusion matrix)
        """
        # TODO: Implement confusion matrix generation
        logger.info("Generating confusion matrix...")

        # Placeholder (18x18 matrix for 18 PHI categories)
        return np.zeros((len(PHI_CATEGORIES), len(PHI_CATEGORIES)))

    def _analyze_errors(self) -> Dict:
        """
        Analyze false positives and false negatives.

        Returns:
            Dictionary with error analysis
        """
        # TODO: Implement error analysis
        logger.info("Analyzing errors...")

        error_analysis = {
            "false_positives": {
                "count": 0,
                "examples": [],
                "common_patterns": [],
            },
            "false_negatives": {
                "count": 0,
                "examples": [],
                "common_patterns": [],
            },
        }

        return error_analysis

    def _benchmark_performance(self) -> Dict:
        """
        Benchmark inference speed and resource usage.

        Returns:
            Dictionary with performance metrics
        """
        # TODO: Implement performance benchmarking
        logger.info("Benchmarking performance...")

        import time

        # Measure avg time per document
        # For now, placeholder
        performance = {
            "avg_time_per_document": 0.0,  # seconds
            "avg_time_per_10_pages": 0.0,  # seconds
            "throughput": 0.0,  # documents/hour
            "gpu_memory": 0.0,  # GB (if GPU used)
            "cpu_usage": 0.0,  # percentage
        }

        return performance

    def _save_metrics(self, metrics: Dict):
        """
        Save metrics to JSON file.

        Args:
            metrics: Evaluation metrics dictionary
        """
        output_path = self.output_dir / "evaluation_metrics.json"
        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Metrics saved to {output_path}")

    def _generate_visualizations(self, metrics: Dict):
        """
        Generate visualizations (confusion matrix, per-category F1 bar chart).

        Args:
            metrics: Evaluation metrics
        """
        logger.info("Generating visualizations...")

        # Confusion matrix heatmap
        self._plot_confusion_matrix(metrics["confusion_matrix"])

        # Per-category F1 scores bar chart
        self._plot_per_category_f1(metrics["per_category"])

    def _plot_confusion_matrix(self, cm: np.ndarray):
        """
        Plot confusion matrix heatmap.

        Args:
            cm: Confusion matrix array
        """
        plt.figure(figsize=(14, 12))
        sns.heatmap(
            cm,
            annot=True,
            fmt=".0f",
            cmap="Blues",
            xticklabels=PHI_CATEGORIES,
            yticklabels=PHI_CATEGORIES,
        )
        plt.title("PHI Detection Confusion Matrix")
        plt.xlabel("Predicted Category")
        plt.ylabel("Actual Category")
        plt.xticks(rotation=45, ha="right")
        plt.yticks(rotation=0)
        plt.tight_layout()

        output_path = self.output_dir / "confusion_matrix.png"
        plt.savefig(output_path, dpi=300)
        logger.info(f"Confusion matrix saved to {output_path}")

    def _plot_per_category_f1(self, per_category: Dict):
        """
        Plot per-category F1 scores bar chart.

        Args:
            per_category: Per-category metrics dictionary
        """
        categories = list(per_category.keys())
        f1_scores = [per_category[cat]["f1_score"] for cat in categories]

        plt.figure(figsize=(14, 6))
        bars = plt.bar(categories, f1_scores, color="steelblue")

        # Color bars below threshold red
        for i, f1 in enumerate(f1_scores):
            if f1 < 0.85:
                bars[i].set_color("red")

        plt.axhline(y=0.92, color="green", linestyle="--", label="Target F1 (0.92)")
        plt.axhline(y=0.85, color="orange", linestyle="--", label="Min F1 (0.85)")
        plt.title("PHI Detection F1 Score by Category")
        plt.xlabel("PHI Category")
        plt.ylabel("F1 Score")
        plt.xticks(rotation=45, ha="right")
        plt.ylim(0, 1.0)
        plt.legend()
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()

        output_path = self.output_dir / "per_category_f1.png"
        plt.savefig(output_path, dpi=300)
        logger.info(f"Per-category F1 chart saved to {output_path}")

    def generate_report(self, metrics: Dict):
        """
        Generate evaluation report (Markdown).

        Args:
            metrics: Evaluation metrics
        """
        logger.info("Generating evaluation report...")

        report_path = self.output_dir / "evaluation_report.md"

        with open(report_path, "w") as f:
            f.write("# PHI Detection Model Evaluation Report\n\n")

            # Overall metrics
            f.write("## Overall Metrics\n\n")
            overall = metrics["overall"]
            f.write(f"- **Precision**: {overall['precision']:.3f}\n")
            f.write(f"- **Recall**: {overall['recall']:.3f}\n")
            f.write(f"- **F1 Score**: {overall['f1_score']:.3f}\n")
            f.write(f"- **Accuracy**: {overall['accuracy']:.3f}\n\n")

            # Target comparison
            f.write("### Target Comparison\n\n")
            f.write("| Metric | Actual | Target | Status |\n")
            f.write("|--------|--------|--------|--------|\n")
            f.write(
                f"| Precision | {overall['precision']:.3f} | >0.95 | "
                f"{'✅' if overall['precision'] > 0.95 else '❌'} |\n"
            )
            f.write(
                f"| Recall | {overall['recall']:.3f} | >0.90 | "
                f"{'✅' if overall['recall'] > 0.90 else '❌'} |\n"
            )
            f.write(
                f"| F1 Score | {overall['f1_score']:.3f} | >0.92 | "
                f"{'✅' if overall['f1_score'] > 0.92 else '❌'} |\n\n"
            )

            # Per-category metrics
            f.write("## Per-Category Metrics\n\n")
            f.write("| Category | Precision | Recall | F1 | Target F1 | Status |\n")
            f.write("|----------|-----------|--------|-----|-----------|--------|\n")
            for cat, cat_metrics in metrics["per_category"].items():
                target_f1 = 0.85  # Minimum target
                status = "✅" if cat_metrics["f1_score"] >= target_f1 else "❌"
                f.write(
                    f"| {cat} | {cat_metrics['precision']:.3f} | "
                    f"{cat_metrics['recall']:.3f} | {cat_metrics['f1_score']:.3f} | "
                    f">{target_f1} | {status} |\n"
                )

            # Error analysis
            f.write("\n## Error Analysis\n\n")
            errors = metrics["error_analysis"]
            f.write(
                f"- **False Positives**: {errors['false_positives']['count']}\n"
            )
            f.write(f"- **False Negatives**: {errors['false_negatives']['count']}\n\n")

            # Performance benchmarks
            f.write("## Performance Benchmarks\n\n")
            perf = metrics["performance"]
            f.write(f"- **Avg Time per Document**: {perf['avg_time_per_document']:.2f}s\n")
            f.write(
                f"- **Avg Time per 10 Pages**: {perf['avg_time_per_10_pages']:.2f}s "
                f"({'✅' if perf['avg_time_per_10_pages'] < 120 else '❌'} target: <120s)\n"
            )
            f.write(f"- **Throughput**: {perf['throughput']:.1f} docs/hour\n")

        logger.info(f"Evaluation report saved to {report_path}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Evaluate MedCAT PHI Detection Model")

    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to trained MedCAT model",
    )
    parser.add_argument(
        "--test-data",
        type=str,
        required=True,
        help="Path to i2b2 test set directory",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/reports/evaluation",
        help="Path to save evaluation results",
    )

    return parser.parse_args()


def main():
    """Main evaluation script."""
    args = parse_args()

    # Check model exists
    model_path = Path(args.model)
    if not model_path.exists():
        logger.error(
            f"❌ Model not found: {model_path}\n"
            f"   Please train model first using scripts/ml/train_phi_model.py"
        )
        sys.exit(1)

    # Check test data exists
    test_data_dir = Path(args.test_data)
    if not test_data_dir.exists():
        logger.error(
            f"❌ Test data not found: {test_data_dir}\n"
            f"   Please ensure i2b2 test set is available"
        )
        sys.exit(1)

    # Initialize evaluator
    evaluator = PHIEvaluator(
        model_path=str(args.model),
        test_data_dir=str(args.test_data),
        output_dir=str(args.output_dir),
    )

    # Run evaluation
    try:
        metrics = evaluator.evaluate()
        evaluator.generate_report(metrics)

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("EVALUATION COMPLETE")
        logger.info("=" * 60)
        logger.info(
            f"Precision: {metrics['overall']['precision']:.3f} (target: >0.95)"
        )
        logger.info(f"Recall: {metrics['overall']['recall']:.3f} (target: >0.90)")
        logger.info(
            f"F1 Score: {metrics['overall']['f1_score']:.3f} (target: >0.92)"
        )
        logger.info("=" * 60)

        # Check if targets met
        if (
            metrics["overall"]["precision"] >= 0.95
            and metrics["overall"]["recall"] >= 0.90
            and metrics["overall"]["f1_score"] >= 0.92
        ):
            logger.info("✅ All targets MET - Model ready for production")
        else:
            logger.warning("❌ Targets NOT MET - Model needs improvement")

    except Exception as e:
        logger.error(f"❌ Evaluation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # ⚠️  BLOCKER: This script requires:
    # 1. Trained PHI detection model (from train_phi_model.py)
    # 2. i2b2 2014 test set (195 notes)
    # 3. MedCAT library
    #
    # Status: SCAFFOLDING - Implementation incomplete
    # Next steps: Train model, then run evaluation
    main()
