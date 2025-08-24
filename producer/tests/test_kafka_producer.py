import pytest
from unittest.mock import patch, MagicMock
from app import kafka_producer

@pytest.fixture
def valid_payload():
    return {
        "email_id": "abc123",
        "first_name": "Harika",
        "last_name": "K",
        "subject": "Feedback",
        "body": "This is a test message."
    }

def test_publish_success(valid_payload):
    with patch("app.kafka_producer._get_producer") as mock_get_producer:
        mock_producer = MagicMock()
        mock_get_producer.return_value = mock_producer
        kafka_producer.publish(valid_payload)
        mock_producer.send.assert_called_once()
        mock_producer.flush.assert_called_once()

def test_publish_missing_fields():
    invalid_payload = {
        "email_id": "abc123",
        "first_name": "Harika",
        "subject": "Feedback",
        "body": "This is a test message."
    }
    with pytest.raises(ValueError) as exc_info:
        kafka_producer.publish(invalid_payload)
    assert "Missing required fields" in str(exc_info.value)

def test_publish_retries_on_failure(valid_payload):
    with patch("app.kafka_producer._get_producer") as mock_get_producer:
        mock_producer = MagicMock()
        mock_producer.send.side_effect = Exception("Kafka is down")
        mock_get_producer.return_value = mock_producer
        with pytest.raises(Exception):
            kafka_producer.publish(valid_payload)


def test_publish_empty_payload():
    empty_payload = {}
    with pytest.raises(ValueError) as exc_info:
        kafka_producer.publish(empty_payload)
    assert "Missing required fields" in str(exc_info.value)


def test_publish_correct_topic(valid_payload):
    with patch("app.kafka_producer._get_producer") as mock_get_producer:
        mock_producer = MagicMock()
        mock_get_producer.return_value = mock_producer
        kafka_producer.publish(valid_payload)
        args, kwargs = mock_producer.send.call_args
        assert args[0] == "complaints.v1"


def test_publish_calls_send_with_correct_payload(valid_payload):
    with patch("app.kafka_producer._get_producer") as mock_get_producer:
        mock_producer = MagicMock()
        mock_get_producer.return_value = mock_producer
        kafka_producer.publish(valid_payload)
        args, kwargs = mock_producer.send.call_args
        assert args[0] == "complaints.v1"
        assert args[1] == valid_payload
