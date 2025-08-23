import os
import smtplib
import logging
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST","mailhog")
SMTP_PORT = int(os.getenv("SMTP_PORT","1025"))
FROM_ADDR = os.getenv("FROM_ADDR","no-reply@example.com")


SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "false").lower() in {"1", "true", "yes", "on"}
SMTP_TIMEOUT = float(os.getenv("SMTP_TIMEOUT", "10"))


def send_email(
    to_addr: str,
    subject: str,
    body: str,
    attachment_name: str | None = None,
    attachment_bytes: bytes | None = None,
) -> None:
    """Send an email (optionally with a single attachment) via SMTP.

    Uses MailHog by default but supports STARTTLS and AUTH if configured via env vars.

    Env vars:
      - SMTP_HOST (default: "mailhog")
      - SMTP_PORT (default: 1025)
      - FROM_ADDR (default: "no-reply@example.com")
      - SMTP_USERNAME (optional)
      - SMTP_PASSWORD (optional)
      - SMTP_STARTTLS (true/false; default: false)
      - SMTP_TIMEOUT (seconds; default: 10)
    """
    msg = EmailMessage()
    msg["From"] = FROM_ADDR
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment_name and attachment_bytes is not None:
        msg.add_attachment(
            attachment_bytes,
            maintype="application",
            subtype="octet-stream",
            filename=attachment_name,
        )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT) as s:
            if SMTP_STARTTLS:
                try:
                    s.starttls()
                except smtplib.SMTPException as e:
                    logging.warning("STARTTLS failed: %s", e)
            if SMTP_USERNAME and SMTP_PASSWORD:
                s.login(SMTP_USERNAME, SMTP_PASSWORD)
            s.send_message(msg)
    except Exception:
        logging.exception("Failed to send email to %s", to_addr)
        raise
