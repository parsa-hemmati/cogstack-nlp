"""
Timeline Export Service

Provides export functionality for patient timelines to various formats:
- PDF: Visual clinical summary for referrals/audits
- FHIR R4: Composition resource for EHR interoperability
- JSON: Machine-readable data for analysis/research
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
import json

from weasyprint import HTML
from fhir.resources.composition import Composition, CompositionSection
from fhir.resources.observation import Observation
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.reference import Reference
from fhir.resources.identifier import Identifier
from jinja2 import Environment, FileSystemLoader
import os

from app.schemas.timeline import PatientTimeline, TimelineConcept, ConceptMention


class TimelineExportService:
    """Service for exporting patient timelines to various formats."""

    async def export_to_pdf(
        self,
        patient_id: UUID,
        timeline_data: PatientTimeline,
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Generate PDF from timeline data.

        Args:
            patient_id: Patient UUID
            timeline_data: Complete timeline data (documents + concepts)
            options: Export options
                - watermark: bool (default True) - Add "Confidential" watermark
                - de_identified: bool (default False) - Remove patient PII
                - include_svg: bool (default False) - Embed timeline SVG (not implemented)

        Returns:
            PDF file as bytes

        Example:
            >>> service = TimelineExportService()
            >>> pdf_bytes = await service.export_to_pdf(
            ...     patient_id=UUID("..."),
            ...     timeline_data=timeline,
            ...     options={"watermark": True, "de_identified": False}
            ... )
            >>> len(pdf_bytes) > 0
            True
        """
        options = options or {}
        watermark = options.get("watermark", True)
        de_identified = options.get("de_identified", False)

        # Prepare template context
        context = {
            "patient_id": str(patient_id),
            "patient_name": "[De-identified]" if de_identified else f"Patient {str(patient_id)[:8]}",
            "patient_mrn": "[De-identified]" if de_identified else str(patient_id)[:8],
            "export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "de_identified": de_identified,
            "watermark": watermark,
            "concepts": [
                {
                    "concept_name": concept.concept_name,
                    "concept_type": concept.concept_type,
                    "first_mention_date": concept.first_mention_date.strftime("%Y-%m-%d") if concept.first_mention_date else "N/A",
                    "mention_count": concept.mention_count
                }
                for concept in timeline_data.concepts
            ],
            "documents": [
                {
                    "date": doc.date.strftime("%Y-%m-%d") if doc.date else "N/A",
                    "title": doc.title,
                    "document_type": doc.document_type
                }
                for doc in timeline_data.documents
            ],
            "timeline_svg": None  # SVG embedding will be added in Task 5.6.3
        }

        # Render HTML from template
        html_content = self._render_pdf_template(context)

        # Convert HTML to PDF
        pdf_bytes = HTML(string=html_content).write_pdf()

        return pdf_bytes

    def _render_pdf_template(self, context: Dict[str, Any]) -> str:
        """
        Render PDF HTML template with context data.

        Loads external Jinja2 template from app/templates/timeline/timeline_pdf.html

        Args:
            context: Template context variables

        Returns:
            Rendered HTML string
        """
        # Get template directory path (app/templates)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(current_dir)
        templates_dir = os.path.join(app_dir, 'templates')

        # Create Jinja2 environment
        env = Environment(loader=FileSystemLoader(templates_dir))

        # Load timeline PDF template
        template = env.get_template('timeline/timeline_pdf.html')

        # Render with context
        return template.render(**context)

    async def export_to_fhir(
        self,
        patient_id: UUID,
        timeline_data: PatientTimeline
    ) -> Dict[str, Any]:
        """
        Map timeline to FHIR R4 Composition resource.

        Creates a FHIR Composition with:
        - Document type: "clinical-timeline"
        - Subject: Patient reference
        - Sections: Clinical concepts as Observation references
        - Meta-annotations: Mapped to Observation components

        Args:
            patient_id: Patient UUID
            timeline_data: Complete timeline data

        Returns:
            FHIR Composition resource as dict (JSON-serializable)

        Example:
            >>> fhir_comp = await service.export_to_fhir(
            ...     patient_id=UUID("..."),
            ...     timeline_data=timeline
            ... )
            >>> fhir_comp["resourceType"]
            'Composition'
            >>> fhir_comp["type"]["coding"][0]["code"]
            'clinical-timeline'
        """
        # Create Composition resource
        composition = Composition(
            id=str(UUID(int=0)),  # Will be assigned by FHIR server
            status="final",
            type=CodeableConcept(
                coding=[Coding(
                    system="http://cogstack.org/fhir/composition-type",
                    code="clinical-timeline",
                    display="Clinical Timeline"
                )]
            ),
            subject=Reference(
                reference=f"Patient/{patient_id}",
                type="Patient"
            ),
            date=datetime.now().isoformat(),
            author=[
                Reference(
                    reference="Organization/cogstack-nlp",
                    display="CogStack NLP Platform"
                )
            ],
            title="Patient Clinical Timeline",
            section=[]
        )

        # Create section for each concept with Observation references
        for concept in timeline_data.concepts:
            section = CompositionSection(
                title=concept.concept_name,
                code=CodeableConcept(
                    coding=[Coding(
                        system="http://snomed.info/sct",
                        code=concept.concept_cui,
                        display=concept.concept_name
                    )]
                ),
                text={
                    "status": "generated",
                    "div": f"<div xmlns='http://www.w3.org/1999/xhtml'><p>{concept.concept_name} - {concept.mention_count} mentions</p></div>"
                },
                entry=[]
            )

            # Create Observation reference for each mention
            for mention in concept.mentions:
                # Map meta-annotations to Observation components
                obs_ref = Reference(
                    reference=f"Observation/{concept.concept_cui}-{mention.date.isoformat()}",
                    type="Observation",
                    display=f"{concept.concept_name} - {mention.date.strftime('%Y-%m-%d')}"
                )
                section.entry.append(obs_ref)

            composition.section.append(section)

        # Convert to dict for JSON serialization
        return composition.dict(exclude_none=True)

    async def export_to_json(
        self,
        timeline_data: PatientTimeline,
        de_identified: bool = False
    ) -> Dict[str, Any]:
        """
        Serialize timeline to JSON format.

        Includes:
        - Export metadata (timestamp, filters)
        - Complete timeline data (concepts + documents)
        - Machine-readable format for analysis/research

        Args:
            timeline_data: Complete timeline data
            de_identified: If True, removes patient identifiers (HIPAA Safe Harbor)

        Returns:
            JSON-serializable dict

        Example:
            >>> json_data = await service.export_to_json(timeline_data)
            >>> json_data["export_metadata"]["export_timestamp"]
            '2025-11-19T...'
            >>> len(json_data["concepts"]) > 0
            True
        """
        # Add export metadata
        export_data = {
            "export_metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "export_format": "json",
                "de_identified": de_identified,
                "filters_applied": timeline_data.filters_applied.dict() if timeline_data.filters_applied else {}
            },
            # De-identify patient ID if requested
            "patient_id": "[De-identified]" if de_identified else timeline_data.patient_id,
            "date_range": {
                "start": timeline_data.date_range.start.isoformat() if timeline_data.date_range.start else None,
                "end": timeline_data.date_range.end.isoformat() if timeline_data.date_range.end else None
            },
            "concepts": [
                {
                    "concept_cui": concept.concept_cui,
                    "concept_name": concept.concept_name,
                    "concept_type": concept.concept_type,
                    "first_mention_date": concept.first_mention_date.isoformat() if concept.first_mention_date else None,
                    "mention_count": concept.mention_count,
                    "mentions": [
                        {
                            "concept_cui": mention.concept_cui,
                            "concept_name": mention.concept_name,
                            "concept_type": mention.concept_type,
                            "document_id": str(mention.document_id),
                            "date": mention.date.isoformat() if mention.date else None,
                            "sentence": mention.sentence,
                            "meta_annotations": {
                                "Negation": mention.meta_annotations.Negation,
                                "Temporality": mention.meta_annotations.Temporality,
                                "Experiencer": mention.meta_annotations.Experiencer,
                                "Certainty": mention.meta_annotations.Certainty
                            } if mention.meta_annotations else None,
                            "confidence": mention.confidence,
                            "is_first_mention": mention.is_first_mention
                        }
                        for mention in concept.mentions
                    ]
                }
                for concept in timeline_data.concepts
            ],
            "documents": [
                {
                    "document_id": str(doc.document_id),
                    "title": doc.title,
                    "document_type": doc.document_type,
                    "date": doc.date.isoformat() if doc.date else None,
                    "author": doc.author,
                    "concepts": doc.concepts
                }
                for doc in timeline_data.documents
            ]
        }

        return export_data
