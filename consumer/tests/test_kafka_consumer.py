
import pytest
from fastapi.testclient import TestClient
from app.kafka_consumer import app, get_consumer_running, set_consumer_running

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_consumer_health_check_running():
    set_consumer_running(True)
    response = client.get("/health/consumer")
    assert response.status_code == 200
    assert response.json()["consumer_running"] is True
    assert response.json()["status"] == "healthy"

def test_consumer_health_check_not_running():
    set_consumer_running(False)
    response = client.get("/health/consumer")
    assert response.status_code == 200
    assert response.json()["consumer_running"] is False
    assert response.json()["status"] == "unhealthy"

def test_debug_env():
    response = client.get("/debug/env")
    assert response.status_code == 200
    assert "KAFKA_BROKER" in response.json()
