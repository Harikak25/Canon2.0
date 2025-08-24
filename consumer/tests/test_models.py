
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, EmailRecord
from uuid import UUID
import datetime

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

def test_email_record_creation(session):
    record = EmailRecord(
        email_id="test@example.com",
        first_name="John",
        last_name="Doe",
        subject="Test Subject",
        body="This is a test body.",
        attachment_name=None,
        attachment_data=None
    )
    session.add(record)
    session.commit()

    retrieved = session.query(EmailRecord).first()
    assert retrieved.email_id == "test@example.com"
    assert retrieved.first_name == "John"
    assert retrieved.last_name == "Doe"
    assert retrieved.subject == "Test Subject"
    assert isinstance(retrieved.submitted_at, datetime.datetime)
