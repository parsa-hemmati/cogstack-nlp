import sys
import os
import logging
from uuid import uuid4

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))
sys.path.append(os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.services.analytics.analytics_dashboard_service import AnalyticsDashboardService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify():
    logger.info("Starting Analytics Service Verification")
    
    db = SessionLocal()
    try:
        service = AnalyticsDashboardService(db)
        
        # 1. Test Total Patients (Metric)
        logger.info("Testing 'total_patients' metric...")
        data = service.get_widget_data({
            "type": "metric",
            "config": {"metric": "total_patients"}
        })
        logger.info(f"Total Patients: {data}")
        
        # 2. Test Gender Distribution (Bar Chart)
        logger.info("Testing 'gender_distribution' bar chart...")
        data = service.get_widget_data({
            "type": "bar_chart",
            "config": {"groupBy": "gender", "metric": "count"}
        })
        logger.info(f"Gender Distribution: {data}")

        # 3. Test Processing Success Rate (Gauge)
        logger.info("Testing 'processing_success_rate' gauge...")
        data = service.get_widget_data({
            "type": "gauge",
            "config": {"metric": "processing_success_rate"}
        })
        logger.info(f"Success Rate: {data}")

    except Exception as e:
        logger.error(f"Verification Failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    verify()
