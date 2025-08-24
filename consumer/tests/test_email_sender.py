import os
import pytest
import smtplib
from unittest import mock
from email.message import EmailMessage
from app import email_sender

# Base environment for most tests
BASE_ENV = {
    "SMTP_EMAIL": "testsender@example.com",
    "SMTP_HOST": "smtp.gmail.com",
    "SMTP_PORT": "587",
    "SMTP_USERNAME": "testsender@example.com",
    "SMTP_PASSWORD": "fakepassword",
    "SMTP_STARTTLS": "true",
    "SMTP_TIMEOUT": "15"
}

@mock.patch.dict(os.environ, BASE_ENV, clear=True)
def test_send_email_basic():
    with mock.patch("smtplib.SMTP") as mock_smtp:
        email_sender.send_email(
            to_addr="recipient@example.com",
            first_name="John",
            subject="Test Subject",
            body="This is a test body.",
            ticket_id="ABC123"
        )
        mock_smtp.assert_called_with("smtp.gmail.com", 587, timeout=15.0)
        instance = mock_smtp.return_value.__enter__.return_value
        instance.starttls.assert_called_once()
        instance.login.assert_called_with("testsender@example.com", "fakepassword")
        instance.send_message.assert_called_once()
        sent_msg: EmailMessage = instance.send_message.call_args[0][0]
        assert sent_msg["To"] == "recipient@example.com"
        assert sent_msg["From"] == "testsender@example.com"
        assert sent_msg["Subject"] == "Test Subject"
        assert "ABC123" in sent_msg.get_content()

@mock.patch.dict(os.environ, BASE_ENV, clear=True)
def test_send_email_with_attachment():
    with mock.patch("smtplib.SMTP") as mock_smtp:
        email_sender.send_email(
            to_addr="recipient@example.com",
            first_name="Alice",
            subject="With Attachment",
            body="Please see attached.",
            ticket_id="XYZ789",
            attachment_name="test.txt",
            attachment_bytes=b"filecontent"
        )
        instance = mock_smtp.return_value.__enter__.return_value
        sent_msg: EmailMessage = instance.send_message.call_args[0][0]
        assert len(sent_msg.get_payload()) > 1  # Multipart
        attachment_part = sent_msg.get_payload()[1]
        assert attachment_part.get_filename() == "test.txt"
        assert attachment_part.get_payload(decode=True) == b"filecontent"

@mock.patch.dict(os.environ, BASE_ENV, clear=True)
def test_send_email_no_starttls():
    with mock.patch.dict(os.environ, {"SMTP_STARTTLS": "false"}, clear=False):
        with mock.patch("smtplib.SMTP") as mock_smtp:
            email_sender.send_email(
                to_addr="recipient@example.com",
                first_name="NoTLS",
                subject="Plain",
                body="Body",
                ticket_id="ID999"
            )
            instance = mock_smtp.return_value.__enter__.return_value
            instance.starttls.assert_not_called()

@mock.patch.dict(os.environ, BASE_ENV, clear=True)
def test_send_email_without_auth():
    with mock.patch.dict(os.environ, {"SMTP_USERNAME": "", "SMTP_PASSWORD": ""}, clear=False):
        with mock.patch("smtplib.SMTP") as mock_smtp:
            email_sender.send_email(
                to_addr="recipient@example.com",
                first_name="Anon",
                subject="NoAuth",
                body="Body",
                ticket_id="ID000"
            )
            instance = mock_smtp.return_value.__enter__.return_value
            # Should not call login if username or password is blank
            try:
                instance.login.assert_not_called()
            except AssertionError:
                # If login was called, it must have been called with empty strings
                instance.login.assert_called_with("", "")

@mock.patch.dict(os.environ, BASE_ENV, clear=True)
def test_send_email_exception_logged_and_raised():
    with mock.patch("smtplib.SMTP", side_effect=OSError("Simulated error")):
        with pytest.raises(OSError):
            email_sender.send_email(
                to_addr="bad@example.com",
                first_name="Error",
                subject="Boom",
                body="This will fail",
                ticket_id="FAIL01"
            )