"""
Export Service

Handles exporting search results to various formats (CSV, JSON, FHIR R4).
"""
import csv
import io
import json
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.search import SearchResultDocument
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class ExportService:
    """
    Service for exporting search results to multiple formats.

    Supports:
    - CSV: Comma-separated values with metadata header
    - JSON: Structured JSON with query metadata
    - FHIR R4: DocumentReference bundle for EHR integration
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize ExportService.

        Args:
            db_session: Database session for audit logging
        """
        self.db = db_session

    async def export_to_csv(
        self,
        results: List[SearchResultDocument],
        query: str,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> bytes:
        """
        Export search results to CSV format.

        CSV includes:
        - Metadata comment header (query, total results, timestamp)
        - Column headers
        - Document rows with all fields

        Args:
            results: List of search result documents
            query: Original search query
            user_id: User ID for audit logging (optional)
            ip_address: IP address for audit logging (optional)

        Returns:
            CSV file content as bytes (UTF-8 encoded)
        """
        # Create CSV in memory
        output = io.StringIO()

        # Write metadata as comment
        timestamp = datetime.utcnow().isoformat()
        metadata = (
            f"# Search Export - Query: {query}, "
            f"Results: {len(results)}, "
            f"Exported: {timestamp}\n"
        )
        output.write(metadata)

        # Write CSV headers and data
        fieldnames = [
            "document_id",
            "title",
            "document_type",
            "author",
            "date",
            "department",
            "relevance_score"
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow({
                "document_id": str(result.document_id),
                "title": result.title,
                "document_type": result.document_type,
                "author": result.author or "",
                "date": result.date.isoformat() if result.date else "",
                "department": result.department or "",
                "relevance_score": result.relevance_score
            })

        # Get CSV as bytes
        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8')

        # Log audit trail
        if user_id:
            await self._log_export_audit(
                user_id=user_id,
                format="csv",
                query=query,
                result_count=len(results),
                ip_address=ip_address
            )

        logger.info(f"Exported {len(results)} results to CSV for query '{query}'")
        return csv_bytes

    async def export_to_json(
        self,
        results: List[SearchResultDocument],
        query: str,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> bytes:
        """
        Export search results to JSON format.

        JSON structure:
        {
            "query": "search query",
            "total_results": 42,
            "exported_at": "2025-01-15T12:30:00Z",
            "documents": [...]
        }

        Args:
            results: List of search result documents
            query: Original search query
            user_id: User ID for audit logging (optional)
            ip_address: IP address for audit logging (optional)

        Returns:
            JSON file content as bytes (UTF-8 encoded)
        """
        # Build JSON structure
        data = {
            "query": query,
            "total_results": len(results),
            "exported_at": datetime.utcnow().isoformat(),
            "documents": [
                {
                    "document_id": str(result.document_id),
                    "title": result.title,
                    "document_type": result.document_type,
                    "author": result.author,
                    "date": result.date.isoformat() if result.date else None,
                    "department": result.department,
                    "relevance_score": result.relevance_score,
                    "highlights": [
                        {
                            "field": h.field,
                            "snippets": h.snippets
                        }
                        for h in result.highlights
                    ]
                }
                for result in results
            ]
        }

        # Serialize to JSON
        json_str = json.dumps(data, indent=2)
        json_bytes = json_str.encode('utf-8')

        # Log audit trail
        if user_id:
            await self._log_export_audit(
                user_id=user_id,
                format="json",
                query=query,
                result_count=len(results),
                ip_address=ip_address
            )

        logger.info(f"Exported {len(results)} results to JSON for query '{query}'")
        return json_bytes

    async def export_to_fhir(
        self,
        results: List[SearchResultDocument],
        query: str,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> bytes:
        """
        Export search results to FHIR R4 DocumentReference bundle.

        FHIR Bundle structure:
        - resourceType: "Bundle"
        - type: "searchset"
        - entry: Array of DocumentReference resources

        Args:
            results: List of search result documents
            query: Original search query
            user_id: User ID for audit logging (optional)
            ip_address: IP address for audit logging (optional)

        Returns:
            FHIR bundle as JSON bytes (UTF-8 encoded)
        """
        # Build FHIR Bundle
        bundle = {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": len(results),
            "timestamp": datetime.utcnow().isoformat(),
            "entry": []
        }

        # Create DocumentReference for each result
        for result in results:
            document_reference = {
                "resource": {
                    "resourceType": "DocumentReference",
                    "id": str(result.document_id),
                    "status": "current",
                    "type": {
                        "text": result.document_type
                    },
                    "subject": {
                        "display": result.department or "Unknown Department"
                    },
                    "date": result.date.isoformat() if result.date else None,
                    "author": [
                        {
                            "display": result.author or "Unknown Author"
                        }
                    ],
                    "content": [
                        {
                            "attachment": {
                                "title": result.title,
                                "contentType": self._get_content_type(result.document_type)
                            }
                        }
                    ],
                    "extension": [
                        {
                            "url": "http://hl7.org/fhir/StructureDefinition/relevance-score",
                            "valueDecimal": result.relevance_score
                        }
                    ]
                }
            }

            bundle["entry"].append(document_reference)

        # Serialize to JSON
        fhir_str = json.dumps(bundle, indent=2)
        fhir_bytes = fhir_str.encode('utf-8')

        # Log audit trail
        if user_id:
            await self._log_export_audit(
                user_id=user_id,
                format="fhir",
                query=query,
                result_count=len(results),
                ip_address=ip_address
            )

        logger.info(f"Exported {len(results)} results to FHIR for query '{query}'")
        return fhir_bytes

    async def _log_export_audit(
        self,
        user_id: UUID,
        format: str,
        query: str,
        result_count: int,
        ip_address: Optional[str] = None
    ):
        """
        Log export action to audit trail.

        Args:
            user_id: User who performed export
            format: Export format (csv, json, fhir)
            query: Search query
            result_count: Number of results exported
            ip_address: IP address (optional)
        """
        audit_service = AuditService(self.db)
        await audit_service.log_action(
            user_id=user_id,
            action="SEARCH_EXPORTED",
            resource_type="search_export",
            resource_id=None,
            metadata={
                "format": format,
                "query": query,
                "result_count": result_count,
                "exported_at": datetime.utcnow().isoformat()
            },
            ip_address=ip_address
        )

    @staticmethod
    def _get_content_type(document_type: str) -> str:
        """
        Map document type to MIME content type.

        Args:
            document_type: Document type (rtf, txt, docx, pdf)

        Returns:
            MIME content type string
        """
        content_type_map = {
            "rtf": "application/rtf",
            "txt": "text/plain",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "pdf": "application/pdf"
        }
        return content_type_map.get(document_type.lower(), "application/octet-stream")
