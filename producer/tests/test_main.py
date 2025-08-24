from fastapi.testclient import TestClient
from app.main import app  # Ensure this path matches your actual app structure

client = TestClient(app)

def test_submit_success():
    payload = {
        "email_id": "harika@example.com",
        "first_name": "Harika",
        "last_name": "K",
        "subject": "Test Subject",
        "body": "This is a test complaint."
    }
    response = client.post("/submit", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "saved"
    assert "id" in response.json()

def test_submit_missing_field():
    payload = {
        "email_id": "harika@example.com",
        "first_name": "Harika",
        "last_name": "K",
        "subject": "Test Subject"
        # Missing body
    }
    response = client.post("/submit", json=payload)
    assert response.status_code == 422


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data, dict)
    assert "ok" in json_data or "status" in json_data
    if "status" in json_data:
        assert json_data["status"] == "ok"
    if "ok" in json_data:
        assert json_data["ok"] is True


def test_health_check_wrong_method():
    response = client.post("/health")
    assert response.status_code == 405



# Additional tests for error handling and optional/extra field logic
def test_submit_invalid_json():
    # Send invalid JSON structure
    response = client.post("/submit", data="not a json")
    assert response.status_code == 422


def test_submit_empty_payload():
    # Empty JSON object
    response = client.post("/submit", json={})
    assert response.status_code == 422




def test_health_check_content_type():
    response = client.get("/health")
    assert response.headers["content-type"] == "application/json"


def test_submit_extra_fields():
    payload = {
        "email_id": "harika@example.com",
        "first_name": "Harika",
        "last_name": "K",
        "subject": "Extra Field Test",
        "body": "Test",
        "extra_field": "this should be ignored"
    }
    response = client.post("/submit", json=payload)
    assert response.status_code == 201
    assert "id" in response.json()


# Test for invalid email format
def test_submit_invalid_email_format():
    payload = {
        "email_id": "not-an-email",
        "first_name": "Harika",
        "last_name": "K",
        "subject": "Invalid Email",
        "body": "Testing invalid email format"
    }
    response = client.post("/submit", json=payload)
    assert response.status_code == 422


# Test for blank subject and body
def test_submit_blank_subject_and_body():
    payload = {
        "email_id": "harika@example.com",
        "first_name": "Harika",
        "last_name": "K",
        "subject": "",
        "body": ""
    }
    response = client.post("/submit", json=payload)
    assert response.status_code == 422


# Test for method not allowed on /submit (GET instead of POST)
def test_submit_method_not_allowed():
    response = client.get("/submit")
    assert response.status_code == 405


# Readiness check: all dependencies OK
def test_readiness_when_all_dependencies_ok(monkeypatch):
    from app import main

    class DummySession:
        def execute(self, stmt): return 1
        def close(self): pass

    monkeypatch.setattr(main, "SessionLocal", lambda: DummySession())

    class DummySocket:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass

    def dummy_create_connection(*args, **kwargs): return DummySocket()
    monkeypatch.setattr(main.socket, "create_connection", dummy_create_connection)

    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


# Readiness check: all dependencies fail
def test_readiness_failure(monkeypatch):
    from app import main

    class DummySessionFail:
        def execute(self, stmt): raise Exception("DB unreachable")
        def close(self): pass

    monkeypatch.setattr(main, "SessionLocal", lambda: DummySessionFail())

    def dummy_create_connection(*args, **kwargs): raise Exception("Kafka unreachable")
    monkeypatch.setattr(main.socket, "create_connection", dummy_create_connection)

    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["detail"]["ok"] is False


# Kafka retry logic in /submit
def test_submit_kafka_retry(monkeypatch):
    from app import main
    attempt_counter = {"count": 0}

    def dummy_publish(msg):
        if attempt_counter["count"] < 1:
            attempt_counter["count"] += 1
            raise Exception("Simulated failure")
        return True

    monkeypatch.setattr(main, "publish", dummy_publish)

    payload = {
        "email_id": "retry@example.com",
        "first_name": "Retry",
        "last_name": "Case",
        "subject": "Kafka Retry",
        "body": "This should pass after one failure"
    }

    response = client.post("/submit", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "saved"



