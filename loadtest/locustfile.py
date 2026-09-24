import os
import re

from locust import HttpUser, between, task


class BugTrackingUser(HttpUser):
    wait_time = between(1, 3)
    host = os.getenv("LOADTEST_HOST", "http://127.0.0.1:8000")

    def on_start(self):
        username = os.getenv("LOADTEST_USERNAME")
        password = os.getenv("LOADTEST_PASSWORD")
        if not username or not password:
            raise RuntimeError(
                "Set LOADTEST_USERNAME and LOADTEST_PASSWORD before running Locust."
            )

        response = self.client.get("/login/")
        csrf_match = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text
        )
        if not csrf_match:
            raise RuntimeError("Could not find the login CSRF token.")

        self.client.post(
            "/login/",
            data={
                "csrfmiddlewaretoken": csrf_match.group(1),
                "username": username,
                "password": password,
            },
            name="POST /login/",
        )

    @task(5)
    def view_dashboard(self):
        self.client.get("/dashboard/", name="GET /dashboard/")

    @task(2)
    def view_role_dashboard(self):
        self.client.get("/manager_dashboard/", name="GET /manager_dashboard/")
