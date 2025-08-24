import os
import asyncio
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import (
    app,
    set_consumer_running,
    get_consumer_running,
    wait_for_kafka,
    create_consumer,
)

client = TestClient(app)

import logging
import threading

logger = logging.getLogger(__name__)

def test_health_and_root_endpoints():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "complaints-consumer"
    assert "timestamp" in data

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Complaints Consumer Service is running"}

def test_ready_and_consumer_health():
    set_consumer_running(True)
    response = client.get("/health/consumer")
    data = response.json()
    assert data["status"] == "healthy"
    assert data["consumer_running"] is True

    set_consumer_running(False)
    response = client.get("/health/consumer")
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["consumer_running"] is False

def test_set_get_consumer_running_toggle():
    set_consumer_running(True)
    assert get_consumer_running() is True
    set_consumer_running(False)
    assert get_consumer_running() is False

def test_debug_env(monkeypatch):
    monkeypatch.setenv("KAFKA_BROKER", "broker")
    monkeypatch.setenv("KAFKA_TOPIC", "topic")
    monkeypatch.setenv("KAFKA_GROUP", "group")
    monkeypatch.setenv("KAFKA_OFFSET", "earliest")

    response = client.get("/debug/env")
    data = response.json()
    assert data == {
        "KAFKA_BROKER": "broker",
        "KAFKA_TOPIC": "topic",
        "KAFKA_GROUP": "group",
        "KAFKA_OFFSET": "earliest",
    }

def test_openapi_docs():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data

def test_lifespan_startup_shutdown():
    with TestClient(app) as test_client:
        response = test_client.get("/")
        assert response.status_code == 200
        assert get_consumer_running() in [True, False]

@pytest.mark.parametrize("consumer_side_effect, expected_result", [
    (None, True),
    (Exception("fail"), False),
])
def test_wait_for_kafka_success_and_failure(monkeypatch, consumer_side_effect, expected_result):
    class DummyConsumer:
        def __init__(self, *args, **kwargs):
            if consumer_side_effect:
                raise consumer_side_effect

    monkeypatch.setattr("app.main.KafkaConsumer", DummyConsumer)

    result = wait_for_kafka("broker:9092", max_wait_time=1)
    assert result == expected_result

def test_create_consumer_with_and_without_sasl(monkeypatch):
    # SASL path
    monkeypatch.setenv("KAFKA_SASL_USERNAME", "u")
    monkeypatch.setenv("KAFKA_SASL_PASSWORD", "p")
    monkeypatch.setenv("KAFKA_SASL_MECHANISM", "PLAIN")
    monkeypatch.setenv("KAFKA_SECURITY_PROTOCOL", "SASL_SSL")
    consumer = create_consumer("broker:9092", "topic", "group")
    assert consumer is not None
    for var in ["KAFKA_SASL_USERNAME","KAFKA_SASL_PASSWORD","KAFKA_SASL_MECHANISM","KAFKA_SECURITY_PROTOCOL"]:
        monkeypatch.delenv(var, raising=False)

    # No SASL path
    consumer = create_consumer("broker:9092", "topic", "group")
    assert consumer is not None


# --- New tests ---
import types

def test_process_complaint_message_happy_and_error(monkeypatch):
    from app import main as main_mod
    # Prepare a full payload
    payload = {
        "id": "123",
        "first_name": "Alice",
        "subject": "Subject",
        "body": "Body",
        "email": "alice@example.com",
        "attachment_name": "file.txt",
        "attachment_bytes": b"abc"
    }
    called = {}
    def fake_send_email(**kwargs):
        called['sent'] = kwargs
        return True
    monkeypatch.setattr("app.email_sender.send_email", fake_send_email)
    # Should call send_email
    main_mod.process_complaint_message(payload)
    assert 'sent' in called
    # Now simulate send_email raising exception
    def raise_exc(**kwargs):
        raise Exception("fail!")
    monkeypatch.setattr("app.email_sender.send_email", raise_exc)
    # Should not propagate error
    main_mod.process_complaint_message(payload)  # Should not raise


# --- New test: test_test_email_route_failure ---
def test_test_email_route_failure(monkeypatch):
    # Patch send_email to raise
    def raise_exc(*a, **kw):
        raise Exception("fail!")
    monkeypatch.setattr("app.email_sender.send_email", raise_exc)
    # Use client to POST to /test-email
    response = client.post("/test-email", json={
        "to": "a@example.com",
        "subject": "s",
        "body": "b"
    })
    assert response.status_code == 500
    assert "Failed to send test email" in response.text


# --- New test: test_lifespan_shutdown ---
def test_lifespan_shutdown():
    # On exit from TestClient, consumer_running should be False
    with TestClient(app) as test_client:
        assert test_client.get("/").status_code == 200
    # After exiting, consumer_running should be False
    assert get_consumer_running() is False


def test_debug_env_missing(monkeypatch):
    # Clear env vars
    for var in ["KAFKA_BROKER", "KAFKA_TOPIC", "KAFKA_GROUP", "KAFKA_OFFSET"]:
        monkeypatch.delenv(var, raising=False)
    response = client.get("/debug/env")
    data = response.json()
    for var in ["KAFKA_BROKER", "KAFKA_TOPIC", "KAFKA_GROUP", "KAFKA_OFFSET"]:
        assert data[var] == "not set"


def test_start_consumer_with_dummy_handler(monkeypatch):
    from app import main as main_mod
    # Dummy handler to record messages
    handled = []
    def dummy_handler(msg):
        handled.append(msg)
    # Fake consumer yields one message with .value
    class FakeMsg:
        value = {"foo": "bar"}
    class FakeConsumer:
        def __iter__(self):
            yield FakeMsg()
    monkeypatch.setattr(main_mod, "create_consumer", lambda *a, **kw: FakeConsumer())
    monkeypatch.setattr(main_mod, "wait_for_kafka", lambda *a, **kw: True)
    import time
    orig_sleep = time.sleep
    def raise_to_break(*a, **kw):
        raise Exception("break")
    monkeypatch.setattr(time, "sleep", raise_to_break)
    try:
        main_mod.start_consumer(dummy_handler)
    except Exception as e:
        assert str(e) == "break"
    assert handled and handled[0].value == {"foo": "bar"}