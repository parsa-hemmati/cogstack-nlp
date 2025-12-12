"""
Mock Backend Server for E2E Testing

This is a simple mock backend that simulates the Clinical Care Tools API
for frontend end-to-end testing when the full backend infrastructure
(PostgreSQL, Redis, etc.) is not available.

Run with: python mock_backend.py
Serves on: http://localhost:8000
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import uuid
from datetime import datetime

# Mock data
MOCK_USER = {
    "id": str(uuid.uuid4()),
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "System Administrator",
    "role": "admin",
    "is_active": True,
    "is_verified": True,
    "can_break_glass": True,
    "failed_login_attempts": 0,
    "locked_until": None,
    "last_login_at": datetime.now().isoformat(),
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": datetime.now().isoformat()
}

MOCK_PATIENTS = [
    {"id": "patient-001", "first_name": "John", "last_name": "Smith", "date_of_birth": "1980-05-15", "gender": "male", "mrn": "MRN001"},
    {"id": "patient-002", "first_name": "Jane", "last_name": "Doe", "date_of_birth": "1975-08-22", "gender": "female", "mrn": "MRN002"},
    {"id": "patient-003", "first_name": "Robert", "last_name": "Johnson", "date_of_birth": "1990-12-03", "gender": "male", "mrn": "MRN003"},
]

MOCK_PROJECTS = [
    {"id": "project-001", "name": "Sepsis Research Study", "description": "Clinical study on sepsis detection", "status": "active", "created_at": "2024-01-15T10:00:00Z"},
    {"id": "project-002", "name": "Diabetes Management", "description": "Diabetes patient outcome tracking", "status": "active", "created_at": "2024-02-20T14:30:00Z"},
]

# Mock tokens
VALID_TOKENS = set()


class MockAPIHandler(BaseHTTPRequestHandler):
    def _send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, message, status=400):
        self._send_json_response({"detail": message}, status)

    def _get_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length:
            return json.loads(self.rfile.read(content_length))
        return {}

    def _check_auth(self):
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            return token in VALID_TOKENS
        return False

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self._send_json_response({"status": "healthy", "version": "mock-1.0.0"})
        
        elif self.path == '/api/v1/auth/me':
            if not self._check_auth():
                self._send_error("Not authenticated", 401)
                return
            self._send_json_response(MOCK_USER)
        
        elif self.path == '/api/v1/patients' or self.path.startswith('/api/v1/patients?'):
            if not self._check_auth():
                self._send_error("Not authenticated", 401)
                return
            self._send_json_response({"items": MOCK_PATIENTS, "total": len(MOCK_PATIENTS)})
        
        elif self.path == '/api/v1/projects' or self.path.startswith('/api/v1/projects?'):
            if not self._check_auth():
                self._send_error("Not authenticated", 401)
                return
            self._send_json_response({"items": MOCK_PROJECTS, "total": len(MOCK_PROJECTS)})
        
        elif self.path == '/api/v1/timeline':
            if not self._check_auth():
                self._send_error("Not authenticated", 401)
                return
            self._send_json_response({"events": [], "total": 0})
        
        else:
            self._send_error("Not found", 404)

    def do_POST(self):
        if self.path == '/api/v1/auth/login':
            body = self._get_body()
            username = body.get('username', '')
            password = body.get('password', '')
            
            # Accept common test credentials
            valid_creds = [
                ('admin', 'admin123'),
                ('admin', 'StrongAdminPass1!'),
                ('admin@example.com', 'admin123'),
            ]
            
            if (username, password) in valid_creds:
                access_token = str(uuid.uuid4())
                refresh_token = str(uuid.uuid4())
                VALID_TOKENS.add(access_token)
                
                self._send_json_response({
                    "user": MOCK_USER,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer"
                })
            else:
                self._send_error("Invalid credentials", 401)
        
        elif self.path == '/api/v1/auth/logout':
            auth_header = self.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                VALID_TOKENS.discard(token)
            self._send_json_response({"message": "Logged out"})
        
        elif self.path == '/api/v1/projects':
            if not self._check_auth():
                self._send_error("Not authenticated", 401)
                return
            body = self._get_body()
            new_project = {
                "id": str(uuid.uuid4()),
                "name": body.get("name", "New Project"),
                "description": body.get("description", ""),
                "status": "active",
                "created_at": datetime.now().isoformat()
            }
            MOCK_PROJECTS.append(new_project)
            self._send_json_response(new_project, 201)
        
        elif self.path == '/api/v1/patients':
            if not self._check_auth():
                self._send_error("Not authenticated", 401)
                return
            body = self._get_body()
            new_patient = {
                "id": str(uuid.uuid4()),
                "first_name": body.get("first_name", "Test"),
                "last_name": body.get("last_name", "Patient"),
                "date_of_birth": body.get("date_of_birth", "2000-01-01"),
                "gender": body.get("gender", "unknown"),
                "mrn": body.get("mrn", f"MRN{len(MOCK_PATIENTS)+1:03d}")
            }
            MOCK_PATIENTS.append(new_patient)
            self._send_json_response(new_patient, 201)
        
        else:
            self._send_error("Not found", 404)

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def run_server(port=8000):
    server = HTTPServer(('0.0.0.0', port), MockAPIHandler)
    print(f"Mock Backend Server running on http://localhost:{port}")
    print("Endpoints:")
    print("  POST /api/v1/auth/login - Login (admin/admin123 or admin@example.com/admin123)")
    print("  GET  /api/v1/auth/me - Get current user")
    print("  GET  /api/v1/patients - List patients")
    print("  POST /api/v1/patients - Create patient")
    print("  GET  /api/v1/projects - List projects")
    print("  POST /api/v1/projects - Create project")
    print("  GET  /health - Health check")
    print("\nPress Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    run_server()
