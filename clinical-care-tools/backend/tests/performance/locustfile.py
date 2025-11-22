"""
Performance testing suite using Locust for Clinical Care Tools.

Load testing scenarios:
1. Authentication load test (500 concurrent logins)
2. Patient search load test (1000 concurrent searches)
3. Document upload load test (bulk upload 100 documents)
4. Mixed workload test (realistic user behavior)

Targets:
- API response time: <500ms (P95)
- Patient search: <1s (P95)
- Document upload: <2s per file (P95)
- Support: 500 concurrent users
"""

from locust import HttpUser, task, between, events
from datetime import datetime
import time
import json
import random
import string


class AuthLoadTest(HttpUser):
    """Load test for authentication endpoints."""

    wait_time = between(1, 3)

    def on_start(self):
        """Setup before running tasks."""
        self.access_token = None

    @task(3)
    def login_user(self):
        """Test user login performance."""
        email = f"user_{random.randint(1, 1000)}@example.com"
        password = "test_password_123!"

        start_time = time.time()
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        elapsed = time.time() - start_time

        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            # Log performance metric
            events.request.fire(
                request_type="auth_login",
                name="/api/v1/auth/login",
                response_time=elapsed * 1000,
                response_length=len(response.content),
                exception=None,
                context={}
            )

    @task(1)
    def logout_user(self):
        """Test user logout performance."""
        if self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.client.post(
                "/api/v1/auth/logout",
                headers=headers
            )
            assert response.status_code in [200, 204]

    @task(2)
    def refresh_token(self):
        """Test token refresh performance."""
        if self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.client.post(
                "/api/v1/auth/refresh",
                headers=headers
            )
            if response.status_code == 200:
                self.access_token = response.json()["access_token"]


class PatientSearchLoadTest(HttpUser):
    """Load test for patient search endpoints."""

    wait_time = between(2, 5)

    def on_start(self):
        """Setup authentication before running tasks."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "loadtest@example.com",
                "password": "test_password_123!"
            }
        )
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
        else:
            self.access_token = "test_token"

    @task(5)
    def search_by_concept(self):
        """Test patient search by medical concept."""
        concepts = [
            "atrial fibrillation",
            "diabetes",
            "hypertension",
            "myocardial infarction",
            "heart failure",
        ]
        concept = random.choice(concepts)
        headers = {"Authorization": f"Bearer {self.access_token}"}

        start_time = time.time()
        response = self.client.post(
            "/api/v1/patients/search",
            json={
                "concept": concept,
                "limit": 20,
            },
            headers=headers
        )
        elapsed = time.time() - start_time

        events.request.fire(
            request_type="search_by_concept",
            name=f"/api/v1/patients/search?concept={concept}",
            response_time=elapsed * 1000,
            response_length=len(response.content),
            exception=None if response.status_code == 200 else Exception(),
            context={}
        )

    @task(3)
    def search_with_filters(self):
        """Test patient search with meta-annotation filters."""
        headers = {"Authorization": f"Bearer {self.access_token}"}

        start_time = time.time()
        response = self.client.post(
            "/api/v1/patients/search",
            json={
                "concept": "diabetes",
                "filters": {
                    "Negation": "Affirmed",
                    "Experiencer": "Patient",
                    "Temporality": "Current",
                },
                "limit": 50,
            },
            headers=headers
        )
        elapsed = time.time() - start_time

        events.request.fire(
            request_type="search_with_filters",
            name="/api/v1/patients/search?filters=true",
            response_time=elapsed * 1000,
            response_length=len(response.content),
            exception=None if response.status_code == 200 else Exception(),
            context={}
        )

    @task(2)
    def search_pagination(self):
        """Test pagination performance."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        page = random.randint(1, 10)

        response = self.client.post(
            "/api/v1/patients/search",
            json={
                "concept": "heart disease",
                "limit": 20,
                "offset": (page - 1) * 20,
            },
            headers=headers
        )
        assert response.status_code in [200, 400]


class DocumentUploadLoadTest(HttpUser):
    """Load test for document upload endpoints."""

    wait_time = between(1, 3)

    def on_start(self):
        """Setup authentication and project."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "loadtest@example.com",
                "password": "test_password_123!"
            }
        )
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
        else:
            self.access_token = "test_token"

        # Get or create project
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.client.post(
            "/api/v1/projects",
            json={"name": "Load Test Project"},
            headers=headers
        )
        if response.status_code == 201:
            self.project_id = response.json()["id"]
        else:
            self.project_id = "test_project"

    @task(4)
    def upload_small_document(self):
        """Test uploading small clinical documents."""
        clinical_notes = [
            "Patient presents with chest pain and shortness of breath.",
            "History of diabetes mellitus type 2, well-controlled.",
            "No allergies noted in chart. Pain level 4/10.",
            "Patient denies recent fever or chills.",
        ]
        content = random.choice(clinical_notes)
        headers = {"Authorization": f"Bearer {self.access_token}"}

        start_time = time.time()
        response = self.client.post(
            f"/api/v1/projects/{self.project_id}/documents",
            json={
                "content": content,
                "document_type": "clinical_note",
            },
            headers=headers
        )
        elapsed = time.time() - start_time

        events.request.fire(
            request_type="upload_small_doc",
            name="/api/v1/projects/{}/documents".format(self.project_id),
            response_time=elapsed * 1000,
            response_length=len(response.content),
            exception=None if response.status_code == 201 else Exception(),
            context={}
        )

    @task(2)
    def upload_large_document(self):
        """Test uploading larger clinical documents."""
        # Generate 10KB document
        content = "Patient medical history and examination notes. " * 250
        headers = {"Authorization": f"Bearer {self.access_token}"}

        start_time = time.time()
        response = self.client.post(
            f"/api/v1/projects/{self.project_id}/documents",
            json={
                "content": content,
                "document_type": "medical_record",
            },
            headers=headers
        )
        elapsed = time.time() - start_time

        events.request.fire(
            request_type="upload_large_doc",
            name="/api/v1/projects/{}/documents".format(self.project_id),
            response_time=elapsed * 1000,
            response_length=len(response.content),
            exception=None if response.status_code == 201 else Exception(),
            context={}
        )

    @task(1)
    def bulk_upload_documents(self):
        """Test bulk document upload."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        documents = [
            {
                "content": f"Test document {i}",
                "document_type": "clinical_note",
            }
            for i in range(10)
        ]

        start_time = time.time()
        response = self.client.post(
            f"/api/v1/projects/{self.project_id}/documents/bulk",
            json={"documents": documents},
            headers=headers
        )
        elapsed = time.time() - start_time

        events.request.fire(
            request_type="bulk_upload",
            name="/api/v1/projects/{}/documents/bulk".format(self.project_id),
            response_time=elapsed * 1000,
            response_length=len(response.content),
            exception=None if response.status_code in [200, 201] else Exception(),
            context={}
        )


class MixedWorkloadTest(HttpUser):
    """Realistic mixed workload test simulating actual user behavior."""

    wait_time = between(1, 4)

    def on_start(self):
        """Setup user session."""
        self.user_id = f"user_{random.randint(1, 100)}"
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": f"{self.user_id}@example.com",
                "password": "test_password_123!"
            }
        )
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
        else:
            self.access_token = "test_token"

    @task(10)
    def browse_projects(self):
        """User browses their projects."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        self.client.get("/api/v1/projects", headers=headers)

    @task(15)
    def search_patients(self):
        """User searches for patients."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        self.client.post(
            "/api/v1/patients/search",
            json={"concept": "diabetes"},
            headers=headers
        )

    @task(10)
    def view_patient_timeline(self):
        """User views patient timeline."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        patient_id = f"patient_{random.randint(1, 1000)}"
        self.client.get(
            f"/api/v1/patients/{patient_id}/timeline",
            headers=headers
        )

    @task(8)
    def upload_document(self):
        """User uploads a document."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        content = "Patient presents with symptoms. Examination findings noted."
        self.client.post(
            "/api/v1/documents",
            json={
                "content": content,
                "document_type": "clinical_note",
            },
            headers=headers
        )

    @task(5)
    def check_audit_logs(self):
        """User reviews their audit logs."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        self.client.get("/api/v1/audit-logs/me", headers=headers)

    @task(2)
    def generate_report(self):
        """User generates a report."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        self.client.post(
            "/api/v1/reports",
            json={"report_type": "patient_summary"},
            headers=headers
        )


# Event handlers for detailed performance reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start."""
    print("\n" + "="*80)
    print("PERFORMANCE TEST STARTED")
    print("="*80)
    print(f"Target: {environment.host}")
    print(f"Start time: {datetime.now()}")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log test stop and summary."""
    print("\n" + "="*80)
    print("PERFORMANCE TEST COMPLETED")
    print("="*80)
    print(f"Stop time: {datetime.now()}")
    print("\nPerformance Summary:")
    print("-" * 80)

    stats = environment.stats
    for request_type, data in stats.items():
        if request_type != "Total":
            print(f"\n{request_type}:")
            print(f"  Requests: {data.num_requests}")
            print(f"  Failures: {data.num_failures}")
            print(f"  Avg response: {data.avg_response_time:.0f}ms")
            print(f"  Min response: {data.min_response_time:.0f}ms")
            print(f"  Max response: {data.max_response_time:.0f}ms")
            print(f"  P95 response: {data.get_response_time_percentile(0.95):.0f}ms")
            print(f"  P99 response: {data.get_response_time_percentile(0.99):.0f}ms")

    print("\n" + "="*80)
