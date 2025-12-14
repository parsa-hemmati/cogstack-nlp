"""
Comprehensive Mock Backend Server for E2E Testing

Enhanced mock backend with realistic clinical data for testing all modules:
- Authentication & User Management
- Dashboard with statistics
- Patient Search & Patient Details
- Timeline View with clinical events
- Document Management
- Projects & Tasks
- Analytics & Alerts

Run with: python mock_backend_comprehensive.py
Serves on: http://localhost:8000
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import uuid
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

# =============================================================================
# COMPREHENSIVE MOCK DATA
# =============================================================================

# Users
MOCK_USERS = [
    {
        "id": "user-001",
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Dr. Sarah Admin",
        "role": "admin",
        "is_active": True,
        "is_verified": True,
        "can_break_glass": True,
        "department": "Administration",
        "created_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": "user-002",
        "username": "clinician",
        "email": "clinician@example.com",
        "full_name": "Dr. James Wilson",
        "role": "clinician",
        "is_active": True,
        "is_verified": True,
        "can_break_glass": True,
        "department": "Internal Medicine",
        "created_at": "2024-02-15T00:00:00Z"
    },
    {
        "id": "user-003",
        "username": "researcher",
        "email": "researcher@example.com",
        "full_name": "Dr. Emily Chen",
        "role": "researcher",
        "is_active": True,
        "is_verified": True,
        "can_break_glass": False,
        "department": "Clinical Research",
        "created_at": "2024-03-10T00:00:00Z"
    }
]

# Patients - Realistic clinical data
MOCK_PATIENTS = [
    {
        "id": "patient-001",
        "mrn": "MRN-2024-001",
        "first_name": "John",
        "last_name": "Smith",
        "date_of_birth": "1965-03-15",
        "gender": "male",
        "age": 59,
        "phone": "+1-555-0101",
        "email": "john.smith@email.com",
        "address": "123 Main St, Boston, MA 02101",
        "primary_diagnosis": "Type 2 Diabetes Mellitus",
        "icd10_codes": ["E11.9", "I10", "E78.5"],
        "allergies": ["Penicillin", "Sulfa drugs"],
        "active_medications": ["Metformin 500mg", "Lisinopril 10mg", "Atorvastatin 20mg"],
        "last_visit": "2024-12-10",
        "risk_score": 7.2,
        "status": "active"
    },
    {
        "id": "patient-002",
        "mrn": "MRN-2024-002",
        "first_name": "Maria",
        "last_name": "Garcia",
        "date_of_birth": "1978-07-22",
        "gender": "female",
        "age": 46,
        "phone": "+1-555-0102",
        "email": "maria.garcia@email.com",
        "address": "456 Oak Ave, Cambridge, MA 02139",
        "primary_diagnosis": "Chronic Obstructive Pulmonary Disease",
        "icd10_codes": ["J44.1", "F32.9", "R05.9"],
        "allergies": ["Aspirin"],
        "active_medications": ["Albuterol inhaler", "Fluticasone", "Sertraline 50mg"],
        "last_visit": "2024-12-08",
        "risk_score": 6.5,
        "status": "active"
    },
    {
        "id": "patient-003",
        "mrn": "MRN-2024-003",
        "first_name": "Robert",
        "last_name": "Johnson",
        "date_of_birth": "1952-11-08",
        "gender": "male",
        "age": 72,
        "phone": "+1-555-0103",
        "email": "robert.johnson@email.com",
        "address": "789 Elm St, Somerville, MA 02143",
        "primary_diagnosis": "Congestive Heart Failure",
        "icd10_codes": ["I50.9", "I48.91", "N18.3"],
        "allergies": ["None known"],
        "active_medications": ["Furosemide 40mg", "Carvedilol 12.5mg", "Warfarin 5mg"],
        "last_visit": "2024-12-12",
        "risk_score": 8.9,
        "status": "critical"
    },
    {
        "id": "patient-004",
        "mrn": "MRN-2024-004",
        "first_name": "Sarah",
        "last_name": "Williams",
        "date_of_birth": "1990-04-30",
        "gender": "female",
        "age": 34,
        "phone": "+1-555-0104",
        "email": "sarah.w@email.com",
        "address": "321 Pine Rd, Brookline, MA 02445",
        "primary_diagnosis": "Rheumatoid Arthritis",
        "icd10_codes": ["M06.9", "M79.3"],
        "allergies": ["Ibuprofen", "NSAIDs"],
        "active_medications": ["Methotrexate 15mg/week", "Folic acid 1mg"],
        "last_visit": "2024-12-05",
        "risk_score": 4.2,
        "status": "stable"
    },
    {
        "id": "patient-005",
        "mrn": "MRN-2024-005",
        "first_name": "David",
        "last_name": "Brown",
        "date_of_birth": "1985-09-12",
        "gender": "male",
        "age": 39,
        "phone": "+1-555-0105",
        "email": "david.brown@email.com",
        "address": "654 Maple Dr, Newton, MA 02458",
        "primary_diagnosis": "Major Depressive Disorder",
        "icd10_codes": ["F33.1", "F41.1", "G47.00"],
        "allergies": ["None known"],
        "active_medications": ["Escitalopram 20mg", "Trazodone 50mg"],
        "last_visit": "2024-12-01",
        "risk_score": 5.1,
        "status": "active"
    }
]

# Timeline Events - Clinical events for patients
MOCK_TIMELINE_EVENTS = [
    {
        "id": "event-001",
        "patient_id": "patient-001",
        "event_type": "lab_result",
        "title": "HbA1c Result",
        "description": "HbA1c: 7.8% (elevated, target <7.0%)",
        "severity": "warning",
        "date": "2024-12-10T09:30:00Z",
        "provider": "Dr. Wilson",
        "details": {"value": 7.8, "unit": "%", "reference_range": "4.0-5.6%"}
    },
    {
        "id": "event-002",
        "patient_id": "patient-001",
        "event_type": "medication_change",
        "title": "Medication Adjustment",
        "description": "Metformin increased from 500mg to 1000mg BID",
        "severity": "info",
        "date": "2024-12-10T10:00:00Z",
        "provider": "Dr. Wilson",
        "details": {"medication": "Metformin", "old_dose": "500mg", "new_dose": "1000mg"}
    },
    {
        "id": "event-003",
        "patient_id": "patient-003",
        "event_type": "critical_alert",
        "title": "Critical: Low Ejection Fraction",
        "description": "Echo shows EF 25% (severely reduced)",
        "severity": "critical",
        "date": "2024-12-12T14:00:00Z",
        "provider": "Dr. Adams",
        "details": {"ef_percentage": 25, "previous_ef": 35}
    },
    {
        "id": "event-004",
        "patient_id": "patient-002",
        "event_type": "visit",
        "title": "Pulmonology Follow-up",
        "description": "Routine COPD management visit, stable spirometry",
        "severity": "info",
        "date": "2024-12-08T11:00:00Z",
        "provider": "Dr. Patel",
        "details": {"fev1": 65, "fvc": 78}
    },
    {
        "id": "event-005",
        "patient_id": "patient-003",
        "event_type": "admission",
        "title": "Hospital Admission",
        "description": "Admitted for acute decompensated heart failure",
        "severity": "critical",
        "date": "2024-12-11T08:00:00Z",
        "provider": "Dr. Wilson",
        "details": {"unit": "CCU", "los_expected": 5}
    }
]

# Documents
MOCK_DOCUMENTS = [
    {
        "id": "doc-001",
        "title": "Discharge Summary - John Smith",
        "document_type": "discharge_summary",
        "patient_id": "patient-001",
        "status": "processed",
        "created_at": "2024-12-10T16:00:00Z",
        "author": "Dr. Wilson",
        "word_count": 1250,
        "entities_found": 23,
        "nlp_status": "completed"
    },
    {
        "id": "doc-002",
        "title": "Progress Note - Maria Garcia",
        "document_type": "progress_note",
        "patient_id": "patient-002",
        "status": "processed",
        "created_at": "2024-12-08T12:00:00Z",
        "author": "Dr. Patel",
        "word_count": 450,
        "entities_found": 12,
        "nlp_status": "completed"
    },
    {
        "id": "doc-003",
        "title": "Admission Note - Robert Johnson",
        "document_type": "admission_note",
        "patient_id": "patient-003",
        "status": "processing",
        "created_at": "2024-12-11T09:00:00Z",
        "author": "Dr. Wilson",
        "word_count": 980,
        "entities_found": 0,
        "nlp_status": "in_progress"
    },
    {
        "id": "doc-004",
        "title": "Sepsis Research Protocol",
        "document_type": "research_protocol",
        "project_id": "project-001",
        "status": "processed",
        "created_at": "2024-11-15T10:00:00Z",
        "author": "Dr. Chen",
        "word_count": 3200,
        "entities_found": 45,
        "nlp_status": "completed"
    }
]

# Projects
MOCK_PROJECTS = [
    {
        "id": "project-001",
        "name": "Sepsis Early Detection Study",
        "description": "AI-powered early sepsis detection using clinical notes and vitals",
        "status": "active",
        "created_at": "2024-01-15T10:00:00Z",
        "owner": "Dr. Emily Chen",
        "team_size": 5,
        "documents_count": 156,
        "patients_enrolled": 89,
        "progress": 65
    },
    {
        "id": "project-002",
        "name": "Diabetes Management Outcomes",
        "description": "Tracking HbA1c improvements with NLP-assisted care",
        "status": "active",
        "created_at": "2024-02-20T14:30:00Z",
        "owner": "Dr. James Wilson",
        "team_size": 3,
        "documents_count": 234,
        "patients_enrolled": 145,
        "progress": 42
    },
    {
        "id": "project-003",
        "name": "Heart Failure Readmission Prediction",
        "description": "Predictive model for 30-day readmission risk",
        "status": "completed",
        "created_at": "2024-03-01T09:00:00Z",
        "owner": "Dr. Sarah Admin",
        "team_size": 4,
        "documents_count": 512,
        "patients_enrolled": 203,
        "progress": 100
    }
]

# Tasks
MOCK_TASKS = [
    {
        "id": "task-001",
        "title": "Review sepsis cohort inclusion criteria",
        "description": "Validate patient selection for sepsis study",
        "status": "in_progress",
        "priority": "high",
        "project_id": "project-001",
        "assignee": "Dr. Chen",
        "due_date": "2024-12-15",
        "created_at": "2024-12-01T10:00:00Z"
    },
    {
        "id": "task-002",
        "title": "Annotate discharge summaries batch #12",
        "description": "NLP annotation review for 25 documents",
        "status": "pending",
        "priority": "medium",
        "project_id": "project-001",
        "assignee": "Dr. Wilson",
        "due_date": "2024-12-18",
        "created_at": "2024-12-05T14:00:00Z"
    },
    {
        "id": "task-003",
        "title": "Generate quarterly analytics report",
        "description": "Compile Q4 2024 patient outcomes data",
        "status": "completed",
        "priority": "high",
        "project_id": "project-002",
        "assignee": "Dr. Admin",
        "due_date": "2024-12-10",
        "created_at": "2024-11-30T09:00:00Z"
    },
    {
        "id": "task-004",
        "title": "Update ICD-10 mapping rules",
        "description": "Review and update clinical coding automation",
        "status": "pending",
        "priority": "low",
        "project_id": "project-002",
        "assignee": "Dr. Chen",
        "due_date": "2024-12-20",
        "created_at": "2024-12-08T11:00:00Z"
    }
]

# Analytics Data
MOCK_ANALYTICS = {
    "summary": {
        "total_patients": 1247,
        "active_patients": 892,
        "critical_patients": 34,
        "documents_processed": 5621,
        "avg_processing_time": 2.3,
        "nlp_accuracy": 94.7
    },
    "trends": {
        "patients_by_month": [
            {"month": "Jul", "count": 156},
            {"month": "Aug", "count": 178},
            {"month": "Sep", "count": 195},
            {"month": "Oct", "count": 212},
            {"month": "Nov", "count": 234},
            {"month": "Dec", "count": 272}
        ],
        "documents_by_type": [
            {"type": "Discharge Summary", "count": 1245},
            {"type": "Progress Note", "count": 2156},
            {"type": "Admission Note", "count": 890},
            {"type": "Lab Report", "count": 1330}
        ],
        "diagnoses_distribution": [
            {"diagnosis": "Diabetes", "percentage": 28},
            {"diagnosis": "Hypertension", "percentage": 35},
            {"diagnosis": "Heart Failure", "percentage": 15},
            {"diagnosis": "COPD", "percentage": 12},
            {"diagnosis": "Other", "percentage": 10}
        ]
    }
}

# Alerts
MOCK_ALERTS = [
    {
        "id": "alert-001",
        "type": "critical_finding",
        "severity": "critical",
        "title": "Critical Lab Value: Potassium 6.2",
        "message": "Patient Robert Johnson (MRN-2024-003) has critically elevated potassium",
        "patient_id": "patient-003",
        "created_at": "2024-12-12T15:30:00Z",
        "acknowledged": False,
        "acknowledged_by": None
    },
    {
        "id": "alert-002",
        "type": "medication_interaction",
        "severity": "warning",
        "title": "Drug Interaction Warning",
        "message": "Potential interaction between Warfarin and new antibiotic order",
        "patient_id": "patient-003",
        "created_at": "2024-12-12T14:00:00Z",
        "acknowledged": True,
        "acknowledged_by": "Dr. Wilson"
    },
    {
        "id": "alert-003",
        "type": "sepsis_screening",
        "severity": "warning",
        "title": "Sepsis Screening Positive",
        "message": "SIRS criteria met for patient in ED - review recommended",
        "patient_id": "patient-001",
        "created_at": "2024-12-11T08:45:00Z",
        "acknowledged": True,
        "acknowledged_by": "Dr. Adams"
    }
]

# Dashboard Stats
MOCK_DASHBOARD = {
    "stats": {
        "total_patients": 1247,
        "active_projects": 2,
        "pending_tasks": 8,
        "unread_alerts": 3,
        "documents_today": 47,
        "critical_patients": 34
    },
    "recent_activity": [
        {"type": "document", "action": "processed", "item": "Discharge Summary - John Smith", "time": "10 mins ago"},
        {"type": "alert", "action": "triggered", "item": "Critical Lab Value", "time": "25 mins ago"},
        {"type": "patient", "action": "admitted", "item": "Robert Johnson", "time": "1 hour ago"},
        {"type": "task", "action": "completed", "item": "Q4 Analytics Report", "time": "2 hours ago"}
    ],
    "quick_actions": [
        {"label": "View Critical Patients", "count": 34, "link": "/patients?status=critical"},
        {"label": "Pending Alerts", "count": 3, "link": "/alerts"},
        {"label": "Documents to Review", "count": 12, "link": "/documents?status=pending"}
    ]
}

# Valid tokens storage
VALID_TOKENS = {}  # token -> user_id

# =============================================================================
# REQUEST HANDLER
# =============================================================================

class ComprehensiveMockHandler(BaseHTTPRequestHandler):
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _send_error(self, message, status=400):
        self._send_json({"detail": message}, status)

    def _get_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length:
            return json.loads(self.rfile.read(content_length))
        return {}

    def _check_auth(self):
        auth = self.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            return auth[7:] in VALID_TOKENS
        return False

    def _get_user(self):
        auth = self.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth[7:]
            user_id = VALID_TOKENS.get(token)
            for user in MOCK_USERS:
                if user['id'] == user_id:
                    return user
        return MOCK_USERS[0]

    def _parse_path(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        path, query = self._parse_path()

        # Health check
        if path == '/health':
            self._send_json({
                "status": "healthy",
                "version": "mock-2.0.0",
                "timestamp": datetime.now().isoformat()
            })
            return

        # Auth endpoints
        if path == '/api/v1/auth/me':
            if not self._check_auth():
                return self._send_error("Not authenticated", 401)
            self._send_json(self._get_user())
            return

        # Protected endpoints - require auth
        if not self._check_auth():
            return self._send_error("Not authenticated", 401)

        # Dashboard
        if path == '/api/v1/dashboard' or path == '/api/v1/dashboard/stats':
            self._send_json(MOCK_DASHBOARD)

        # Patients
        elif path == '/api/v1/patients':
            search = query.get('search', [''])[0].lower()
            status = query.get('status', [''])[0]
            patients = MOCK_PATIENTS
            if search:
                patients = [p for p in patients if search in p['first_name'].lower() or 
                           search in p['last_name'].lower() or search in p['mrn'].lower()]
            if status:
                patients = [p for p in patients if p['status'] == status]
            self._send_json({"items": patients, "total": len(patients)})

        elif path.startswith('/api/v1/patients/') and path.count('/') == 4:
            patient_id = path.split('/')[-1]
            patient = next((p for p in MOCK_PATIENTS if p['id'] == patient_id), None)
            if patient:
                self._send_json(patient)
            else:
                self._send_error("Patient not found", 404)

        # Timeline
        elif path == '/api/v1/timeline':
            patient_id = query.get('patient_id', [''])[0]
            events = MOCK_TIMELINE_EVENTS
            if patient_id:
                events = [e for e in events if e['patient_id'] == patient_id]
            self._send_json({"events": events, "total": len(events)})

        # Documents
        elif path == '/api/v1/documents':
            doc_type = query.get('type', [''])[0]
            status = query.get('status', [''])[0]
            docs = MOCK_DOCUMENTS
            if doc_type:
                docs = [d for d in docs if d['document_type'] == doc_type]
            if status:
                docs = [d for d in docs if d['status'] == status]
            self._send_json({"items": docs, "total": len(docs)})

        elif path.startswith('/api/v1/documents/') and path.count('/') == 4:
            doc_id = path.split('/')[-1]
            doc = next((d for d in MOCK_DOCUMENTS if d['id'] == doc_id), None)
            if doc:
                self._send_json(doc)
            else:
                self._send_error("Document not found", 404)

        # Projects
        elif path == '/api/v1/projects':
            status = query.get('status', [''])[0]
            projects = MOCK_PROJECTS
            if status:
                projects = [p for p in projects if p['status'] == status]
            self._send_json({"items": projects, "total": len(projects)})

        elif path.startswith('/api/v1/projects/') and path.count('/') == 4:
            project_id = path.split('/')[-1]
            project = next((p for p in MOCK_PROJECTS if p['id'] == project_id), None)
            if project:
                self._send_json(project)
            else:
                self._send_error("Project not found", 404)

        # Tasks
        elif path == '/api/v1/tasks':
            status = query.get('status', [''])[0]
            project_id = query.get('project_id', [''])[0]
            tasks = MOCK_TASKS
            if status:
                tasks = [t for t in tasks if t['status'] == status]
            if project_id:
                tasks = [t for t in tasks if t['project_id'] == project_id]
            self._send_json({"items": tasks, "total": len(tasks)})

        # Analytics
        elif path == '/api/v1/analytics' or path == '/api/v1/analytics/summary':
            self._send_json(MOCK_ANALYTICS)

        elif path == '/api/v1/analytics/trends':
            self._send_json(MOCK_ANALYTICS['trends'])

        # Alerts
        elif path == '/api/v1/alerts':
            severity = query.get('severity', [''])[0]
            acknowledged = query.get('acknowledged', [''])[0]
            alerts = MOCK_ALERTS
            if severity:
                alerts = [a for a in alerts if a['severity'] == severity]
            if acknowledged:
                ack_bool = acknowledged.lower() == 'true'
                alerts = [a for a in alerts if a['acknowledged'] == ack_bool]
            self._send_json({"items": alerts, "total": len(alerts)})

        # Users (admin only)
        elif path == '/api/v1/users':
            self._send_json({"items": MOCK_USERS, "total": len(MOCK_USERS)})

        else:
            self._send_error("Not found", 404)

    def do_POST(self):
        path, query = self._parse_path()
        body = self._get_body()

        # Login
        if path == '/api/v1/auth/login':
            username = body.get('username', '')
            password = body.get('password', '')
            
            valid_creds = [
                ('admin', 'admin123'),
                ('admin@example.com', 'admin123'),
                ('clinician', 'clinician123'),
                ('researcher', 'researcher123'),
            ]
            
            if (username, password) in valid_creds:
                user = next((u for u in MOCK_USERS if u['username'] == username or u['email'] == username), MOCK_USERS[0])
                token = str(uuid.uuid4())
                VALID_TOKENS[token] = user['id']
                
                self._send_json({
                    "user": user,
                    "access_token": token,
                    "refresh_token": str(uuid.uuid4()),
                    "token_type": "bearer"
                })
            else:
                self._send_error("Invalid credentials", 401)
            return

        # Logout
        if path == '/api/v1/auth/logout':
            auth = self.headers.get('Authorization', '')
            if auth.startswith('Bearer '):
                VALID_TOKENS.pop(auth[7:], None)
            self._send_json({"message": "Logged out"})
            return

        # Protected endpoints
        if not self._check_auth():
            return self._send_error("Not authenticated", 401)

        # Create patient
        if path == '/api/v1/patients':
            new_patient = {
                "id": str(uuid.uuid4()),
                "mrn": f"MRN-2024-{len(MOCK_PATIENTS)+1:03d}",
                **body,
                "status": "active",
                "risk_score": 5.0
            }
            MOCK_PATIENTS.append(new_patient)
            self._send_json(new_patient, 201)

        # Create project
        elif path == '/api/v1/projects':
            new_project = {
                "id": str(uuid.uuid4()),
                **body,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "progress": 0
            }
            MOCK_PROJECTS.append(new_project)
            self._send_json(new_project, 201)

        # Create task
        elif path == '/api/v1/tasks':
            new_task = {
                "id": str(uuid.uuid4()),
                **body,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            MOCK_TASKS.append(new_task)
            self._send_json(new_task, 201)

        # Acknowledge alert
        elif path.startswith('/api/v1/alerts/') and path.endswith('/acknowledge'):
            alert_id = path.split('/')[4]
            alert = next((a for a in MOCK_ALERTS if a['id'] == alert_id), None)
            if alert:
                alert['acknowledged'] = True
                alert['acknowledged_by'] = self._get_user()['full_name']
                self._send_json(alert)
            else:
                self._send_error("Alert not found", 404)

        # Upload document (mock)
        elif path == '/api/v1/documents/upload':
            new_doc = {
                "id": str(uuid.uuid4()),
                "title": body.get("title", "Uploaded Document"),
                "document_type": body.get("document_type", "other"),
                "status": "processing",
                "created_at": datetime.now().isoformat(),
                "nlp_status": "pending"
            }
            MOCK_DOCUMENTS.append(new_doc)
            self._send_json(new_doc, 201)

        else:
            self._send_error("Not found", 404)

    def do_PUT(self):
        path, query = self._parse_path()
        body = self._get_body()

        if not self._check_auth():
            return self._send_error("Not authenticated", 401)

        # Update task
        if path.startswith('/api/v1/tasks/'):
            task_id = path.split('/')[-1]
            task = next((t for t in MOCK_TASKS if t['id'] == task_id), None)
            if task:
                task.update(body)
                self._send_json(task)
            else:
                self._send_error("Task not found", 404)

        # Update project
        elif path.startswith('/api/v1/projects/'):
            project_id = path.split('/')[-1]
            project = next((p for p in MOCK_PROJECTS if p['id'] == project_id), None)
            if project:
                project.update(body)
                self._send_json(project)
            else:
                self._send_error("Project not found", 404)

        else:
            self._send_error("Not found", 404)

    def do_DELETE(self):
        path, query = self._parse_path()

        if not self._check_auth():
            return self._send_error("Not authenticated", 401)

        # Delete task
        if path.startswith('/api/v1/tasks/'):
            task_id = path.split('/')[-1]
            global MOCK_TASKS
            MOCK_TASKS = [t for t in MOCK_TASKS if t['id'] != task_id]
            self._send_json({"message": "Deleted"})

        else:
            self._send_error("Not found", 404)

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.command} {self.path} - {args[1] if len(args) > 1 else ''}")


# =============================================================================
# SERVER
# =============================================================================

def run_server(port=8000):
    server = HTTPServer(('0.0.0.0', port), ComprehensiveMockHandler)
    print("=" * 60)
    print("  COMPREHENSIVE MOCK BACKEND SERVER")
    print("=" * 60)
    print(f"  Running on: http://localhost:{port}")
    print()
    print("  Test Credentials:")
    print("    - admin@example.com / admin123 (Admin)")
    print("    - clinician / clinician123 (Clinician)")
    print("    - researcher / researcher123 (Researcher)")
    print()
    print("  Available Endpoints:")
    print("    GET  /health")
    print("    POST /api/v1/auth/login")
    print("    GET  /api/v1/auth/me")
    print("    GET  /api/v1/dashboard")
    print("    GET  /api/v1/patients")
    print("    GET  /api/v1/patients/{id}")
    print("    GET  /api/v1/timeline")
    print("    GET  /api/v1/documents")
    print("    GET  /api/v1/projects")
    print("    GET  /api/v1/tasks")
    print("    GET  /api/v1/analytics")
    print("    GET  /api/v1/alerts")
    print("    GET  /api/v1/users")
    print()
    print("  Mock Data:")
    print(f"    - {len(MOCK_PATIENTS)} patients")
    print(f"    - {len(MOCK_DOCUMENTS)} documents")
    print(f"    - {len(MOCK_PROJECTS)} projects")
    print(f"    - {len(MOCK_TASKS)} tasks")
    print(f"    - {len(MOCK_TIMELINE_EVENTS)} timeline events")
    print(f"    - {len(MOCK_ALERTS)} alerts")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    run_server()
