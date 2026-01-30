"""
Email Sending Utility for Mindrian
===================================

Provides email sending capabilities using SMTP or SendGrid.
Configure via environment variables.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List
from datetime import datetime

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # Use app password for Gmail
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@mindrian.ai")


def send_email_smtp(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str = None,
    from_email: str = None,
    attachments: List[dict] = None
) -> bool:
    """
    Send email via SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML body content
        body_text: Plain text body (optional)
        from_email: Sender email (optional, uses default)
        attachments: List of {"filename": "...", "content": bytes} dicts

    Returns:
        True if sent successfully, False otherwise
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print("SMTP not configured (missing SMTP_USER or SMTP_PASSWORD)")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email or DEFAULT_FROM_EMAIL
        msg['To'] = to_email

        # Plain text part
        if body_text:
            part1 = MIMEText(body_text, 'plain')
            msg.attach(part1)

        # HTML part
        part2 = MIMEText(body_html, 'html')
        msg.attach(part2)

        # Attachments
        if attachments:
            for att in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(att['content'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={att["filename"]}'
                )
                msg.attach(part)

        # Send
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(
                from_email or DEFAULT_FROM_EMAIL,
                to_email,
                msg.as_string()
            )

        print(f"Email sent to {to_email}")
        return True

    except Exception as e:
        print(f"SMTP email error: {e}")
        return False


def send_email_sendgrid(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str = None,
    from_email: str = None
) -> bool:
    """
    Send email via SendGrid API.

    Requires sendgrid package: pip install sendgrid
    """
    if not SENDGRID_API_KEY:
        print("SendGrid not configured (missing SENDGRID_API_KEY)")
        return False

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Content

        message = Mail(
            from_email=from_email or DEFAULT_FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=body_html
        )

        if body_text:
            message.add_content(Content("text/plain", body_text))

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in [200, 201, 202]:
            print(f"Email sent to {to_email} via SendGrid")
            return True
        else:
            print(f"SendGrid returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"SendGrid email error: {e}")
        return False


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str = None,
    from_email: str = None,
    attachments: List[dict] = None
) -> bool:
    """
    Send email using available method (SendGrid preferred, SMTP fallback).

    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML body content
        body_text: Plain text body (optional)
        from_email: Sender email (optional)
        attachments: List of attachments (SMTP only)

    Returns:
        True if sent successfully
    """
    # Try SendGrid first
    if SENDGRID_API_KEY:
        return send_email_sendgrid(to_email, subject, body_html, body_text, from_email)

    # Fall back to SMTP
    if SMTP_USER and SMTP_PASSWORD:
        return send_email_smtp(to_email, subject, body_html, body_text, from_email, attachments)

    print("No email configuration found. Set SENDGRID_API_KEY or SMTP_USER/SMTP_PASSWORD")
    return False


def is_email_configured() -> bool:
    """Check if email sending is configured."""
    return bool(SENDGRID_API_KEY) or (bool(SMTP_USER) and bool(SMTP_PASSWORD))
