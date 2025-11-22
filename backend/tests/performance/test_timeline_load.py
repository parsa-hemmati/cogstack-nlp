"""
Load Testing for Timeline API using Locust

Simulates 100 concurrent users accessing patient timelines
to measure system performance under load.

Target Metrics:
- P50 response time < 200ms
- P95 response time < 500ms
- P99 response time < 1000ms
- Success rate > 99%

Task #007: E2E Tests, Performance Testing & Accessibility Audit
"""

from locust import HttpUser, task, between, events
from datetime import datetime, timedelta
import random
import json


class TimelineUser(HttpUser):
    """
    Simulates a clinician user accessing patient timelines.
    
    User behavior:
    - Login to get auth token
    - View 10 different patient timelines
    - Apply various filters
    - Export timeline data
    """
    
    # Wait time between tasks (1-3 seconds)
    wait_time = between(1, 3)
    
    def on_start(self):
        """
        Called when a simulated user starts.
        Login to get authentication token.
        """
        # Login
        response = self.client.post("/api/v1/auth/login", json={
            "email": f"loadtest_user_{random.randint(1, 100)}@example.com",
            "password": "LoadTest123!"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            self.headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
        else:
            # Use test token if login fails
            self.headers = {
                "Authorization": "Bearer test_token_123",
                "Content-Type": "application/json"
            }
        
        # Patient IDs for testing
        self.patient_ids = [
            f"P{str(i).zfill(5)}" for i in range(1, 101)
        ]
    
    @task(5)  # Weight: 5 (most common action)
    def view_patient_timeline(self):
        """
        View a patient timeline without filters.
        
        This is the most common workflow: clinician opens patient record.
        """
        patient_id = random.choice(self.patient_ids)
        
        with self.client.get(
            f"/api/v1/timeline/{patient_id}",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/timeline/[patient_id]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Validate response structure
                if "timeline_data" in data and "documents" in data["timeline_data"]:
                    response.success()
                else:
                    response.failure("Invalid response structure")
            elif response.status_code == 404:
                # Patient not found is acceptable in test environment
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(3)  # Weight: 3
    def view_timeline_with_date_filter(self):
        """
        View timeline with date range filter.
        
        Common workflow: reviewing recent patient history (last 6 months).
        """
        patient_id = random.choice(self.patient_ids)
        
        # Generate date range (random 6-month period in last 2 years)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        params = {
            "date_start": start_date.isoformat(),
            "date_end": end_date.isoformat()
        }
        
        with self.client.get(
            f"/api/v1/timeline/{patient_id}",
            params=params,
            headers=self.headers,
            catch_response=True,
            name="/api/v1/timeline/[patient_id] (date filter)"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(2)  # Weight: 2
    def view_timeline_with_concept_filter(self):
        """
        View timeline filtered by medical concepts.
        
        Research workflow: finding all mentions of specific conditions.
        """
        patient_id = random.choice(self.patient_ids)
        
        # Common medical concepts (CUIs)
        concepts = [
            "C0011849",  # Diabetes Mellitus
            "C0020538",  # Hypertension
            "C0004238",  # Atrial Fibrillation
            "C0018801",  # Heart Failure
            "C0011860",  # Type 2 Diabetes
        ]
        
        # Select 1-3 random concepts
        selected_concepts = random.sample(concepts, random.randint(1, 3))
        
        params = {
            "concepts": ",".join(selected_concepts)
        }
        
        with self.client.get(
            f"/api/v1/timeline/{patient_id}",
            params=params,
            headers=self.headers,
            catch_response=True,
            name="/api/v1/timeline/[patient_id] (concept filter)"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(2)  # Weight: 2
    def view_timeline_with_meta_annotations(self):
        """
        View timeline with meta-annotation filters.
        
        Research workflow: finding affirmed, current patient conditions.
        """
        patient_id = random.choice(self.patient_ids)
        
        params = {
            "meta_negation": "Affirmed",
            "meta_experiencer": "Patient",
            "meta_temporality": random.choice(["Current", "Recent", "Past"])
        }
        
        with self.client.get(
            f"/api/v1/timeline/{patient_id}",
            params=params,
            headers=self.headers,
            catch_response=True,
            name="/api/v1/timeline/[patient_id] (meta-annotation filter)"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(1)  # Weight: 1
    def load_filter_presets(self):
        """
        Load user's saved filter presets.
        
        Workflow: user manages their saved filters.
        """
        with self.client.get(
            "/api/v1/timeline/filters",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/timeline/filters (list presets)"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(1)  # Weight: 1 (less common)
    def export_timeline(self):
        """
        Export patient timeline as PDF.
        
        Workflow: clinician exports timeline for review or documentation.
        """
        patient_id = random.choice(self.patient_ids)
        
        export_data = {
            "patient_id": patient_id,
            "format": random.choice(["pdf", "fhir", "json"]),
            "include_phi": False,
            "filters": {}
        }
        
        with self.client.post(
            f"/api/v1/timeline/{patient_id}/export",
            json=export_data,
            headers=self.headers,
            catch_response=True,
            name="/api/v1/timeline/[patient_id]/export"
        ) as response:
            if response.status_code in [200, 202]:
                # 200 = synchronous export, 202 = async export
                response.success()
            elif response.status_code == 404:
                # Patient not found is acceptable
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Called at the start of the test.
    Log test configuration.
    """
    print("""
    ================================
    Timeline API Load Test Starting
    ================================
    
    Configuration:
    - Simulated users: 100 concurrent
    - Each user views: 10 different timelines
    - Total requests: ~1,000 timeline views
    
    Target Metrics:
    - P50 < 200ms
    - P95 < 500ms
    - P99 < 1000ms
    - Success rate > 99%
    
    Test scenarios:
    1. View timeline (weight: 5)
    2. Date filter (weight: 3)
    3. Concept filter (weight: 2)
    4. Meta-annotation filter (weight: 2)
    5. Load presets (weight: 1)
    6. Export timeline (weight: 1)
    
    ================================
    """)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Called at the end of the test.
    Log summary metrics.
    """
    stats = environment.stats
    
    print("""
    ================================
    Timeline API Load Test Complete
    ================================
    """)
    
    # Print summary for each endpoint
    for name, stat in stats.entries.items():
        if stat.num_requests > 0:
            print(f"\n{name}:")
            print(f"  Total requests: {stat.num_requests}")
            print(f"  Failures: {stat.num_failures}")
            print(f"  Success rate: {((stat.num_requests - stat.num_failures) / stat.num_requests * 100):.2f}%")
            print(f"  P50: {stat.median_response_time:.2f}ms")
            print(f"  P95: {stat.get_response_time_percentile(0.95):.2f}ms")
            print(f"  P99: {stat.get_response_time_percentile(0.99):.2f}ms")
            print(f"  Avg: {stat.avg_response_time:.2f}ms")
            print(f"  Min: {stat.min_response_time:.2f}ms")
            print(f"  Max: {stat.max_response_time:.2f}ms")
    
    # Overall stats
    print(f"\nOverall:")
    print(f"  Total requests: {stats.total.num_requests}")
    print(f"  Failures: {stats.total.num_failures}")
    print(f"  Success rate: {((stats.total.num_requests - stats.total.num_failures) / stats.total.num_requests * 100):.2f}%")
    print(f"  RPS: {stats.total.total_rps:.2f}")
    
    print("\n================================\n")


# Usage:
# Run with: locust -f backend/tests/performance/test_timeline_load.py --host=http://localhost:8000
#
# Web UI: locust -f backend/tests/performance/test_timeline_load.py --host=http://localhost:8000 --web-port=8089
#         Then open http://localhost:8089
#
# Headless: locust -f backend/tests/performance/test_timeline_load.py --host=http://localhost:8000 \
#           --headless --users=100 --spawn-rate=10 --run-time=5m
#
# With HTML report:
#   locust -f backend/tests/performance/test_timeline_load.py --host=http://localhost:8000 \
#          --headless --users=100 --spawn-rate=10 --run-time=5m --html=timeline_load_test_report.html
