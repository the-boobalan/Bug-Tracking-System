# Load testing

Install Locust in the virtual environment:

```powershell
pip install locust
```

Start the Django ASGI server in one terminal:

```powershell
uvicorn bug_tracking_system.asgi:application --host 127.0.0.1 --port 8000
```

Set a test account and start Locust from the Django project directory:

```powershell
$env:LOADTEST_USERNAME = "manager-test"
$env:LOADTEST_PASSWORD = "use-a-test-password"
locust -f loadtest/locustfile.py
```

Open `http://127.0.0.1:8089`, choose the number of users and spawn rate, and record response time, failures, and requests per second. Run the test against a staging database, never the production database.
