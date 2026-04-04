"""
email_service.py — Real email delivery via SendGrid.

Sends personalised rejection emails directly to candidates.
Tracks delivery status in the database.
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL     = os.getenv("SENDER_EMAIL", "noreply@whynothireme.com")
SENDER_NAME      = os.getenv("SENDER_NAME",  "WhyNotHireMe")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class EmailPayload:
    to_email:     str
    to_name:      str
    subject:      str
    body_text:    str       # plain text version
    body_html:    str       # HTML version
    from_email:   str = ""  # override sender if needed
    from_name:    str = ""


# ---------------------------------------------------------------------------
# SendGrid sender
# ---------------------------------------------------------------------------

def send_email(payload: EmailPayload) -> dict:
    """
    Send an email via SendGrid.

    Returns:
        {
            "success": True/False,
            "status_code": 202,
            "message": "Email sent successfully"
        }

    Raises:
        ImportError if sendgrid package not installed.
        Exception if API key missing or SendGrid returns error.
    """
    if not SENDGRID_API_KEY:
        raise ValueError(
            "SENDGRID_API_KEY not set in .env file. "
            "Get your key from sendgrid.com"
        )

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import (
            Mail, Email, To, Content, MimeType
        )
    except ImportError:
        raise ImportError(
            "SendGrid not installed. Run: pip install sendgrid"
        )

    sender_email = payload.from_email or SENDER_EMAIL
    sender_name  = payload.from_name  or SENDER_NAME

    message = Mail()
    message.from_email  = Email(sender_email, sender_name)
    message.to          = [To(payload.to_email, payload.to_name)]
    message.subject     = payload.subject

    # Plain text version
    message.add_content(Content(MimeType.text, payload.body_text))

    # HTML version (richer experience)
    message.add_content(Content(MimeType.html, payload.body_html))

    try:
        client   = SendGridAPIClient(SENDGRID_API_KEY)
        response = client.send(message)

        if response.status_code in (200, 202):
            logger.info(
                "Email sent to %s — status %d",
                payload.to_email, response.status_code
            )
            return {
                "success":     True,
                "status_code": response.status_code,
                "message":     "Email sent successfully.",
            }
        else:
            logger.error(
                "SendGrid returned %d for %s",
                response.status_code, payload.to_email
            )
            return {
                "success":     False,
                "status_code": response.status_code,
                "message":     f"SendGrid returned status {response.status_code}.",
            }

    except Exception as exc:
        logger.exception("SendGrid send failed")
        return {
            "success": False,
            "status_code": 500,
            "message": str(exc),
        }


# ---------------------------------------------------------------------------
# Convenience wrapper — build payload from email_generator output
# ---------------------------------------------------------------------------

def send_rejection_email(
    candidate_email: str,
    candidate_name:  str,
    email_data:      dict,              # output from email_generator.generate_rejection_email
    company_email:   Optional[str] = None,
    company_name:    Optional[str] = None,
) -> dict:
    """
    High-level function — takes email_generator output and sends it.

    Args:
        candidate_email: Recipient email address
        candidate_name:  Recipient name
        email_data:      Dict returned by generate_rejection_email()
        company_email:   Optional sender override (company's own email)
        company_name:    Optional sender name override

    Returns:
        Result dict with success, status_code, message
    """
    payload = EmailPayload(
        to_email   = candidate_email,
        to_name    = candidate_name,
        subject    = email_data.get("subject", "Your Application Update"),
        body_text  = email_data.get("body", ""),
        body_html  = email_data.get("html_body", email_data.get("body", "")),
        from_email = company_email or SENDER_EMAIL,
        from_name  = company_name  or SENDER_NAME,
    )
    return send_email(payload)