
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_ready_healthy(monkeypatch):
    monkeypatch.setattr("app.main.get_consumer_running", lambda: True)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_ready_unhealthy(monkeypatch):
    monkeypatch.setattr("app.main.get_consumer_running", lambda: False)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "unhealthy"

@pytest.mark.asyncio
async def test_debug_env(monkeypatch):
    monkeypatch.setenv("KAFKA_BROKER", "dummy-broker")
    monkeypatch.setenv("KAFKA_TOPIC", "dummy-topic")
    monkeypatch.setenv("KAFKA_GROUP", "dummy-group")
    monkeypatch.setenv("KAFKA_OFFSET", "earliest")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/debug/env")
    json_data = response.json()
    assert json_data["KAFKA_BROKER"] == "dummy-broker"
    assert json_data["KAFKA_TOPIC"] == "dummy-topic"
    assert json_data["KAFKA_GROUP"] == "dummy-group"
    assert json_data["KAFKA_OFFSET"] == "earliest"
