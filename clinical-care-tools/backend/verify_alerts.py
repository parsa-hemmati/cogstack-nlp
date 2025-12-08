import asyncio
import sys
import os
import uuid
import logging
from uuid import uuid4

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))
sys.path.append(os.path.dirname(__file__))

from app.core.database import AsyncSessionLocal
from app.services.alerting.alert_manager import AlertManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify():
    logger.info("Starting Alert Manager Verification")
    
    async with AsyncSessionLocal() as db:
        manager = AlertManager(db)
        
        # 1. Create Rule
        user_id = uuid4()
        rule_name = f"Test Rule {uuid4()}"
        logger.info(f"Creating rule: {rule_name}")
        
        rule = await manager.create_rule(
            name=rule_name,
            conditions={
                "operator": "and",
                "conditions": [
                    {
                        "field": "text",
                        "operator": "contains",
                        "value": "SEPSIS"
                    }
                ]
            },
            severity="high",
            created_by=user_id,
            description="Test rule for sepsis"
        )
        logger.info(f"Rule created: {rule.id}")
        
        # 2. Evaluate Data (Should Match)
        logger.info("Evaluating matching data...")
        data = {"text": "Patient shows signs of SEPSIS."}
        alerts = await manager.evaluate_and_notify(
            data=data,
            patient_id=uuid4()
        )
        
        if alerts:
            logger.info(f"SUCCESS: Triggered {len(alerts)} alerts.")
            logger.info(f"Alert ID: {alerts[0].id}")
        else:
            logger.error("FAILURE: No alerts triggered!")
            return

        # 3. Evaluate Data (Should NOT Match)
        logger.info("Evaluating non-matching data...")
        data_safe = {"text": "Patient is fine."}
        alerts_safe = await manager.evaluate_and_notify(
            data=data_safe,
            patient_id=uuid4()
        )
        
        if not alerts_safe:
            logger.info("SUCCESS: No alerts triggered for safe data.")
        else:
            logger.error(f"FAILURE: Unexpected alerts triggered: {len(alerts_safe)}")
            
        # 4. List Alerts
        logger.info("Listing alerts...")
        listed = await manager.list_alerts(limit=5)
        logger.info(f"Found {len(listed)} total alerts in system.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(verify())
