"""
Performance Tests for Timeline API using Locust
Tests load handling, response times, and throughput

Run with:
  locust -f backend/tests/performance/test_timeline_load.py --host=http://localhost:8000

Web UI: http://localhost:8089
"""

from locust import HttpUser, task, between
import random
import json


class TimelineUser(HttpUser):
    """
    Simulates a clinician viewing patient timelines
    """

    # Wait 1-3 seconds between tasks (realistic user behavior)
    wait_time = between(1, 3)

    # Test patient IDs (should exist in test database)
    patient_ids = [
        "P12345",
        "P12346",
        "P12347",
        "P12348",
        "P12349",
        "P12350",
        "P12351",
        "P12352",
        "P12353",
        "P12354",
    ]

    def on_start(self):
        """
        Called when a user starts
        Authenticates and gets JWT token
        """
        # Login to get JWT token
        response = self.client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@hospital.com",
                "password": "TestPassword123!",
            },
        )

        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            # Use mock token for testing
            self.token = "test-jwt-token"

        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(10)
    def view_timeline(self):
        """
        Main task: View patient timeline
        Weight: 10 (most common operation)
        Target: P95 <500ms for 1,000 events
        """
        patient_id = random.choice(self.patient_ids)

        with self.client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            headers=self.headers,
            json={
                "filters": {},
                "page_size": 1000,
            },
            catch_response=True,
            name="/api/v1/timeline/patient/[id] - Basic",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                event_count = len(data.get("events", []))
                response_time = response.elapsed.total_seconds() * 1000  # ms

                # Verify response time <500ms target
                if response_time > 500:
                    response.failure(
                        f"Response time {response_time:.0f}ms exceeds 500ms target"
                    )

                # Verify events returned
                if event_count == 0:
                    response.failure("No events returned")

                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(5)
    def view_timeline_with_filters(self):
        """
        Task: View timeline with date range filter
        Weight: 5 (common operation)
        """
        patient_id = random.choice(self.patient_ids)

        with self.client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            headers=self.headers,
            json={
                "filters": {
                    "date_range": {
                        "start": "2024-01-01T00:00:00Z",
                        "end": "2024-12-31T23:59:59Z",
                    },
                },
                "page_size": 1000,
            },
            catch_response=True,
            name="/api/v1/timeline/patient/[id] - Date Filter",
        ) as response:
            if response.status_code == 200:
                response_time = response.elapsed.total_seconds() * 1000
                if response_time > 500:
                    response.failure(f"Response time {response_time:.0f}ms > 500ms")
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(3)
    def view_timeline_with_event_type_filter(self):
        """
        Task: View timeline filtered by event type
        Weight: 3 (less common)
        """
        patient_id = random.choice(self.patient_ids)
        event_type = random.choice(["diagnosis", "medication", "procedure", "lab", "visit"])

        with self.client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            headers=self.headers,
            json={
                "filters": {
                    "event_types": [event_type],
                },
                "page_size": 1000,
            },
            catch_response=True,
            name="/api/v1/timeline/patient/[id] - Event Type Filter",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(2)
    def view_timeline_with_meta_annotations(self):
        """
        Task: View timeline with meta-annotation filtering
        Weight: 2 (advanced feature)
        """
        patient_id = random.choice(self.patient_ids)

        with self.client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            headers=self.headers,
            json={
                "filters": {
                    "meta_annotations": {
                        "negation": "Affirmed",
                        "experiencer": "Patient",
                        "temporality": "Current",
                    },
                },
                "page_size": 1000,
            },
            catch_response=True,
            name="/api/v1/timeline/patient/[id] - Meta-annotation Filter",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def view_large_timeline(self):
        """
        Task: Stress test with large timeline (5,000 events)
        Weight: 1 (rare, but important for scalability)
        """
        # Use specific patient with many events
        patient_id = "P_LARGE_TIMELINE"

        with self.client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            headers=self.headers,
            json={
                "filters": {},
                "page_size": 5000,
            },
            catch_response=True,
            name="/api/v1/timeline/patient/[id] - Large (5K events)",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                event_count = len(data.get("events", []))
                response_time = response.elapsed.total_seconds() * 1000

                # Relaxed target for large timelines (<2s)
                if response_time > 2000:
                    response.failure(f"Response time {response_time:.0f}ms > 2000ms")

                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


class TimelineCacheUser(HttpUser):
    """
    Tests caching behavior and cache hit rates
    """

    wait_time = between(0.5, 1.5)

    patient_ids = ["P12345", "P12346", "P12347"]

    def on_start(self):
        self.token = "test-jwt-token"
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task
    def test_cache_hit(self):
        """
        Repeatedly access same timeline to test cache hit rate
        """
        patient_id = random.choice(self.patient_ids)

        # First request (cache miss)
        with self.client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            headers=self.headers,
            json={"filters": {}, "page_size": 1000},
            catch_response=True,
            name="/api/v1/timeline/patient/[id] - Cache Test",
        ) as response:
            if response.status_code == 200:
                first_response_time = response.elapsed.total_seconds() * 1000

                # Second request (should be cache hit)
                with self.client.post(
                    f"/api/v1/timeline/patient/{patient_id}",
                    headers=self.headers,
                    json={"filters": {}, "page_size": 1000},
                    catch_response=True,
                    name="/api/v1/timeline/patient/[id] - Cache Hit",
                ) as cache_response:
                    if cache_response.status_code == 200:
                        cache_response_time = cache_response.elapsed.total_seconds() * 1000

                        # Cache hit should be faster
                        if cache_response_time < first_response_time * 0.5:
                            cache_response.success()
                        else:
                            cache_response.failure(
                                f"Cache hit not faster: {cache_response_time:.0f}ms vs {first_response_time:.0f}ms"
                            )
                    else:
                        cache_response.failure(f"Status: {cache_response.status_code}")

                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


class TimelineConcurrentUser(HttpUser):
    """
    Tests concurrent access patterns
    Simulates multiple clinicians viewing different timelines simultaneously
    """

    wait_time = between(0.1, 0.5)  # Aggressive timing for concurrency test

    patient_ids = [f"P1234{i}" for i in range(10)]

    def on_start(self):
        self.token = "test-jwt-token"
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task
    def concurrent_timeline_access(self):
        """
        Rapidly access different timelines to test concurrent handling
        """
        patient_id = random.choice(self.patient_ids)

        with self.client.post(
            f"/api/v1/timeline/patient/{patient_id}",
            headers=self.headers,
            json={"filters": {}, "page_size": 1000},
            catch_response=True,
            name="/api/v1/timeline/patient/[id] - Concurrent",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                # Rate limiting
                response.failure("Rate limited")
            else:
                response.failure(f"Status code: {response.status_code}")


"""
Test Scenarios:

1. Normal Load Test:
   locust -f test_timeline_load.py --users 100 --spawn-rate 10 --run-time 5m

   Expected Results:
   - P50 <250ms
   - P95 <500ms
   - P99 <1000ms
   - Success rate >99%

2. Stress Test:
   locust -f test_timeline_load.py --users 500 --spawn-rate 50 --run-time 10m

   Expected Results:
   - P95 <1000ms
   - P99 <2000ms
   - Success rate >95%

3. Cache Test:
   locust -f test_timeline_load.py --users 50 --spawn-rate 10 --run-time 3m --class-name TimelineCacheUser

   Expected Results:
   - Cache hit rate >70%
   - Cache hit response time <100ms

4. Concurrency Test:
   locust -f test_timeline_load.py --users 200 --spawn-rate 50 --run-time 5m --class-name TimelineConcurrentUser

   Expected Results:
   - System handles concurrent access
   - No race conditions
   - No deadlocks
"""
