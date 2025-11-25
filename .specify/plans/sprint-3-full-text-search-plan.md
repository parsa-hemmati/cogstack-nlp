# Technical Plan: Full-Text Search Enhancement (Sprint 3)

**Version**: 1.0.0
**Date**: 2025-11-19
**Status**: Ready for Implementation
**Specification**: `.specify/specifications/sprint-3-full-text-search.md` v1.0.0
**Author**: AI Assistant (Claude Code)
**Sprint Duration**: 4 weeks (~120 hours)

**Version History**:
- **1.0.0** (2025-11-19): Initial technical plan for full-text search enhancement

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Elasticsearch Index Design](#elasticsearch-index-design)
4. [API Design](#api-design)
5. [Database Schema](#database-schema)
6. [Component Design](#component-design)
7. [Query Parser Design](#query-parser-design)
8. [Relevance Ranking Implementation](#relevance-ranking-implementation)
9. [Security Architecture](#security-architecture)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Architecture](#deployment-architecture)
12. [Performance Requirements](#performance-requirements)
13. [Risks & Mitigations](#risks--mitigations)
14. [Implementation Phases](#implementation-phases)

---

## Architecture Overview

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│          Clinical Care Tools - Search Architecture              │
│                                                                  │
│  ┌────────────────────┐          ┌──────────────────────────┐  │
│  │    Frontend        │          │       Backend            │  │
│  │  (Vue 3 + TS)      │──────────│      (FastAPI)           │  │
│  │                    │ REST API │                          │  │
│  │  - SearchView      │◀─────────│  - SearchService         │  │
│  │  - QueryBuilder    │          │  - QueryParser           │  │
│  │  - Results Display │          │  - ExportService         │  │
│  │  - Facet Filters   │          │  - AnalyticsService      │  │
│  └────────────────────┘          └───────┬──────────────────┘  │
│                                           │                      │
│                            ┌──────────────┼──────────────┐      │
│                            │              │              │      │
│                            ▼              ▼              ▼      │
│                  ┌──────────────┐  ┌────────────┐  ┌─────────┐│
│                  │ Elasticsearch│  │ PostgreSQL │  │  Redis  ││
│                  │              │  │            │  │ (Cache) ││
│                  │ - documents  │  │ - saved_   │  │         ││
│                  │   index      │  │   searches │  │ - Query ││
│                  │ - Full-text  │  │ - search_  │  │   cache ││
│                  │   search     │  │   analytics│  │         ││
│                  │ - BM25       │  │ - audit_   │  │         ││
│                  │ - Facets     │  │   logs     │  │         ││
│                  └──────────────┘  └────────────┘  └─────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**Frontend (Vue 3 + TypeScript + Vuetify)**:
- **SearchView.vue**: Main search interface with query input
- **QueryBuilder.vue**: Visual query builder (drag-and-drop)
- **SearchResults.vue**: Results list with highlighting and pagination
- **FacetFilters.vue**: Faceted filters sidebar (document type, author, date, department)
- **SavedSearches.vue**: Saved searches panel
- **SearchAnalytics.vue**: Admin analytics dashboard

**Backend (FastAPI + Python 3.11)**:
- **SearchService**: Execute searches, manage saved searches, export results
- **QueryParser**: Parse user queries into Elasticsearch DSL
- **ElasticsearchClient**: Low-level Elasticsearch communication
- **ExportService**: Export results to CSV, JSON, FHIR R4
- **AnalyticsService**: Track and aggregate search analytics
- **AuditService**: Log all search activity (existing from Phase 1)

**Elasticsearch 8+**:
- **documents index**: Full-text indexed clinical documents
- **BM25 scoring**: Industry-standard relevance algorithm
- **Aggregations**: Faceted search counts
- **Highlighting**: Context snippets with keyword highlighting
- **Suggester**: Autocomplete suggestions

**PostgreSQL 15**:
- **saved_searches table**: User saved searches
- **search_analytics table**: Search metrics tracking
- **audit_logs table**: Search audit trail (existing from Phase 1)

**Redis**:
- **Query result caching**: Cache search results for 10 minutes
- **Autocomplete caching**: Cache suggestions for performance

---

## Technology Stack

### New Dependencies for Sprint 3

| Technology | Version | Rationale |
|------------|---------|-----------|
| **Elasticsearch** | 8.11+ | Full-text search, BM25 scoring, aggregations, highlighting |
| **elasticsearch-py** | 8.11+ | Async Elasticsearch Python client |
| **redis** | 5.0+ | Query result caching, autocomplete caching |

### Existing Technologies (from Phase 1-2)

| Technology | Version | Usage |
|------------|---------|-------|
| **FastAPI** | 0.115+ | REST API framework |
| **PostgreSQL** | 15+ | Saved searches, search analytics, audit logs |
| **Vue** | 3.5+ | Frontend framework |
| **Vuetify** | 3.7+ | UI components |

### Alternatives Considered

**Why not Solr?**
- Elasticsearch: Better async Python client, simpler configuration, stronger ecosystem
- Solr: More complex schema management, heavier XML configuration

**Why not Whoosh?**
- Elasticsearch: Distributed, scalable to millions of documents, production-grade
- Whoosh: Pure Python, good for small datasets, less scalable

**Why not PostgreSQL Full-Text Search?**
- Elasticsearch: Superior relevance ranking (BM25), better performance at scale (>1M docs), richer query syntax
- PostgreSQL: Good for simple search, less flexible relevance tuning

---

## Elasticsearch Index Design

### Index Mapping

```json
{
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 1,
    "analysis": {
      "analyzer": {
        "clinical_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "english_stop",
            "english_stemmer",
            "clinical_synonyms"
          ]
        }
      },
      "filter": {
        "english_stop": {
          "type": "stop",
          "stopwords": "_english_"
        },
        "english_stemmer": {
          "type": "stemmer",
          "language": "english"
        },
        "clinical_synonyms": {
          "type": "synonym",
          "synonyms": [
            "MI, myocardial infarction",
            "CAD, coronary artery disease",
            "DM, diabetes mellitus",
            "HTN, hypertension"
          ]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "document_id": {
        "type": "keyword"
      },
      "title": {
        "type": "text",
        "analyzer": "clinical_analyzer",
        "fields": {
          "raw": {
            "type": "keyword"
          }
        }
      },
      "content": {
        "type": "text",
        "analyzer": "clinical_analyzer"
      },
      "document_type": {
        "type": "keyword"
      },
      "author": {
        "type": "keyword"
      },
      "department": {
        "type": "keyword"
      },
      "date": {
        "type": "date",
        "format": "strict_date_optional_time"
      },
      "patient_id": {
        "type": "keyword"
      },
      "concepts": {
        "type": "nested",
        "properties": {
          "cui": {
            "type": "keyword"
          },
          "name": {
            "type": "text"
          },
          "type": {
            "type": "keyword"
          }
        }
      },
      "indexed_at": {
        "type": "date"
      }
    }
  }
}
```

### Index Creation Script

```python
# scripts/create_search_index.py
from elasticsearch import AsyncElasticsearch
import asyncio
import json

async def create_documents_index():
    """Create Elasticsearch documents index with mapping"""
    es = AsyncElasticsearch(['http://localhost:9200'])

    with open('elasticsearch-mapping.json', 'r') as f:
        mapping = json.load(f)

    # Delete existing index if exists
    if await es.indices.exists(index='documents'):
        await es.indices.delete(index='documents')

    # Create index with mapping
    await es.indices.create(index='documents', body=mapping)
    print("✅ Created 'documents' index")

    await es.close()

if __name__ == '__main__':
    asyncio.run(create_documents_index())
```

### Batch Indexing Strategy

```python
# app/services/search_indexer.py
from elasticsearch import AsyncElasticsearch, helpers
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Document
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SearchIndexer:
    """Batch index documents into Elasticsearch"""

    def __init__(self, es: AsyncElasticsearch, db: AsyncSession):
        self.es = es
        self.db = db

    async def index_documents_batch(self, batch_size: int = 1000):
        """Index documents in batches (called every 5 minutes)"""
        # Get unindexed documents
        unindexed_docs = await self._get_unindexed_documents(batch_size)

        if not unindexed_docs:
            logger.info("No documents to index")
            return 0

        # Prepare bulk index actions
        actions = []
        for doc in unindexed_docs:
            actions.append({
                '_index': 'documents',
                '_id': str(doc.id),
                '_source': {
                    'document_id': str(doc.id),
                    'title': doc.title or doc.filename,
                    'content': await self._decrypt_content(doc.content),
                    'document_type': doc.document_type,
                    'author': doc.author,
                    'department': doc.department,
                    'date': doc.created_at.isoformat(),
                    'patient_id': str(doc.patient_id) if doc.patient_id else None,
                    'concepts': await self._extract_concepts(doc),
                    'indexed_at': datetime.utcnow().isoformat()
                }
            })

        # Bulk index
        success, failed = await helpers.async_bulk(self.es, actions)
        logger.info(f"Indexed {success} documents, {failed} failed")

        # Mark documents as indexed
        for doc in unindexed_docs:
            doc.indexed = True
        await self.db.commit()

        return success
```

---

## API Design

### OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: Full-Text Search API
  version: 1.0.0
  description: Document search API with Elasticsearch

paths:
  /api/v1/search:
    post:
      summary: Execute full-text search
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SearchRequest'
      responses:
        '200':
          description: Search results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SearchResponse'
        '400':
          description: Invalid query syntax
        '401':
          description: Unauthorized

  /api/v1/search/suggestions:
    get:
      summary: Get autocomplete suggestions
      security:
        - bearerAuth: []
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Suggestions
          content:
            application/json:
              schema:
                type: object
                properties:
                  query:
                    type: string
                  suggestions:
                    type: array
                    items:
                      type: string

  /api/v1/search/{document_id}/explain:
    get:
      summary: Explain relevance score
      security:
        - bearerAuth: []
      parameters:
        - name: document_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
        - name: query
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Score explanation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ScoreExplanation'

  /api/v1/search/saved:
    get:
      summary: List saved searches
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Saved searches
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/SavedSearch'

    post:
      summary: Save search
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                description:
                  type: string
                query:
                  type: string
                filters:
                  $ref: '#/components/schemas/SearchFilters'
              required: [name, query]
      responses:
        '201':
          description: Search saved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SavedSearch'

  /api/v1/search/export:
    post:
      summary: Export search results
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                query:
                  type: string
                filters:
                  $ref: '#/components/schemas/SearchFilters'
                format:
                  type: string
                  enum: [csv, json, fhir]
              required: [query, format]
      responses:
        '200':
          description: Export file
          content:
            text/csv:
              schema:
                type: string
                format: binary
            application/json:
              schema:
                type: object
            application/fhir+json:
              schema:
                type: object

  /api/v1/search/analytics:
    get:
      summary: Get search analytics (admin only)
      security:
        - bearerAuth: []
      parameters:
        - name: start_date
          in: query
          schema:
            type: string
            format: date
        - name: end_date
          in: query
          schema:
            type: string
            format: date
      responses:
        '200':
          description: Analytics data
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SearchAnalytics'

components:
  schemas:
    SearchRequest:
      type: object
      properties:
        query:
          type: string
          example: "(diabetes OR hypertension) AND medication"
        filters:
          $ref: '#/components/schemas/SearchFilters'
        page:
          type: integer
          default: 1
        page_size:
          type: integer
          default: 20
          maximum: 100
        sort:
          type: string
          enum: [relevance, date, title]
          default: relevance
      required: [query]

    SearchFilters:
      type: object
      properties:
        document_types:
          type: array
          items:
            type: string
        authors:
          type: array
          items:
            type: string
        departments:
          type: array
          items:
            type: string
        date_range:
          type: object
          properties:
            start:
              type: string
              format: date-time
            end:
              type: string
              format: date-time

    SearchResponse:
      type: object
      properties:
        query:
          type: string
        total_results:
          type: integer
        page:
          type: integer
        page_size:
          type: integer
        documents:
          type: array
          items:
            $ref: '#/components/schemas/SearchResultDocument'
        facets:
          $ref: '#/components/schemas/Facets'
        execution_time_ms:
          type: integer

    SearchResultDocument:
      type: object
      properties:
        document_id:
          type: string
          format: uuid
        title:
          type: string
        document_type:
          type: string
        author:
          type: string
        date:
          type: string
          format: date-time
        department:
          type: string
        relevance_score:
          type: number
          format: float
        highlights:
          type: array
          items:
            $ref: '#/components/schemas/Highlight'

    Highlight:
      type: object
      properties:
        field:
          type: string
        snippets:
          type: array
          items:
            type: string

    Facets:
      type: object
      properties:
        document_types:
          type: array
          items:
            $ref: '#/components/schemas/FacetValue'
        authors:
          type: array
          items:
            $ref: '#/components/schemas/FacetValue'
        departments:
          type: array
          items:
            $ref: '#/components/schemas/FacetValue'
        date_range:
          type: object
          properties:
            min:
              type: string
              format: date-time
            max:
              type: string
              format: date-time

    FacetValue:
      type: object
      properties:
        value:
          type: string
        count:
          type: integer

    SavedSearch:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        description:
          type: string
        query:
          type: string
        filters:
          $ref: '#/components/schemas/SearchFilters'
        created_at:
          type: string
          format: date-time
        created_by:
          type: string
          format: uuid

    ScoreExplanation:
      type: object
      properties:
        document_id:
          type: string
          format: uuid
        total_score:
          type: number
        bm25_score:
          type: number
        field_boosts:
          type: object
          additionalProperties:
            type: number
        recency_boost:
          type: number
        matching_terms:
          type: array
          items:
            type: object
            properties:
              term:
                type: string
              field:
                type: string
              score:
                type: number

    SearchAnalytics:
      type: object
      properties:
        top_queries:
          type: array
          items:
            type: object
            properties:
              query:
                type: string
              count:
                type: integer
        zero_result_queries:
          type: array
          items:
            type: string
        slow_queries:
          type: array
          items:
            type: object
            properties:
              query:
                type: string
              execution_time_ms:
                type: integer
        search_trends:
          type: array
          items:
            type: object
            properties:
              date:
                type: string
                format: date
              count:
                type: integer
```

---

## Database Schema

### New Tables for Sprint 3

```sql
-- Saved searches table
CREATE TABLE saved_searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    query TEXT NOT NULL,
    filters JSONB,  -- SearchFilters as JSON
    is_shared BOOLEAN NOT NULL DEFAULT FALSE,
    execution_count INT NOT NULL DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT saved_searches_name_unique UNIQUE (user_id, name)
);

CREATE INDEX idx_saved_searches_user_id ON saved_searches(user_id);
CREATE INDEX idx_saved_searches_is_shared ON saved_searches(is_shared);
CREATE INDEX idx_saved_searches_name ON saved_searches(name);

-- Search analytics table (for metrics tracking)
CREATE TABLE search_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    filters JSONB,
    results_count INT NOT NULL,
    execution_time_ms INT NOT NULL,
    clicked_documents UUID[],  -- Array of document IDs clicked from results

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- No updates allowed (immutable analytics log)
    CONSTRAINT no_updates CHECK (created_at IS NOT NULL)
);

CREATE INDEX idx_search_analytics_user_id ON search_analytics(user_id);
CREATE INDEX idx_search_analytics_query ON search_analytics USING GIN (to_tsvector('english', query));
CREATE INDEX idx_search_analytics_created_at ON search_analytics(created_at DESC);
CREATE INDEX idx_search_analytics_results_count ON search_analytics(results_count);

-- Add indexed flag to documents table (track which docs are in Elasticsearch)
ALTER TABLE documents ADD COLUMN indexed BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE documents ADD COLUMN last_indexed_at TIMESTAMP WITH TIME ZONE;

CREATE INDEX idx_documents_indexed ON documents(indexed) WHERE NOT indexed;
```

### Alembic Migration

```python
# alembic/versions/010_add_search_tables.py
"""Add saved_searches and search_analytics tables

Revision ID: 010
Revises: 009
Create Date: 2025-11-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

def upgrade():
    # Create saved_searches table
    op.create_table(
        'saved_searches',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('filters', JSONB()),
        sa.Column('is_shared', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('execution_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('user_id', 'name', name='saved_searches_name_unique')
    )
    op.create_index('idx_saved_searches_user_id', 'saved_searches', ['user_id'])
    op.create_index('idx_saved_searches_is_shared', 'saved_searches', ['is_shared'])
    op.create_index('idx_saved_searches_name', 'saved_searches', ['name'])

    # Create search_analytics table
    op.create_table(
        'search_analytics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('filters', JSONB()),
        sa.Column('results_count', sa.Integer(), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False),
        sa.Column('clicked_documents', ARRAY(UUID(as_uuid=True))),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('idx_search_analytics_user_id', 'search_analytics', ['user_id'])
    op.create_index('idx_search_analytics_created_at', 'search_analytics', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_search_analytics_results_count', 'search_analytics', ['results_count'])

    # Add indexed flag to documents table
    op.add_column('documents', sa.Column('indexed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('documents', sa.Column('last_indexed_at', sa.TIMESTAMP(timezone=True)))
    op.create_index('idx_documents_indexed', 'documents', ['indexed'], postgresql_where=sa.text('NOT indexed'))

def downgrade():
    op.drop_index('idx_documents_indexed')
    op.drop_column('documents', 'last_indexed_at')
    op.drop_column('documents', 'indexed')

    op.drop_index('idx_search_analytics_results_count')
    op.drop_index('idx_search_analytics_created_at')
    op.drop_index('idx_search_analytics_user_id')
    op.drop_table('search_analytics')

    op.drop_index('idx_saved_searches_name')
    op.drop_index('idx_saved_searches_is_shared')
    op.drop_index('idx_saved_searches_user_id')
    op.drop_table('saved_searches')
```

---

## Component Design

### Backend Services

**SearchService** (`app/services/search_service.py`)
```python
from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, SavedSearch
from app.schemas.search import SearchRequest, SearchResponse
from app.search.query_builder import QueryBuilder
from app.services.audit_service import AuditService
from typing import List, Dict, Any
import logging
import time

logger = logging.getLogger(__name__)

class SearchService:
    """Full-text search service using Elasticsearch"""

    def __init__(
        self,
        es: AsyncElasticsearch,
        db: AsyncSession,
        audit: AuditService
    ):
        self.es = es
        self.db = db
        self.audit = audit
        self.query_builder = QueryBuilder()

    async def search_documents(
        self,
        request: SearchRequest,
        user: User,
        ip_address: str
    ) -> SearchResponse:
        """Execute full-text search with filters and relevance ranking"""
        start_time = time.time()

        try:
            # Build Elasticsearch query
            es_query = self.query_builder.build_query(
                query=request.query,
                filters=request.filters,
                page=request.page,
                page_size=request.page_size,
                sort=request.sort
            )

            # Execute search
            response = await self.es.search(
                index='documents',
                body=es_query,
                timeout='10s'
            )

            # Parse results
            search_results = self._parse_search_response(response, request)

            # Track analytics
            execution_time_ms = int((time.time() - start_time) * 1000)
            await self._track_search(
                user=user,
                query=request.query,
                filters=request.filters,
                results_count=search_results.total_results,
                execution_time_ms=execution_time_ms
            )

            # Audit log
            await self.audit.log(
                user_id=user.id,
                action='SEARCH_EXECUTED',
                resource_type='search',
                resource_id=None,
                details={
                    'query': request.query,
                    'results_count': search_results.total_results,
                    'execution_time_ms': execution_time_ms
                },
                ip_address=ip_address
            )

            return search_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    async def get_suggestions(self, partial_query: str) -> List[str]:
        """Get autocomplete suggestions"""
        response = await self.es.search(
            index='documents',
            body={
                'suggest': {
                    'query-suggest': {
                        'prefix': partial_query,
                        'completion': {
                            'field': 'title.suggest',
                            'size': 10,
                            'skip_duplicates': True
                        }
                    }
                }
            }
        )

        suggestions = []
        for option in response['suggest']['query-suggest'][0]['options']:
            suggestions.append(option['text'])

        return suggestions

    async def explain_score(
        self,
        document_id: str,
        query: str
    ) -> Dict[str, Any]:
        """Explain relevance score for document"""
        es_query = self.query_builder.build_query(query=query)

        response = await self.es.explain(
            index='documents',
            id=document_id,
            body=es_query
        )

        return self._parse_score_explanation(response['explanation'])

    async def save_search(
        self,
        name: str,
        description: str,
        query: str,
        filters: Dict[str, Any],
        user: User
    ) -> SavedSearch:
        """Save search for reuse"""
        saved_search = SavedSearch(
            user_id=user.id,
            name=name,
            description=description,
            query=query,
            filters=filters
        )
        self.db.add(saved_search)
        await self.db.commit()

        await self.audit.log(
            user_id=user.id,
            action='SEARCH_SAVED',
            resource_type='saved_search',
            resource_id=str(saved_search.id),
            details={'name': name, 'query': query}
        )

        return saved_search
```

**QueryBuilder** (`app/search/query_builder.py`)
```python
from typing import Dict, Any, List, Optional
from app.schemas.search import SearchFilters
import re

class QueryBuilder:
    """Build Elasticsearch DSL queries from user input"""

    def build_query(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = 'relevance'
    ) -> Dict[str, Any]:
        """Build complete Elasticsearch query"""

        # Parse query into Elasticsearch bool query
        bool_query = self._parse_query(query)

        # Apply filters
        if filters:
            bool_query = self._apply_filters(bool_query, filters)

        # Build complete query with pagination, sorting, highlighting
        es_query = {
            'from': (page - 1) * page_size,
            'size': page_size,
            'query': {
                'function_score': {
                    'query': bool_query,
                    'functions': [
                        # Recency boost
                        {
                            'gauss': {
                                'date': {
                                    'scale': '30d',  # Half-decay at 30 days
                                    'decay': 0.5
                                }
                            },
                            'weight': 1.5
                        }
                    ],
                    'score_mode': 'multiply',
                    'boost_mode': 'multiply'
                }
            },
            'highlight': {
                'fields': {
                    'title': {'number_of_fragments': 0},
                    'content': {
                        'fragment_size': 150,
                        'number_of_fragments': 3
                    }
                },
                'pre_tags': ['<em>'],
                'post_tags': ['</em>']
            },
            'aggs': {
                'document_types': {
                    'terms': {'field': 'document_type', 'size': 50}
                },
                'authors': {
                    'terms': {'field': 'author', 'size': 50}
                },
                'departments': {
                    'terms': {'field': 'department', 'size': 50}
                },
                'date_range': {
                    'date_histogram': {
                        'field': 'date',
                        'calendar_interval': 'month'
                    }
                }
            }
        }

        # Apply sorting
        if sort == 'date':
            es_query['sort'] = [{'date': 'desc'}]
        elif sort == 'title':
            es_query['sort'] = [{'title.raw': 'asc'}]
        # relevance sort is default (by score)

        return es_query

    def _parse_query(self, query: str) -> Dict[str, Any]:
        """Parse user query into Elasticsearch bool query"""

        # Detect query type
        if self._is_phrase_query(query):
            return self._build_phrase_query(query)
        elif self._is_boolean_query(query):
            return self._build_boolean_query(query)
        elif self._is_field_query(query):
            return self._build_field_query(query)
        else:
            return self._build_simple_query(query)

    def _is_phrase_query(self, query: str) -> bool:
        """Check if query is phrase search (quoted)"""
        return '"' in query

    def _is_boolean_query(self, query: str) -> bool:
        """Check if query contains boolean operators"""
        return bool(re.search(r'\b(AND|OR|NOT)\b', query, re.IGNORECASE))

    def _is_field_query(self, query: str) -> bool:
        """Check if query is field-specific (field:value)"""
        return ':' in query and not query.startswith('http')

    def _build_simple_query(self, query: str) -> Dict[str, Any]:
        """Build simple keyword query with field boosting"""
        return {
            'bool': {
                'should': [
                    {'match': {'title': {'query': query, 'boost': 10}}},
                    {'match': {'content': {'query': query, 'boost': 1}}},
                    {'match': {'author': {'query': query, 'boost': 2}}}
                ],
                'minimum_should_match': 1
            }
        }

    def _build_phrase_query(self, query: str) -> Dict[str, Any]:
        """Build phrase query (exact match)"""
        # Extract phrase from quotes
        phrase_pattern = r'"([^"]*)"'
        phrases = re.findall(phrase_pattern, query)

        if not phrases:
            return self._build_simple_query(query)

        must_clauses = []
        for phrase in phrases:
            must_clauses.append({
                'multi_match': {
                    'query': phrase,
                    'fields': ['title^10', 'content^1'],
                    'type': 'phrase'
                }
            })

        return {'bool': {'must': must_clauses}}

    def _build_boolean_query(self, query: str) -> Dict[str, Any]:
        """Build boolean query (AND, OR, NOT)"""
        # Simple parser for AND/OR/NOT queries
        # Production: use proper query parser (e.g., pyparsing, lark)

        must_clauses = []
        should_clauses = []
        must_not_clauses = []

        # Split by AND/OR/NOT
        parts = re.split(r'\b(AND|OR|NOT)\b', query, flags=re.IGNORECASE)

        operator = 'AND'
        for part in parts:
            part = part.strip()
            if part.upper() in ['AND', 'OR', 'NOT']:
                operator = part.upper()
            elif part:
                clause = {'multi_match': {'query': part, 'fields': ['title^10', 'content^1']}}

                if operator == 'AND':
                    must_clauses.append(clause)
                elif operator == 'OR':
                    should_clauses.append(clause)
                elif operator == 'NOT':
                    must_not_clauses.append(clause)

        bool_query = {}
        if must_clauses:
            bool_query['must'] = must_clauses
        if should_clauses:
            bool_query['should'] = should_clauses
        if must_not_clauses:
            bool_query['must_not'] = must_not_clauses

        return {'bool': bool_query}

    def _apply_filters(
        self,
        query: Dict[str, Any],
        filters: SearchFilters
    ) -> Dict[str, Any]:
        """Apply filters to query"""
        filter_clauses = []

        if filters.document_types:
            filter_clauses.append({
                'terms': {'document_type': filters.document_types}
            })

        if filters.authors:
            filter_clauses.append({
                'terms': {'author': filters.authors}
            })

        if filters.departments:
            filter_clauses.append({
                'terms': {'department': filters.departments}
            })

        if filters.date_range:
            filter_clauses.append({
                'range': {
                    'date': {
                        'gte': filters.date_range.start.isoformat(),
                        'lte': filters.date_range.end.isoformat()
                    }
                }
            })

        if filter_clauses:
            query['bool']['filter'] = filter_clauses

        return query
```

### Frontend Components

**SearchView.vue** (Main component)
```vue
<template>
  <v-container fluid class="search-view">
    <v-row>
      <!-- Faceted filters sidebar (left) -->
      <v-col cols="3">
        <FacetFilters
          :facets="searchResults?.facets"
          :active-filters="filters"
          @update:filters="handleFiltersUpdate"
        />
      </v-col>

      <!-- Main search area (center) -->
      <v-col cols="6">
        <!-- Search input -->
        <v-text-field
          v-model="query"
          label="Search documents..."
          prepend-icon="mdi-magnify"
          clearable
          autofocus
          @keyup.enter="executeSearch"
          @input="debouncedSuggestions"
        >
          <template v-slot:append>
            <v-btn icon @click="toggleQueryBuilder">
              <v-icon>mdi-code-braces</v-icon>
            </v-btn>
          </template>
        </v-text-field>

        <!-- Autocomplete suggestions -->
        <v-list v-if="suggestions.length > 0" class="suggestions">
          <v-list-item
            v-for="(suggestion, index) in suggestions"
            :key="index"
            @click="applySuggestion(suggestion)"
          >
            {{ suggestion }}
          </v-list-item>
        </v-list>

        <!-- Query builder (toggle) -->
        <QueryBuilder
          v-if="showQueryBuilder"
          v-model="query"
          @close="showQueryBuilder = false"
        />

        <!-- Search results -->
        <v-progress-linear v-if="searching" indeterminate />

        <div v-if="searchResults">
          <p class="text-subtitle-1 mb-2">
            {{ searchResults.total_results }} results
            <span class="text-caption">({{ searchResults.execution_time_ms }}ms)</span>
          </p>

          <SearchResult
            v-for="doc in searchResults.documents"
            :key="doc.document_id"
            :document="doc"
            :query="query"
            class="mb-4"
          />

          <!-- Pagination -->
          <v-pagination
            v-model="page"
            :length="totalPages"
            @update:modelValue="executeSearch"
          />
        </div>

        <v-alert v-if="error" type="error">{{ error }}</v-alert>
      </v-col>

      <!-- Saved searches sidebar (right) -->
      <v-col cols="3">
        <SavedSearches
          :saved-searches="savedSearches"
          @execute="executeSavedSearch"
          @save="showSaveDialog = true"
        />
      </v-col>
    </v-row>

    <!-- Save search dialog -->
    <SaveSearchDialog
      v-model="showSaveDialog"
      :query="query"
      :filters="filters"
      @saved="loadSavedSearches"
    />
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useSearchStore } from '@/stores/search'
import { debounce } from 'lodash-es'
import SearchResult from '@/components/search/SearchResult.vue'
import FacetFilters from '@/components/search/FacetFilters.vue'
import QueryBuilder from '@/components/search/QueryBuilder.vue'
import SavedSearches from '@/components/search/SavedSearches.vue'
import SaveSearchDialog from '@/components/search/SaveSearchDialog.vue'

const searchStore = useSearchStore()

const query = ref('')
const filters = ref({})
const page = ref(1)
const searching = ref(false)
const error = ref<string | null>(null)
const suggestions = ref<string[]>([])
const showQueryBuilder = ref(false)
const showSaveDialog = ref(false)

const searchResults = computed(() => searchStore.results)
const savedSearches = computed(() => searchStore.savedSearches)
const totalPages = computed(() => {
  if (!searchResults.value) return 0
  return Math.ceil(searchResults.value.total_results / 20)
})

const executeSearch = async () => {
  searching.value = true
  error.value = null

  try {
    await searchStore.search({
      query: query.value,
      filters: filters.value,
      page: page.value
    })
  } catch (err: any) {
    error.value = err.message || 'Search failed'
  } finally {
    searching.value = false
  }
}

const debouncedSuggestions = debounce(async (event: Event) => {
  const input = (event.target as HTMLInputElement).value
  if (input.length >= 3) {
    suggestions.value = await searchStore.getSuggestions(input)
  } else {
    suggestions.value = []
  }
}, 300)

const applySuggestion = (suggestion: string) => {
  query.value = suggestion
  suggestions.value = []
  executeSearch()
}

const handleFiltersUpdate = (newFilters: any) => {
  filters.value = newFilters
  page.value = 1
  executeSearch()
}

const executeSavedSearch = async (savedSearch: any) => {
  query.value = savedSearch.query
  filters.value = savedSearch.filters
  page.value = 1
  await executeSearch()
}

const loadSavedSearches = async () => {
  await searchStore.loadSavedSearches()
}

onMounted(() => {
  loadSavedSearches()
})
</script>
```

---

## Query Parser Design

### Boolean Query Parsing

For production-grade query parsing, use **Lark parser** (handles nested queries, precedence):

```python
# app/search/query_parser.py
from lark import Lark, Transformer
from typing import Dict, Any

# Grammar for search queries
SEARCH_GRAMMAR = r"""
    ?start: expr

    ?expr: term
         | expr "AND" term   -> and_expr
         | expr "OR" term    -> or_expr
         | "NOT" term        -> not_expr
         | "(" expr ")"      -> group

    ?term: WORD
         | PHRASE
         | field_query

    field_query: FIELD ":" (WORD | PHRASE)

    FIELD: /[a-z_]+/
    WORD: /[a-zA-Z0-9*?]+/
    PHRASE: /"[^"]+"/

    %import common.WS
    %ignore WS
"""

class QueryTransformer(Transformer):
    """Transform parse tree into Elasticsearch bool query"""

    def and_expr(self, args):
        return {'bool': {'must': list(args)}}

    def or_expr(self, args):
        return {'bool': {'should': list(args), 'minimum_should_match': 1}}

    def not_expr(self, args):
        return {'bool': {'must_not': args[0]}}

    def group(self, args):
        return args[0]

    def field_query(self, args):
        field = str(args[0])
        value = str(args[1]).strip('"')
        return {'match': {field: value}}

    def WORD(self, token):
        return {'multi_match': {'query': str(token), 'fields': ['title^10', 'content^1']}}

    def PHRASE(self, token):
        phrase = str(token).strip('"')
        return {'multi_match': {'query': phrase, 'fields': ['title^10', 'content^1'], 'type': 'phrase'}}

class QueryParser:
    """Parse user queries using Lark parser"""

    def __init__(self):
        self.parser = Lark(SEARCH_GRAMMAR, parser='lalr')
        self.transformer = QueryTransformer()

    def parse(self, query: str) -> Dict[str, Any]:
        """Parse query string into Elasticsearch DSL"""
        try:
            tree = self.parser.parse(query)
            return self.transformer.transform(tree)
        except Exception as e:
            # Fallback to simple query on parse error
            return {'multi_match': {'query': query, 'fields': ['title^10', 'content^1']}}
```

---

## Relevance Ranking Implementation

### BM25 Configuration

Elasticsearch default BM25 parameters:
- `k1 = 1.2` (term frequency saturation)
- `b = 0.75` (length normalization)

**Custom configuration** (in index settings):
```json
{
  "settings": {
    "index": {
      "similarity": {
        "custom_bm25": {
          "type": "BM25",
          "k1": 1.5,
          "b": 0.75
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "content": {
        "type": "text",
        "similarity": "custom_bm25"
      }
    }
  }
}
```

### Recency Boost Function

```python
# In QueryBuilder.build_query()
{
  'function_score': {
    'query': bool_query,
    'functions': [
      {
        'gauss': {
          'date': {
            'origin': 'now',
            'scale': '30d',  # Half decay at 30 days
            'offset': '7d',  # No decay for last 7 days
            'decay': 0.5
          }
        },
        'weight': 1.5
      }
    ],
    'score_mode': 'multiply',
    'boost_mode': 'multiply'
  }
}
```

### Score Explanation Parsing

```python
def _parse_score_explanation(self, explanation: Dict[str, Any]) -> ScoreExplanation:
    """Parse Elasticsearch score explanation"""

    def extract_terms(details: List[Dict], terms: List[Dict]):
        for detail in details:
            if 'weight' in detail['description']:
                # Extract term name and score
                match = re.search(r'weight\((.*?)\)', detail['description'])
                if match:
                    term = match.group(1)
                    terms.append({
                        'term': term,
                        'score': detail['value']
                    })

            if 'details' in detail:
                extract_terms(detail['details'], terms)

    matching_terms = []
    extract_terms(explanation.get('details', []), matching_terms)

    return ScoreExplanation(
        total_score=explanation['value'],
        description=explanation['description'],
        matching_terms=matching_terms
    )
```

---

## Security Architecture

### Authentication & Authorization

All search endpoints require JWT authentication (inherited from Phase 1).

**Search-specific permissions**:
```python
class Permission(str, Enum):
    # Search permissions
    SEARCH_EXECUTE = 'search:execute'
    SEARCH_SAVE = 'search:save'
    SEARCH_EXPORT = 'search:export'
    SEARCH_ANALYTICS_VIEW = 'search:analytics_view'  # Admin only

ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.SEARCH_EXECUTE,
        Permission.SEARCH_SAVE,
        Permission.SEARCH_EXPORT,
        Permission.SEARCH_ANALYTICS_VIEW
    ],
    Role.CLINICIAN: [
        Permission.SEARCH_EXECUTE,
        Permission.SEARCH_SAVE
    ],
    Role.RESEARCHER: [
        Permission.SEARCH_EXECUTE,
        Permission.SEARCH_SAVE,
        Permission.SEARCH_EXPORT
    ]
}
```

### Query Injection Prevention

```python
def sanitize_query(query: str) -> str:
    """Sanitize user query to prevent injection attacks"""

    # Remove Elasticsearch special characters that could be exploited
    dangerous_chars = ['<script>', 'javascript:', '{', '}']
    for char in dangerous_chars:
        query = query.replace(char, '')

    # Limit query length
    if len(query) > 1000:
        raise ValueError("Query too long (max 1000 characters)")

    return query
```

### Rate Limiting

```python
# app/middleware/rate_limit.py
from fastapi import Request, HTTPException
from redis import Redis
import time

redis_client = Redis(host='redis', port=6379, decode_responses=True)

async def rate_limit_search(request: Request, user_id: str):
    """Rate limit searches: 60 per minute per user"""
    key = f"rate_limit:search:{user_id}"
    count = redis_client.get(key)

    if count is None:
        redis_client.setex(key, 60, 1)
    elif int(count) >= 60:
        raise HTTPException(429, "Rate limit exceeded: max 60 searches per minute")
    else:
        redis_client.incr(key)
```

---

## Testing Strategy

### Test Pyramid Distribution

- **Unit Tests (60%)**:  15 hours
- **Integration Tests (30%)**: 7.5 hours
- **E2E Tests (10%)**: 2.5 hours

**Total**: 25 hours testing (20% of 120-hour sprint)

### Unit Test Coverage

**QueryBuilder** (20 tests)
```python
def test_parse_simple_query():
    qb = QueryBuilder()
    query = qb._parse_query("diabetes")
    assert query['bool']['should'][0]['match']['title']['query'] == 'diabetes'

def test_parse_boolean_and_query():
    qb = QueryBuilder()
    query = qb._parse_query("diabetes AND hypertension")
    assert len(query['bool']['must']) == 2

def test_parse_phrase_query():
    qb = QueryBuilder()
    query = qb._parse_query('"chest pain"')
    assert query['bool']['must'][0]['multi_match']['type'] == 'phrase'

def test_apply_document_type_filter():
    qb = QueryBuilder()
    filters = SearchFilters(document_types=['clinical_note'])
    query = qb._apply_filters({'bool': {}}, filters)
    assert query['bool']['filter'][0]['terms']['document_type'] == ['clinical_note']
```

**SearchService** (15 tests)
```python
@pytest.mark.asyncio
async def test_search_documents_returns_results(mock_es, mock_db, mock_audit):
    service = SearchService(mock_es, mock_db, mock_audit)
    request = SearchRequest(query="diabetes")

    mock_es.search.return_value = {
        'hits': {
            'total': {'value': 10},
            'hits': [...]
        }
    }

    results = await service.search_documents(request, mock_user, '127.0.0.1')
    assert results.total_results == 10

@pytest.mark.asyncio
async def test_search_logs_audit_trail(mock_es, mock_db, mock_audit):
    service = SearchService(mock_es, mock_db, mock_audit)
    await service.search_documents(SearchRequest(query="diabetes"), mock_user, '127.0.0.1')

    mock_audit.log.assert_called_once()
    assert mock_audit.log.call_args[1]['action'] == 'SEARCH_EXECUTED'
```

### Integration Tests

**Search API** (10 tests)
```python
@pytest.mark.asyncio
async def test_search_endpoint_returns_results(async_client, auth_headers, es_with_data):
    response = await async_client.post(
        '/api/v1/search',
        json={'query': 'diabetes'},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data['total_results'] > 0
    assert 'documents' in data

@pytest.mark.asyncio
async def test_search_endpoint_facets(async_client, auth_headers, es_with_data):
    response = await async_client.post(
        '/api/v1/search',
        json={'query': 'diabetes'},
        headers=auth_headers
    )

    data = response.json()
    assert 'facets' in data
    assert len(data['facets']['document_types']) > 0
```

### E2E Tests (Playwright)

**Full search workflow** (5 tests)
```typescript
test('full search workflow with filters', async ({ page }) => {
  // Login
  await page.goto('http://localhost:8080/login')
  await page.fill('input[name="username"]', 'clinician1')
  await page.fill('input[name="password"]', 'password123')
  await page.click('button[type="submit"]')

  // Navigate to search
  await page.goto('http://localhost:8080/search')

  // Execute search
  await page.fill('input[name="search"]', 'diabetes')
  await page.press('input[name="search"]', 'Enter')
  await page.waitForSelector('.search-result')

  // Verify results
  const resultCount = await page.locator('.search-result').count()
  expect(resultCount).toBeGreaterThan(0)

  // Apply filter
  await page.click('input[value="clinical_note"]')
  await page.waitForSelector('.search-result')

  // Save search
  await page.click('button:has-text("Save Search")')
  await page.fill('input[name="name"]', 'Diabetes Notes')
  await page.click('button:has-text("Save")')
  await expect(page.locator('text=Search saved')).toBeVisible()
})
```

---

## Deployment Architecture

### Docker Compose Updates

```yaml
version: '3.8'

services:
  # Existing services (postgres, backend, frontend)

  # Add Elasticsearch service
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - bootstrap.memory_lock=true
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - es_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Add Redis service (for caching)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  # Background indexer job
  indexer:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: ${DATABASE_URL}
      ELASTICSEARCH_URL: http://elasticsearch:9200
    depends_on:
      postgres:
        condition: service_healthy
      elasticsearch:
        condition: service_healthy
    command: python -m app.jobs.search_indexer
    volumes:
      - ./backend:/app

volumes:
  es_data:
    driver: local
  redis_data:
    driver: local
```

### Environment Variables

```bash
# .env
# Search Configuration
ELASTICSEARCH_URL=http://elasticsearch:9200
SEARCH_INDEX_NAME=documents
SEARCH_BATCH_INTERVAL_MINUTES=5
SEARCH_MAX_RESULTS=10000
SEARCH_CACHE_TTL_SECONDS=600

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_CACHE_TTL_SECONDS=600
```

### Background Indexer Job

```python
# app/jobs/search_indexer.py
"""Background job to index documents into Elasticsearch"""
import asyncio
from app.database import get_db_session
from app.search.elasticsearch_client import get_es_client
from app.services.search_indexer import SearchIndexer
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BATCH_INTERVAL_MINUTES = int(os.getenv('SEARCH_BATCH_INTERVAL_MINUTES', 5))

async def run_indexer():
    """Run indexer in continuous loop"""
    while True:
        try:
            async with get_db_session() as db:
                async with get_es_client() as es:
                    indexer = SearchIndexer(es, db)
                    count = await indexer.index_documents_batch()
                    logger.info(f"Indexed {count} documents")

        except Exception as e:
            logger.error(f"Indexer error: {e}")

        # Sleep for batch interval
        await asyncio.sleep(BATCH_INTERVAL_MINUTES * 60)

if __name__ == '__main__':
    asyncio.run(run_indexer())
```

---

## Performance Requirements

### Response Time Targets

| Operation | Target | Max Acceptable | Optimization Strategy |
|-----------|--------|----------------|----------------------|
| Simple queries (<3 terms) | <1s | 1.5s | ES caching, Redis query cache |
| Complex queries (>3 terms, filters) | <2s | 3s | Query optimization, index tuning |
| Autocomplete suggestions | <200ms | 500ms | Redis cache, ES suggester |
| Faceted search updates | <500ms | 1s | ES aggregations, caching |
| Export CSV (<1000 docs) | <5s | 10s | Streaming response |
| Export FHIR (<100 docs) | <3s | 5s | Async generation |

### Load Testing

**Locust test script** (`tests/performance/search_load_test.py`)
```python
from locust import HttpUser, task, between

class SearchLoadTest(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        # Login
        response = self.client.post('/api/v1/auth/login', json={
            'username': 'test_user',
            'password': 'test_password'
        })
        self.token = response.json()['access_token']
        self.headers = {'Authorization': f'Bearer {self.token}'}

    @task(5)
    def search_simple_query(self):
        self.client.post('/api/v1/search', json={
            'query': 'diabetes'
        }, headers=self.headers)

    @task(3)
    def search_with_filters(self):
        self.client.post('/api/v1/search', json={
            'query': 'diabetes',
            'filters': {
                'document_types': ['clinical_note']
            }
        }, headers=self.headers)

    @task(2)
    def autocomplete(self):
        self.client.get('/api/v1/search/suggestions?q=diabet', headers=self.headers)
```

**Run load test**:
```bash
locust -f tests/performance/search_load_test.py --host=http://localhost:8000 --users=20 --spawn-rate=2
```

### Elasticsearch Tuning

**Index settings for performance**:
```json
{
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 1,
    "refresh_interval": "30s",  // Reduce refresh frequency
    "index": {
      "max_result_window": 10000,
      "mapping": {
        "total_fields": {
          "limit": 2000
        }
      }
    }
  }
}
```

**Query caching** (Redis):
```python
async def search_with_cache(request: SearchRequest) -> SearchResponse:
    # Generate cache key
    cache_key = f"search:{hash(request.json())}"

    # Check cache
    cached = await redis.get(cache_key)
    if cached:
        return SearchResponse.parse_raw(cached)

    # Execute search
    results = await search_service.search_documents(request)

    # Cache results (10 minutes)
    await redis.setex(cache_key, 600, results.json())

    return results
```

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Elasticsearch downtime** | High | Medium | Health checks, circuit breaker, fallback to PostgreSQL basic search |
| **Slow complex queries** | High | Medium | Query timeout (10s), query optimization, caching |
| **Index out of sync** | Medium | Medium | Monitor indexing lag, manual reindex capability |
| **Query injection attacks** | Critical | Low | Input sanitization, query validation, parameterized queries |
| **Storage overflow** | Medium | Low | Index lifecycle management, delete old docs after 2 years |
| **Poor relevance ranking** | Medium | High | Tunable BM25 params, user feedback, A/B testing |
| **Rate limiting bypass** | Medium | Low | Redis-based rate limiting, IP blocking |

**Mitigation: Elasticsearch Circuit Breaker**
```python
class ElasticsearchCircuitBreaker:
    """Circuit breaker for Elasticsearch failures"""

    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker"""
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'half_open'
            else:
                raise Exception("Circuit breaker OPEN - Elasticsearch unavailable")

        try:
            result = await func(*args, **kwargs)
            if self.state == 'half_open':
                self.state = 'closed'
                self.failure_count = 0
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
                logger.error("Circuit breaker OPEN - too many Elasticsearch failures")

            raise
```

---

## Implementation Phases

### Phase 1: Core Search Infrastructure (Week 1, 30 hours)

**Objective**: Set up Elasticsearch, basic search, and indexing

**Tasks**:
1. **Add Elasticsearch to Docker Compose** (2 hours)
   - Configure Elasticsearch 8.11 service
   - Configure Redis service
   - Add health checks
2. **Create Elasticsearch index mapping** (3 hours)
   - Define documents index schema
   - Create custom analyzer (clinical_analyzer)
   - Test index creation script
3. **Implement SearchIndexer service** (5 hours)
   - Batch indexing logic
   - Document decryption for indexing
   - Concept extraction integration
4. **Background indexer job** (3 hours)
   - Continuous indexing loop (every 5 minutes)
   - Error handling and logging
   - Monitor indexing lag
5. **Database migrations** (2 hours)
   - Create saved_searches table
   - Create search_analytics table
   - Add indexed flag to documents table
6. **Basic SearchService** (5 hours)
   - search_documents() method
   - Simple keyword search (no boolean yet)
   - BM25 scoring with field boosts
7. **Basic search API endpoint** (3 hours)
   - POST /api/v1/search
   - Request/response schemas
   - Authentication & authorization
8. **Unit tests** (7 hours)
   - SearchIndexer tests (5 tests)
   - SearchService tests (8 tests)
   - API endpoint tests (5 tests)

**Deliverables**:
- ✅ Elasticsearch running and accessible
- ✅ Documents indexed (basic)
- ✅ Simple keyword search working
- ✅ 18 unit tests passing

---

### Phase 2: Advanced Query Parsing (Week 2, 30 hours)

**Objective**: Boolean operators, phrase search, field-specific search

**Tasks**:
1. **QueryBuilder service** (8 hours)
   - Boolean query parsing (AND, OR, NOT)
   - Phrase search ("exact match")
   - Field-specific search (author:"Dr. Smith")
   - Wildcard search (diabet*)
2. **Query parser (Lark grammar)** (6 hours)
   - Define grammar for nested queries
   - Transformer to Elasticsearch DSL
   - Error handling and fallback
3. **Relevance ranking enhancements** (5 hours)
   - Recency boost function
   - Custom scoring weights
   - Explain score API
4. **Search filters** (4 hours)
   - Document type filter
   - Author filter
   - Department filter
   - Date range filter
5. **Unit tests** (7 hours)
   - QueryBuilder tests (15 tests)
   - QueryParser tests (10 tests)

**Deliverables**:
- ✅ Boolean queries working ((diabetes OR hypertension) AND medication)
- ✅ Phrase search working ("chest pain")
- ✅ Field-specific search (author:"Dr. Smith")
- ✅ Filters working (document type, author, date, department)
- ✅ 25 unit tests passing

---

### Phase 3: Frontend Search UI (Week 2, 30 hours)

**Objective**: Search interface, faceted filters, results display

**Tasks**:
1. **SearchView component** (8 hours)
   - Search input with autocomplete
   - Results display with pagination
   - Loading/error states
2. **QueryBuilder component** (6 hours)
   - Visual query builder (drag-and-drop)
   - Query validation and syntax highlighting
   - Toggle simple/advanced mode
3. **FacetFilters component** (5 hours)
   - Document type facets
   - Author facets
   - Department facets
   - Date range slider
4. **SearchResult component** (4 hours)
   - Document title and metadata
   - Keyword highlighting
   - Context snippets
   - Relevance score display
5. **Autocomplete suggestions** (3 hours)
   - GET /api/v1/search/suggestions endpoint
   - Frontend autocomplete dropdown
   - Debouncing (300ms)
6. **Unit tests** (4 hours)
   - SearchView tests (5 tests)
   - QueryBuilder tests (4 tests)
   - FacetFilters tests (3 tests)
   - SearchResult tests (3 tests)

**Deliverables**:
- ✅ Search UI working (input, results, pagination)
- ✅ Faceted filters working
- ✅ Keyword highlighting in results
- ✅ Autocomplete suggestions working
- ✅ 15 frontend tests passing

---

### Phase 4: Saved Searches & Export (Week 3, 15 hours)

**Objective**: Save searches, export results

**Tasks**:
1. **Saved searches API** (4 hours)
   - POST /api/v1/search/saved (save search)
   - GET /api/v1/search/saved (list saved searches)
   - DELETE /api/v1/search/saved/{id} (delete)
2. **SavedSearches component** (3 hours)
   - Saved searches sidebar
   - Execute saved search
   - Edit/delete saved search
3. **Export service** (5 hours)
   - Export to CSV (document list)
   - Export to JSON (machine-readable)
   - Export to FHIR R4 (DocumentReference bundle)
4. **Unit tests** (3 hours)
   - Saved searches API tests (5 tests)
   - Export service tests (6 tests)

**Deliverables**:
- ✅ Saved searches working (save, list, execute, delete)
- ✅ Export to CSV/JSON/FHIR working
- ✅ 11 unit tests passing

---

### Phase 5: Search Analytics & Admin (Week 3, 15 hours)

**Objective**: Search analytics tracking and admin dashboard

**Tasks**:
1. **AnalyticsService** (4 hours)
   - Track search queries
   - Track clicked results
   - Aggregate analytics (top queries, zero-result, slow)
2. **Search analytics API** (3 hours)
   - GET /api/v1/search/analytics (admin only)
   - Filters (user, date range)
   - Export analytics to CSV
3. **SearchAnalytics component** (5 hours)
   - Admin analytics dashboard
   - Top queries chart (bar chart)
   - Search trends chart (line chart)
   - Zero-result queries list
4. **Unit tests** (3 hours)
   - AnalyticsService tests (5 tests)
   - Analytics API tests (4 tests)

**Deliverables**:
- ✅ Search analytics tracked (all searches logged)
- ✅ Admin analytics dashboard working
- ✅ 9 unit tests passing

---

### Phase 6: Testing & Hardening (Week 4, 25 hours)

**Objective**: Comprehensive testing, performance validation, security audit

**Tasks**:
1. **Integration tests** (10 hours)
   - Search API integration tests (10 tests)
   - Saved searches integration tests (5 tests)
   - Export integration tests (5 tests)
   - Analytics integration tests (3 tests)
2. **E2E tests** (5 hours)
   - Full search workflow (Playwright)
   - Save search workflow
   - Export workflow
3. **Performance testing** (4 hours)
   - Load testing with Locust (20 concurrent users)
   - Measure response times (simple/complex queries)
   - Optimize slow queries
4. **Security audit** (3 hours)
   - Query injection testing
   - Rate limiting validation
   - Audit logging verification
5. **Documentation** (3 hours)
   - API documentation (OpenAPI)
   - User guide (search syntax, tips)
   - Admin guide (analytics, configuration)

**Deliverables**:
- ✅ 23 integration tests passing
- ✅ 5 E2E tests passing
- ✅ Load testing: 20 concurrent users, <2s avg response time
- ✅ Security audit: 0 critical issues
- ✅ Documentation complete

---

## Summary

**Total Estimated Duration**: 120 hours (4 weeks)

**Phase Breakdown**:
- Phase 1: Core Infrastructure (30 hours)
- Phase 2: Advanced Query Parsing (30 hours)
- Phase 3: Frontend UI (30 hours)
- Phase 4: Saved Searches & Export (15 hours)
- Phase 5: Analytics & Admin (15 hours)

**Total Tests**: ~150 tests
- Unit tests: ~90 tests
- Integration tests: ~45 tests
- E2E tests: ~15 tests

**Technology Stack**:
- Elasticsearch 8.11+ (full-text search, BM25 scoring)
- Redis (query caching, rate limiting)
- Lark parser (boolean query parsing)
- Vue 3 + Vuetify (search UI)

**Key Features Delivered**:
- Full-text search with Boolean operators (AND, OR, NOT, parentheses)
- Phrase search, wildcard search, field-specific search
- BM25 relevance ranking with field boosting and recency boost
- Faceted search (document type, author, department, date)
- Search result highlighting and context snippets
- Saved searches (save, share, execute)
- Export capabilities (CSV, JSON, FHIR R4)
- Search analytics dashboard (top queries, zero-result, slow)
- Comprehensive audit logging (HIPAA compliant)

**Next Steps**:
1. **Get user approval** on technical plan
2. **Create task breakdown** (`.specify/tasks/sprint-3-full-text-search-tasks.md`)
3. **Begin Phase 1 implementation** (Elasticsearch setup)

---

**Ready for Implementation!** ✅
