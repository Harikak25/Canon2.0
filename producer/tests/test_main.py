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





# Test /health when DB connection fails (simulate SessionLocal.execute raising)
def test_health_check_db_failure(monkeypatch):
    from app import main
    class DummySessionFail:
        def execute(self, stmt): raise Exception("DB error")
        def close(self): pass
    monkeypatch.setattr(main, "SessionLocal", lambda: DummySessionFail())
    response = client.get("/health")
    assert response.status_code == 500
    json_data = response.json()
    assert "detail" in json_data
    assert json_data["detail"]["message"] == "Database not reachable"


# Test /ready when DB fails but Kafka succeeds (partial readiness failure)
def test_readiness_db_fails_kafka_ok(monkeypatch):
    from app import main
    class DummySessionFail:
        def execute(self, stmt): raise Exception("DB fail")
        def close(self): pass
    monkeypatch.setattr(main, "SessionLocal", lambda: DummySessionFail())
    class DummySocket:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
    def dummy_create_connection(*args, **kwargs): return DummySocket()
    monkeypatch.setattr(main.socket, "create_connection", dummy_create_connection)
    response = client.get("/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["detail"]["ok"] is False
    assert data["detail"]["db_ok"] is False
    assert data["detail"]["kafka_ok"] is True


# Test /ready when DB succeeds but Kafka fails (other partial failure)
def test_readiness_db_ok_kafka_fails(monkeypatch):
    from app import main
    class DummySession:
        def execute(self, stmt): return 1
        def close(self): pass
    monkeypatch.setattr(main, "SessionLocal", lambda: DummySession())
    def dummy_create_connection(*args, **kwargs): raise Exception("Kafka down")
    monkeypatch.setattr(main.socket, "create_connection", dummy_create_connection)
    response = client.get("/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["detail"]["ok"] is False
    assert data["detail"]["db_ok"] is True
    assert data["detail"]["kafka_ok"] is False


# Test /submit when Kafka publish fails all retries
def test_submit_kafka_fails_all_retries(monkeypatch):
    from app import main
    def always_fail_publish(msg): raise Exception("Kafka always fails")
    monkeypatch.setattr(main, "publish", always_fail_publish)
    payload = {
        "email_id": "failkafka@example.com",
        "first_name": "Fail",
        "last_name": "Kafka",
        "subject": "Kafka Failure",
        "body": "Kafka should fail all retries"
    }
    response = client.post("/submit", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "saved"
    assert data.get("warning") == "Message not queued to Kafka."
# Simulate DB failure during commit in /submit
def test_submit_db_commit_failure(monkeypatch):
    from app import main
    class DummySessionCommitFail:
        def __init__(self):
            self.added = []
        def add(self, obj):
            self.added.append(obj)
        def commit(self):
            raise Exception("Simulated DB commit failure")
        def refresh(self, obj): pass
        def close(self): pass
        def rollback(self): pass
    monkeypatch.setattr(main, "SessionLocal", lambda: DummySessionCommitFail())
    payload = {
        "email_id": "faildb@example.com",
        "first_name": "Fail",
        "last_name": "DB",
        "subject": "DB Failure",
        "body": "This should simulate DB commit failure"
    }
    response = client.post("/submit", json=payload)
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert data["detail"].get("message") == "Database error. Please try again later."