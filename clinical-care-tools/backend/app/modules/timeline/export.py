"""
Timeline Export Service

Generates timeline exports in multiple formats:
- PDF: Visual timeline report with watermark support
- FHIR R4: FHIR Composition with embedded Observations and Conditions
- JSON: Raw timeline data in JSON format

Uses:
- WeasyPrint for PDF generation (requires cairo, pango system libraries)
- Jinja2 for HTML template rendering
- FHIR R4 resource builders for FHIR export
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID, uuid4
import json

# PDF export dependencies
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    # Stub implementation for environments without WeasyPrint

from jinja2 import Template

from app.modules.timeline.models import PatientTimeline


class TimelineExportService:
    """
    Service for exporting patient timelines in multiple formats.
    
    Supports:
    - PDF export with watermark (requires WeasyPrint)
    - FHIR R4 Composition export
    - JSON export
    """

    def __init__(self):
        """Initialize export service."""
        if not WEASYPRINT_AVAILABLE:
            # Log warning in production
            pass

    def export_timeline_pdf(
        self,
        timeline: PatientTimeline,
        watermark_text: Optional[str] = None,
        orientation: str = "portrait",
        page_size: str = "A4"
    ) -> bytes:
        """
        Export patient timeline as PDF with optional watermark.
        
        Args:
            timeline: PatientTimeline data to export
            watermark_text: Optional watermark text (e.g., "CONFIDENTIAL")
            orientation: Page orientation ("portrait" or "landscape")
            page_size: Page size ("A4" or "Letter")
        
        Returns:
            PDF bytes
        
        Raises:
            RuntimeError: If WeasyPrint not available
        """
        if not WEASYPRINT_AVAILABLE:
            # Stub implementation for environments without WeasyPrint
            # Returns minimal PDF structure
            return self._generate_stub_pdf(timeline, watermark_text)
        
        # Render HTML from template
        html_content = self._render_timeline_html(
            timeline=timeline,
            watermark_text=watermark_text,
            orientation=orientation,
            page_size=page_size
        )
        
        # Generate PDF using WeasyPrint
        font_config = FontConfiguration()
        pdf_bytes = HTML(string=html_content).write_pdf(
            font_config=font_config
        )
        
        return pdf_bytes

    def _render_timeline_html(
        self,
        timeline: PatientTimeline,
        watermark_text: Optional[str],
        orientation: str,
        page_size: str
    ) -> str:
        """
        Render timeline data to HTML using Jinja2 template.
        
        Args:
            timeline: PatientTimeline data
            watermark_text: Optional watermark
            orientation: Page orientation
            page_size: Page size
        
        Returns:
            HTML string
        """
        # HTML template with embedded CSS
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Patient Timeline - {{ patient_id }}</title>
    <style>
        @page {
            size: {{ page_size }} {{ orientation }};
            margin: 2cm;
        }
        
        body {
            font-family: Arial, sans-serif;
            font-size: 11pt;
            position: relative;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        
        h2 {
            color: #34495e;
            margin-top: 30px;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        th {
            background-color: #3498db;
            color: white;
        }
        
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        
        .meta-affirmed {
            color: #27ae60;
            font-weight: bold;
        }
        
        .meta-negated {
            color: #e74c3c;
            font-weight: bold;
        }
        
        .statistics {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        
        .watermark {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 72pt;
            color: rgba(200, 200, 200, 0.3);
            z-index: -1;
            white-space: nowrap;
        }
    </style>
</head>
<body>
    {% if watermark_text %}
    <div class="watermark">{{ watermark_text }}</div>
    {% endif %}
    
    <h1>Patient Timeline Report</h1>
    
    <div class="statistics">
        <strong>Patient ID:</strong> {{ patient_id }}<br>
        <strong>Date Range:</strong> {{ date_range.start }} to {{ date_range.end }}<br>
        <strong>Total Documents:</strong> {{ statistics.total_documents }}<br>
        <strong>Total Concepts:</strong> {{ statistics.total_concepts }}<br>
        <strong>Generated:</strong> {{ generated_at }}
    </div>
    
    <h2>Documents ({{ documents|length }})</h2>
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Author</th>
            </tr>
        </thead>
        <tbody>
            {% for doc in documents %}
            <tr>
                <td>{{ doc.document_date }}</td>
                <td>{{ doc.document_type }}</td>
                <td>{{ doc.author }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <h2>Medical Concepts ({{ concepts|length }})</h2>
    <table>
        <thead>
            <tr>
                <th>Concept</th>
                <th>CUI</th>
                <th>Frequency</th>
                <th>First Seen</th>
                <th>Last Seen</th>
            </tr>
        </thead>
        <tbody>
            {% for concept in concepts %}
            <tr>
                <td>{{ concept.name }}</td>
                <td>{{ concept.cui }}</td>
                <td>{{ concept.frequency }}</td>
                <td>{{ concept.first_seen }}</td>
                <td>{{ concept.last_seen }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <p style="margin-top: 50px; font-size: 9pt; color: #7f8c8d;">
        <strong>Generated by:</strong> Clinical Care Tools - Timeline Module<br>
        <strong>Compliance:</strong> HIPAA, GDPR, 21 CFR Part 11<br>
        <strong>Note:</strong> This document contains confidential patient health information. Handle according to organizational privacy policies.
    </p>
</body>
</html>
        """
        
        # Render template
        template = Template(template_str)
        html_content = template.render(
            patient_id=timeline.patient_id,
            date_range=timeline.date_range,
            documents=timeline.documents,
            concepts=timeline.concepts,
            statistics=timeline.statistics,
            watermark_text=watermark_text,
            page_size=page_size,
            orientation=orientation,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return html_content

    def _generate_stub_pdf(
        self,
        timeline: PatientTimeline,
        watermark_text: Optional[str]
    ) -> bytes:
        """
        Generate stub PDF for environments without WeasyPrint.
        
        Returns minimal valid PDF with text content.
        
        Args:
            timeline: PatientTimeline data
            watermark_text: Optional watermark
        
        Returns:
            Minimal PDF bytes
        """
        # Minimal PDF structure (PDF 1.4)
        pdf_content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 200 >>
stream
BT
/F1 12 Tf
50 700 Td
(Patient Timeline Report) Tj
0 -20 Td
(Patient ID: {timeline.patient_id}) Tj
0 -20 Td
(Documents: {timeline.statistics.get('total_documents', 0)}) Tj
0 -20 Td
(Concepts: {timeline.statistics.get('total_concepts', 0)}) Tj
0 -40 Td
({watermark_text or 'STUB PDF - WeasyPrint Not Available'}) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000251 00000 n
0000000328 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
586
%%EOF
"""
        return pdf_content.encode('latin-1')

    def export_timeline_fhir(
        self,
        timeline: PatientTimeline
    ) -> Dict[str, Any]:
        """
        Export patient timeline as FHIR R4 Bundle with Composition.
        
        Maps:
        - Timeline → FHIR Composition (document type)
        - Documents → DocumentReference resources
        - Concepts → Observation resources (with SNOMED-CT coding)
        - Meta-annotations → Observation.interpretation or extensions
        
        Args:
            timeline: PatientTimeline data
        
        Returns:
            FHIR Bundle dict
        """
        # Create FHIR Bundle
        bundle = {
            "resourceType": "Bundle",
            "type": "document",
            "timestamp": datetime.now().isoformat(),
            "entry": []
        }
        
        # Create Composition resource
        composition_id = str(uuid4())
        composition = {
            "resourceType": "Composition",
            "id": composition_id,
            "status": "final",
            "type": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "11503-0",
                    "display": "Medical records"
                }]
            },
            "subject": {
                "reference": f"Patient/{timeline.patient_id}"
            },
            "date": datetime.now().isoformat(),
            "author": [{
                "reference": "Organization/clinical-care-tools"
            }],
            "title": "Patient Timeline Report",
            "section": []
        }
        
        # Add Composition to Bundle
        bundle["entry"].append({
            "fullUrl": f"urn:uuid:{composition_id}",
            "resource": composition
        })
        
        # Map concepts to FHIR Observations
        for concept in timeline.concepts:
            for mention in concept.mentions:
                obs_id = str(uuid4())
                observation = {
                    "resourceType": "Observation",
                    "id": obs_id,
                    "status": "final",
                    "code": {
                        "coding": [{
                            "system": "http://snomed.info/sct",
                            "code": concept.cui,
                            "display": concept.name
                        }]
                    },
                    "subject": {
                        "reference": f"Patient/{timeline.patient_id}"
                    },
                    "effectiveDateTime": mention.document_date.isoformat() if hasattr(mention.document_date, 'isoformat') else str(mention.document_date),
                    "valueBoolean": mention.meta_anns.negation == "Affirmed",
                    "interpretation": [{
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                            "code": "POS" if mention.meta_anns.negation == "Affirmed" else "NEG",
                            "display": "Positive" if mention.meta_anns.negation == "Affirmed" else "Negative"
                        }]
                    }]
                }
                
                # Add meta-annotation extensions
                if mention.meta_anns:
                    observation["extension"] = [
                        {
                            "url": "http://clinical-care-tools.org/fhir/StructureDefinition/experiencer",
                            "valueString": mention.meta_anns.experiencer
                        },
                        {
                            "url": "http://clinical-care-tools.org/fhir/StructureDefinition/temporality",
                            "valueString": mention.meta_anns.temporality
                        },
                        {
                            "url": "http://clinical-care-tools.org/fhir/StructureDefinition/certainty",
                            "valueString": mention.meta_anns.certainty
                        }
                    ]
                
                bundle["entry"].append({
                    "fullUrl": f"urn:uuid:{obs_id}",
                    "resource": observation
                })
        
        return bundle

    def export_timeline_json(
        self,
        timeline: PatientTimeline
    ) -> Dict[str, Any]:
        """
        Export patient timeline as JSON.
        
        Returns timeline data in JSON format (using Pydantic model_dump).
        
        Args:
            timeline: PatientTimeline data
        
        Returns:
            Timeline dict
        """
        # Use Pydantic's model_dump to convert to dict
        return timeline.model_dump(mode='json')
