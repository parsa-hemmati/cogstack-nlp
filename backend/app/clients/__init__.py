"""
Client Modules

Provides client wrappers for external services:
- ModelServe: MedCAT NLP model serving
- Elasticsearch: Full-text search engine
"""

from app.clients.elasticsearch_client import get_es_client, health_check

try:
    from app.clients.modelserve_client import ModelServeClient
    __all__ = ['ModelServeClient', 'get_es_client', 'health_check']
except ImportError:
    # ModelServe dependencies not installed, export only Elasticsearch client
    __all__ = ['get_es_client', 'health_check']
