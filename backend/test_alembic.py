#!/usr/bin/env python
"""Test script to run alembic migrations with detailed logging."""
import sys
import logging

# Setup logging to see everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

try:
    logger.info("Importing alembic...")
    from alembic.config import Config
    from alembic import command

    logger.info("Creating config...")
    cfg = Config('alembic.ini')

    logger.info("Running upgrade command...")
    command.upgrade(cfg, 'head')

    logger.info("✅ Migration completed successfully!")

except Exception as e:
    logger.error(f"❌ Error during migration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
