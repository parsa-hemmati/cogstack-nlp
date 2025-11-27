"""
Search Indexer Background Job

Continuously indexes unindexed documents from PostgreSQL to Elasticsearch every N minutes.
Runs in background as a separate service container.

Usage:
    python -m app.jobs.search_indexer_job
"""

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime

from app.clients.elasticsearch_client import get_es_client
from app.db.session import get_db
from app.services.search_indexer import SearchIndexer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global shutdown flag
shutdown_requested = False


def handle_shutdown(signum, frame):
    """Handle SIGTERM/SIGINT for graceful shutdown"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, requesting graceful shutdown...")
    shutdown_requested = True


async def run_indexer():
    """
    Main indexer loop.

    Continuously indexes documents every SEARCH_BATCH_INTERVAL_MINUTES.
    Runs until shutdown signal received (SIGTERM/SIGINT).
    """
    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    # Load configuration from environment
    batch_interval_minutes = int(os.getenv('SEARCH_BATCH_INTERVAL_MINUTES', '5'))
    batch_size = int(os.getenv('SEARCH_BATCH_SIZE', '1000'))

    logger.info("=" * 60)
    logger.info("Search Indexer Background Job")
    logger.info("=" * 60)
    logger.info(f"Batch interval: {batch_interval_minutes} minutes")
    logger.info(f"Batch size: {batch_size} documents")
    logger.info(f"Elasticsearch URL: {os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')}")
    logger.info("=" * 60)

    # Initialize Elasticsearch client
    es_client = get_es_client()

    try:
        # Check Elasticsearch health
        health = await es_client.cluster.health()
        logger.info(f"Elasticsearch cluster health: {health.get('status')}")

        # Main indexing loop
        iteration = 0
        while not shutdown_requested:
            iteration += 1
            start_time = datetime.now()

            logger.info(f"[Iteration {iteration}] Starting batch indexing...")

            try:
                # Get database session
                async for db_session in get_db():
                    # Create indexer instance
                    indexer = SearchIndexer(es_client=es_client, db_session=db_session)

                    # Index documents batch
                    indexed_count = await indexer.index_documents_batch(batch_size=batch_size)

                    elapsed_seconds = (datetime.now() - start_time).total_seconds()

                    if indexed_count > 0:
                        logger.info(
                            f"[Iteration {iteration}] Successfully indexed {indexed_count} documents "
                            f"in {elapsed_seconds:.2f} seconds"
                        )
                    else:
                        logger.info(f"[Iteration {iteration}] No unindexed documents found")

                    break  # Exit the async for loop

            except Exception as e:
                logger.error(f"[Iteration {iteration}] Error during indexing: {e}", exc_info=True)

            # Sleep until next iteration (unless shutdown requested)
            if not shutdown_requested:
                sleep_seconds = batch_interval_minutes * 60
                logger.info(f"[Iteration {iteration}] Sleeping for {batch_interval_minutes} minutes...")

                # Sleep in small chunks to allow responsive shutdown
                for i in range(sleep_seconds):
                    if shutdown_requested:
                        break
                    await asyncio.sleep(1)

        logger.info("Shutdown requested, exiting gracefully...")

    except Exception as e:
        logger.error(f"Fatal error in indexer loop: {e}", exc_info=True)
        sys.exit(1)

    finally:
        await es_client.close()
        logger.info("Elasticsearch client closed")


if __name__ == "__main__":
    logger.info("Starting search indexer job...")
    try:
        asyncio.run(run_indexer())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    logger.info("Search indexer job terminated")
