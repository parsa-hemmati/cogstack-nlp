"""
Elasticsearch Client Module

Provides async Elasticsearch client wrapper for application use.
Handles connection management and provides helper functions.

Usage:
    # As regular client
    client = get_es_client()
    result = await client.search(...)
    await client.close()

    # As context manager
    async with get_es_client() as client:
        result = await client.search(...)
"""

import os
from typing import Dict, Any
from elasticsearch import AsyncElasticsearch
import logging

logger = logging.getLogger(__name__)


def get_es_client() -> AsyncElasticsearch:
    """
    Get AsyncElasticsearch client instance.

    Reads Elasticsearch URL from environment variable ELASTICSEARCH_URL.
    Defaults to http://localhost:9200 if not set.

    Returns:
        AsyncElasticsearch: Configured Elasticsearch client instance

    Example:
        client = get_es_client()
        health = await client.cluster.health()
        await client.close()
    """
    es_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
    logger.debug(f"Connecting to Elasticsearch at {es_url}")

    return AsyncElasticsearch(
        hosts=[es_url],
        # Connection settings
        max_retries=3,
        retry_on_timeout=True,
        # Timeouts
        request_timeout=30,
        # Keep-alive
        verify_certs=False,  # For development; enable in production
    )


async def health_check() -> Dict[str, Any]:
    """
    Check Elasticsearch cluster health.

    Returns:
        Dict[str, Any]: Cluster health information including:
            - cluster_name: Name of the cluster
            - status: Cluster status (green/yellow/red)
            - number_of_nodes: Number of nodes in cluster
            - ...other health metrics

    Example:
        health = await health_check()
        print(f"Cluster status: {health['status']}")
    """
    client = get_es_client()
    try:
        health_info = await client.cluster.health()
        logger.info(f"Elasticsearch cluster health: {health_info.get('status')}")
        return health_info
    finally:
        await client.close()
