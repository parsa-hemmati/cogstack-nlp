"""
Timeline Export Service
Handles export of timeline data to PDF, JSON, and FHIR formats
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from fhir.resources.bundle import Bundle
from fhir.resources.documentreference import DocumentReference
from fhir.resources.condition import Condition
from fhir.resources.medicationstatement import MedicationStatement
from fhir.resources.procedure import Procedure
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.reference import Reference
from fhir.resources.identifier import Identifier

from app.schemas.timeline import TimelineResponse, TimelineDocument, TimelineConcept


class TimelineExportService:
    """Service for exporting timeline data in various formats"""

    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "timeline_exports"
        self.temp_dir.mkdir(exist_ok=True)

    def export_to_pdf(
        self, timeline_data: TimelineResponse, patient_name: Optional[str] = None
    ) -> Path:
        """
        Export timeline to PDF format

        Args:
            timeline_data: Timeline data to export
            patient_name: Optional patient name for header

        Returns:
            Path to generated PDF file
        """
        # Create temporary PDF file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"timeline_{timeline_data.patientId}_{timestamp}.pdf"
        filepath = self.temp_dir / filename

        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Container for PDF elements
        story = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#2c3e50"),
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#34495e"),
            spaceAfter=12,
        )
        normal_style = styles["Normal"]

        # Title
        title_text = f"Patient Timeline Report"
        if patient_name:
            title_text += f" - {patient_name}"
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 12))

        # Metadata
        metadata_text = f"""
        <b>Patient ID:</b> {timeline_data.patientId}<br/>
        <b>Generated:</b> {datetime.fromisoformat(timeline_data.metadata.generatedAt).strftime('%Y-%m-%d %H:%M:%S')}<br/>
        <b>Date Range:</b> {timeline_data.dateRange.start} to {timeline_data.dateRange.end}<br/>
        <b>Documents:</b> {timeline_data.metadata.documentCount}<br/>
        <b>Concepts:</b> {timeline_data.metadata.conceptCount}<br/>
        """
        story.append(Paragraph(metadata_text, normal_style))
        story.append(Spacer(1, 20))

        # Documents Section
        story.append(Paragraph("Documents", heading_style))
        if timeline_data.documents:
            doc_data = [["Date", "Type", "Title", "Annotations"]]
            for doc in timeline_data.documents:
                doc_data.append([
                    doc.date,
                    doc.documentType.replace("_", " ").title(),
                    doc.title[:50] + "..." if len(doc.title) > 50 else doc.title,
                    str(doc.annotationCount),
                ])

            doc_table = Table(doc_data, colWidths=[1.2 * inch, 1.2 * inch, 2.5 * inch, 0.8 * inch])
            doc_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ecf0f1")]),
                ])
            )
            story.append(doc_table)
        else:
            story.append(Paragraph("No documents found.", normal_style))

        story.append(Spacer(1, 20))

        # Concepts Section
        story.append(Paragraph("Clinical Concepts", heading_style))
        if timeline_data.concepts:
            # Group concepts by type
            concepts_by_type: Dict[str, List[TimelineConcept]] = {}
            for concept in timeline_data.concepts:
                if concept.conceptType not in concepts_by_type:
                    concepts_by_type[concept.conceptType] = []
                concepts_by_type[concept.conceptType].append(concept)

            # Render each type
            for concept_type, concepts in sorted(concepts_by_type.items()):
                story.append(Spacer(1, 12))
                story.append(Paragraph(concept_type.title(), ParagraphStyle(
                    "ConceptType",
                    parent=styles["Heading3"],
                    fontSize=12,
                    textColor=colors.HexColor("#7f8c8d"),
                    spaceAfter=6,
                )))

                concept_data = [["Concept", "First Mentioned", "Last Mentioned", "Occurrences"]]
                for concept in concepts[:20]:  # Limit to 20 per type
                    concept_data.append([
                        concept.preferredName[:40] + "..." if len(concept.preferredName) > 40 else concept.preferredName,
                        concept.firstMentioned,
                        concept.lastMentioned,
                        str(concept.occurrenceCount),
                    ])

                concept_table = Table(concept_data, colWidths=[2.5 * inch, 1.2 * inch, 1.2 * inch, 0.8 * inch])
                concept_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7f8c8d")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ecf0f1")]),
                    ])
                )
                story.append(concept_table)

                if len(concepts) > 20:
                    story.append(Spacer(1, 6))
                    story.append(Paragraph(f"... and {len(concepts) - 20} more", normal_style))

        else:
            story.append(Paragraph("No concepts found.", normal_style))

        # Build PDF
        doc.build(story)

        return filepath

    def export_to_json(self, timeline_data: TimelineResponse) -> Path:
        """
        Export timeline to JSON format

        Args:
            timeline_data: Timeline data to export

        Returns:
            Path to generated JSON file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"timeline_{timeline_data.patientId}_{timestamp}.json"
        filepath = self.temp_dir / filename

        # Convert to dict and write
        with open(filepath, "w") as f:
            json.dump(timeline_data.model_dump(mode="json"), f, indent=2, default=str)

        return filepath

    def export_to_fhir(self, timeline_data: TimelineResponse) -> Path:
        """
        Export timeline to FHIR R4 Bundle

        Args:
            timeline_data: Timeline data to export

        Returns:
            Path to generated FHIR JSON file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"timeline_{timeline_data.patientId}_{timestamp}_fhir.json"
        filepath = self.temp_dir / filename

        # Create FHIR Bundle
        bundle = Bundle(
            type="collection",
            timestamp=datetime.now(),
            entry=[],
        )

        # Add DocumentReference resources for each document
        for doc in timeline_data.documents:
            doc_ref = self._create_document_reference(doc, timeline_data.patientId)
            bundle.entry.append({
                "fullUrl": f"urn:uuid:{doc.id}",
                "resource": doc_ref.dict(),
            })

        # Add resources for each concept based on type
        for concept in timeline_data.concepts:
            resource = self._create_concept_resource(concept, timeline_data.patientId)
            if resource:
                bundle.entry.append({
                    "fullUrl": f"urn:uuid:{concept.cui}",
                    "resource": resource.dict(),
                })

        # Write FHIR Bundle
        with open(filepath, "w") as f:
            f.write(bundle.json(indent=2))

        return filepath

    def _create_document_reference(
        self, doc: TimelineDocument, patient_id: str
    ) -> DocumentReference:
        """Create FHIR DocumentReference from TimelineDocument"""
        return DocumentReference(
            status="current",
            type=CodeableConcept(
                coding=[
                    Coding(
                        system="http://loinc.org",
                        code=self._get_document_type_loinc_code(doc.documentType),
                        display=doc.documentType.replace("_", " ").title(),
                    )
                ]
            ),
            subject=Reference(reference=f"Patient/{patient_id}"),
            date=datetime.fromisoformat(doc.date),
            description=doc.title,
        )

    def _create_concept_resource(
        self, concept: TimelineConcept, patient_id: str
    ):
        """Create appropriate FHIR resource based on concept type"""
        code = CodeableConcept(
            coding=[
                Coding(
                    system="http://snomed.info/sct",
                    code=concept.cui,
                    display=concept.preferredName,
                )
            ],
            text=concept.preferredName,
        )

        if concept.conceptType == "condition":
            return Condition(
                clinicalStatus=CodeableConcept(
                    coding=[
                        Coding(
                            system="http://terminology.hl7.org/CodeSystem/condition-clinical",
                            code="active",
                            display="Active",
                        )
                    ]
                ),
                code=code,
                subject=Reference(reference=f"Patient/{patient_id}"),
                onsetDateTime=datetime.fromisoformat(concept.firstMentioned),
            )

        elif concept.conceptType == "medication":
            return MedicationStatement(
                status="active",
                medicationCodeableConcept=code,
                subject=Reference(reference=f"Patient/{patient_id}"),
                effectiveDateTime=datetime.fromisoformat(concept.firstMentioned),
            )

        elif concept.conceptType == "procedure":
            return Procedure(
                status="completed",
                code=code,
                subject=Reference(reference=f"Patient/{patient_id}"),
                performedDateTime=datetime.fromisoformat(concept.firstMentioned),
            )

        return None

    def _get_document_type_loinc_code(self, doc_type: str) -> str:
        """Map document type to LOINC code"""
        mapping = {
            "clinical_note": "34109-9",  # Note
            "lab_result": "11502-2",  # Laboratory report
            "discharge_summary": "18842-5",  # Discharge summary
            "radiology_report": "18748-4",  # Diagnostic imaging report
        }
        return mapping.get(doc_type, "34109-9")

    def cleanup_old_exports(self, max_age_hours: int = 24):
        """
        Delete export files older than specified hours

        Args:
            max_age_hours: Maximum age of files to keep
        """
        now = datetime.now()
        for file in self.temp_dir.glob("timeline_*"):
            if file.is_file():
                file_age = datetime.fromtimestamp(file.stat().st_mtime)
                age_hours = (now - file_age).total_seconds() / 3600
                if age_hours > max_age_hours:
                    file.unlink()
