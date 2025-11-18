"""Tests for Elasticsearch index mapping configuration.

Tests ensure:
- Index mapping includes all required fields
- Analyzers configured correctly
- Field types are correct (text, keyword, date)
- Keyword sub-fields present for faceting
"""

import pytest
from app.services.elasticsearch.index_config import (
    DOCUMENTS_INDEX_CONFIG,
    INDEX_NAME,
    create_index,
    delete_index,
    get_index_mapping
)


class TestIndexConfiguration:
    """Test index configuration structure."""

    def test_index_has_settings(self):
        """Test index configuration includes settings."""
        assert "settings" in DOCUMENTS_INDEX_CONFIG
        settings = DOCUMENTS_INDEX_CONFIG["settings"]

        assert settings["number_of_shards"] == 2
        assert settings["number_of_replicas"] == 1
        assert settings["refresh_interval"] == "5s"

    def test_index_has_mappings(self):
        """Test index configuration includes mappings."""
        assert "mappings" in DOCUMENTS_INDEX_CONFIG
        mappings = DOCUMENTS_INDEX_CONFIG["mappings"]

        assert "properties" in mappings
        assert len(mappings["properties"]) > 0

    def test_custom_analyzer_configured(self):
        """Test medical_analyzer is configured correctly."""
        analysis = DOCUMENTS_INDEX_CONFIG["settings"]["analysis"]

        assert "analyzer" in analysis
        assert "medical_analyzer" in analysis["analyzer"]

        medical_analyzer = analysis["analyzer"]["medical_analyzer"]
        assert medical_analyzer["type"] == "custom"
        assert medical_analyzer["tokenizer"] == "standard"
        assert "lowercase" in medical_analyzer["filter"]
        assert "stop" in medical_analyzer["filter"]
        assert "snowball" in medical_analyzer["filter"]

    def test_all_required_fields_present(self):
        """Test all required fields are in mapping."""
        properties = DOCUMENTS_INDEX_CONFIG["mappings"]["properties"]

        required_fields = [
            "document_id",
            "patient_id",
            "title",
            "content",
            "document_type",
            "author",
            "department",
            "date",
            "created_at",
            "updated_at"
        ]

        for field in required_fields:
            assert field in properties, f"Field '{field}' missing from mapping"

    def test_text_fields_have_analyzer(self):
        """Test text fields use medical_analyzer."""
        properties = DOCUMENTS_INDEX_CONFIG["mappings"]["properties"]

        # Title should have analyzer
        assert properties["title"]["type"] == "text"
        assert properties["title"]["analyzer"] == "medical_analyzer"

        # Content should have analyzer
        assert properties["content"]["type"] == "text"
        assert properties["content"]["analyzer"] == "medical_analyzer"

        # Author should have analyzer
        assert properties["author"]["type"] == "text"
        assert properties["author"]["analyzer"] == "medical_analyzer"

    def test_keyword_subfields_for_faceting(self):
        """Test text fields have keyword sub-fields for faceting."""
        properties = DOCUMENTS_INDEX_CONFIG["mappings"]["properties"]

        # Title should have keyword sub-field
        assert "fields" in properties["title"]
        assert "keyword" in properties["title"]["fields"]
        assert properties["title"]["fields"]["keyword"]["type"] == "keyword"

        # Author should have keyword sub-field
        assert "fields" in properties["author"]
        assert "keyword" in properties["author"]["fields"]
        assert properties["author"]["fields"]["keyword"]["type"] == "keyword"

    def test_keyword_fields(self):
        """Test fields that should be keyword type."""
        properties = DOCUMENTS_INDEX_CONFIG["mappings"]["properties"]

        # These fields should be keyword
        assert properties["document_id"]["type"] == "keyword"
        assert properties["patient_id"]["type"] == "keyword"
        assert properties["document_type"]["type"] == "keyword"
        assert properties["department"]["type"] == "keyword"

    def test_date_fields(self):
        """Test date fields are configured correctly."""
        properties = DOCUMENTS_INDEX_CONFIG["mappings"]["properties"]

        # Date field
        assert properties["date"]["type"] == "date"
        assert "format" in properties["date"]

        # Timestamp fields
        assert properties["created_at"]["type"] == "date"
        assert properties["updated_at"]["type"] == "date"


@pytest.mark.asyncio
class TestIndexOperations:
    """Test index creation/deletion operations (requires running Elasticsearch)."""

    @pytest.fixture
    async def es_client(self):
        """Create Elasticsearch client for testing."""
        from elasticsearch import AsyncElasticsearch
        from app.core.config import settings

        client = AsyncElasticsearch(
            hosts=[settings.ELASTICSEARCH_URL],
            verify_certs=False
        )

        yield client

        await client.close()

    @pytest.fixture
    async def clean_index(self, es_client):
        """Ensure test index doesn't exist before test."""
        test_index = "test_documents"

        # Delete index if exists
        if await es_client.indices.exists(index=test_index):
            await es_client.indices.delete(index=test_index)

        yield test_index

        # Cleanup after test
        if await es_client.indices.exists(index=test_index):
            await es_client.indices.delete(index=test_index)

    async def test_create_index_success(self, es_client, clean_index):
        """Test successful index creation."""
        created = await create_index(es_client, clean_index)

        assert created is True

        # Verify index exists
        exists = await es_client.indices.exists(index=clean_index)
        assert exists is True

    async def test_create_index_already_exists(self, es_client, clean_index):
        """Test creating index that already exists returns False."""
        # Create index first time
        await create_index(es_client, clean_index)

        # Try to create again
        created = await create_index(es_client, clean_index)

        assert created is False

    async def test_delete_index_success(self, es_client, clean_index):
        """Test successful index deletion."""
        # Create index first
        await create_index(es_client, clean_index)

        # Delete index
        deleted = await delete_index(es_client, clean_index)

        assert deleted is True

        # Verify index doesn't exist
        exists = await es_client.indices.exists(index=clean_index)
        assert exists is False

    async def test_delete_index_not_exists(self, es_client, clean_index):
        """Test deleting non-existent index returns False."""
        deleted = await delete_index(es_client, clean_index)

        assert deleted is False

    async def test_get_index_mapping(self, es_client, clean_index):
        """Test retrieving index mapping."""
        # Create index
        await create_index(es_client, clean_index)

        # Get mapping
        mapping = await get_index_mapping(es_client, clean_index)

        assert "properties" in mapping
        assert "title" in mapping["properties"]
        assert "content" in mapping["properties"]
