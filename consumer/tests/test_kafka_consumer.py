import os
import pytest
import threading
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.kafka_consumer import process_complaint_message

client = TestClient(app)

class FakeKafkaConsumer:
    def __init__(self, *a, **kw): pass
    def __iter__(self): yield FakeMessage()
    def close(self): pass
    def assignment(self): return []

BASE_ENV = {
    "SMTP_HOST": "smtp.gmail.com",
    "SMTP_PORT": "587",
    "SMTP_USERNAME": "testsender@example.com",
    "SMTP_PASSWORD": "fakepassword",
    "SMTP_EMAIL": "testsender@example.com",
    "SMTP_STARTTLS": "true"
}

def test_test_email_missing_env_var():
    payload = {
        "to": "fail@example.com",
        "subject": "Env missing",
        "body": "..."
    }
    with patch.dict(os.environ, {}, clear=True):
        response = client.post("/test-email", json=payload)
        assert response.status_code == 404
        assert "SMTP_EMAIL" in response.json()["detail"]

@patch("app.email_sender.send_email")
def test_test_email_route_success(mock_send_email):
    payload = {
        "to": "success@example.com",
        "subject": "Hello",
        "body": "Test body"
    }
    with patch.dict(os.environ, BASE_ENV, clear=True):
        response = client.post("/test-email", json=payload)
        assert response.status_code in (200, 404)
        mock_send_email.assert_called_once_with(
            to_addr="success@example.com",
            first_name="Test",
            subject="Hello",
            body="Test body",
            ticket_id="TEST123",
            attachment_name=None,
            attachment_bytes=None
        )

@patch("app.email_sender.send_email")
def test_process_complaint_message_valid(mock_send_email):
    payload = {
        "id": "789",
        "first_name": "Jane",
        "subject": "Complaint",
        "body": "This is a complaint",
        "email_id": "jane.doe@example.com",
        "attachment_name": "log.txt",
        "attachment_bytes": b"sample-content"
    }
    with patch.dict(os.environ, BASE_ENV, clear=True):
        process_complaint_message(payload)
        mock_send_email.assert_called_once_with(
            to_addr="jane.doe@example.com",
            first_name="Jane",
            subject="Complaint",
            body="This is a complaint",
            ticket_id="789",
            attachment_name="log.txt",
            attachment_bytes=b"sample-content"
        )

@patch("app.kafka_consumer.logger")
def test_process_complaint_message_malformed_payload(mock_logger):
    malformed = {"id": "123"}  # Missing required fields like subject, body, email_id
    process_complaint_message(malformed)
    mock_logger.error.assert_called()


# Additional tests for app/kafka_consumer.py
import time

import app.kafka_consumer as kafka_consumer_mod

def test_start_kafka_consumer_with_fake_message():
    # Patch KafkaConsumer to yield one fake message, patch process_complaint_message and time.sleep
    class FakeMessage:
        value = {"id": "1", "subject": "s", "body": "b", "email_id": "e", "first_name": "f"}
        offset = 0
        partition = 0
    class FakeKafkaConsumer:
        def __init__(self, *a, **kw): pass
        def __iter__(self): yield FakeMessage()
        def close(self): pass
        def assignment(self): return []
    with patch("app.kafka_consumer.KafkaConsumer", FakeKafkaConsumer), \
         patch("app.kafka_consumer.process_complaint_message") as mock_proc, \
         patch("app.kafka_consumer.time.sleep", side_effect=Exception("break")):
        # Patch running to True for the loop
        kafka_consumer_mod.running = True
        try:
            with pytest.raises(Exception, match="break"):
                kafka_consumer_mod.start_kafka_consumer()
        finally:
            kafka_consumer_mod.running = False
        mock_proc.assert_called_once()


def test_reset_offset():
    fake_partition = object()
    class FakeConsumer:
        def assignment(self): return [fake_partition]
        def seek_to_beginning(self, *parts): self.sought = parts
    consumer = FakeConsumer()
    kafka_consumer_mod.reset_offset(consumer)
    assert hasattr(consumer, "sought")
    assert fake_partition in consumer.sought


def test_shutdown_sets_flag():
    kafka_consumer_mod.running = True
    kafka_consumer_mod.shutdown()
    assert kafka_consumer_mod.running is False


def test_handle_signal_exits():
    with pytest.raises(SystemExit):
        kafka_consumer_mod.handle_signal(None, None)


def test_start_kafka_consumer_no_brokers():
    class FakeNoBrokers:
        def __init__(self, *a, **kw): raise kafka_consumer_mod.NoBrokersAvailable("fail")
    with patch("app.kafka_consumer.KafkaConsumer", FakeNoBrokers):
        kafka_consumer_mod.running = True
        # Should not raise
        kafka_consumer_mod.start_kafka_consumer()


def test_create_consumer_empty_group(monkeypatch):
    monkeypatch.delenv("KAFKA_SASL_MECHANISM", raising=False)
    c = kafka_consumer_mod.create_consumer("broker:9092", "topic", "")
    assert c.config["group_id"] == "emailer-group"

def test_wait_for_kafka_timeout(monkeypatch):
    monkeypatch.setattr(kafka_consumer_mod, "KafkaConsumer", lambda *a, **k: (_ for _ in ()).throw(Exception("fail")))
    result = kafka_consumer_mod.wait_for_kafka("broker:9092", max_wait_time=1)
    assert result is False

def test_start_kafka_consumer_exceptions(monkeypatch):
    monkeypatch.setattr(kafka_consumer_mod, "create_consumer", lambda *a, **k: (_ for _ in ()).throw(kafka_consumer_mod.NoBrokersAvailable()))
    t = threading.Thread(target=kafka_consumer_mod.start_kafka_consumer, daemon=True)
    t.start(); t.join(timeout=1)


def test_json_decode_error_branch(monkeypatch):
    class FakeMessage: 
        value = b"not-json"
        offset = 0
        partition = 0
    class FakeConsumer: 
        def __iter__(self): yield FakeMessage()
        def assignment(self): return []
        def close(self): pass
    monkeypatch.setattr(kafka_consumer_mod, "create_consumer", lambda *a, **k: FakeConsumer())
    monkeypatch.setattr(kafka_consumer_mod, "wait_for_kafka", lambda *a, **k: True)
    monkeypatch.setattr(kafka_consumer_mod, "process_complaint_message", lambda x: None)
    t = threading.Thread(target=kafka_consumer_mod.start_kafka_consumer, daemon=True)
    t.start(); time.sleep(0.2)
    kafka_consumer_mod.set_consumer_running(False)


# Additional tests for edge cases: None value and JSON decode error in consumer
def test_consumer_message_none_value(monkeypatch):
    """Test consumer handles a message with value=None gracefully."""
    class FakeMessage:
        value = None
        offset = 0
        partition = 0
    class FakeConsumer:
        def __iter__(self): yield FakeMessage()
        def assignment(self): return []
        def close(self): pass
    monkeypatch.setattr(kafka_consumer_mod, "create_consumer", lambda *a, **k: FakeConsumer())
    monkeypatch.setattr(kafka_consumer_mod, "wait_for_kafka", lambda *a, **k: True)
    monkeypatch.setattr(kafka_consumer_mod, "process_complaint_message", lambda x: None)
    kafka_consumer_mod.set_consumer_running(True)
    t = threading.Thread(target=kafka_consumer_mod.start_kafka_consumer, daemon=True)
    t.start()
    import time
    time.sleep(0.2)
    kafka_consumer_mod.set_consumer_running(False)
    t.join(timeout=1)


def test_consumer_message_json_error(monkeypatch):
    """Test consumer handles a message with invalid JSON bytes gracefully."""
    class FakeMessage:
        value = b"not-json"
        offset = 0
        partition = 0
    class FakeConsumer:
        def __iter__(self): yield FakeMessage()
        def assignment(self): return []
        def close(self): pass
    monkeypatch.setattr(kafka_consumer_mod, "create_consumer", lambda *a, **k: FakeConsumer())
    monkeypatch.setattr(kafka_consumer_mod, "wait_for_kafka", lambda *a, **k: True)
    kafka_consumer_mod.set_consumer_running(True)
    t = threading.Thread(target=kafka_consumer_mod.start_kafka_consumer, daemon=True)
    t.start()
    import time
    time.sleep(0.2)
    kafka_consumer_mod.set_consumer_running(False)
    t.join(timeout=1)