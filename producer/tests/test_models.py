import pytest
from app import models
import uuid
from datetime import datetime

def test_email_record_model_fields():
    record = models.EmailRecord(
        id=uuid.uuid4(),
        email_id="user@example.com",
        first_name="John",
        last_name="Doe",
        subject="Test Subject",
        body="This is a test email body.",
        attachment_name="test.txt",
        attachment_data=b"Sample data",
        submitted_at=datetime.utcnow()
    )

    assert record.email_id == "user@example.com"
    assert record.first_name == "John"
    assert record.last_name == "Doe"
    assert record.subject == "Test Subject"
    assert record.body == "This is a test email body."
    assert record.attachment_name == "test.txt"
    assert record.attachment_data == b"Sample data"
    assert isinstance(record.submitted_at, datetime)
