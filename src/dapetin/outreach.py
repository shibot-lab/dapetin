from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import smtplib
import ssl

from dapetin.domain.models import Opportunity, PipelineStatus


@dataclass(frozen=True, slots=True)
class OutreachMessage:
    recipient: str
    subject: str
    body: str


class OutreachProvider:
    def send(self, message: OutreachMessage) -> None:
        raise NotImplementedError


class SmtpOutreachProvider(OutreachProvider):
    """Send one targeted email through an explicitly configured SMTP server."""

    def __init__(self, host: str, port: int, username: str, password: str, sender: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender

    def send(self, message: OutreachMessage) -> None:
        email = EmailMessage()
        email["From"] = self.sender
        email["To"] = message.recipient
        email["Subject"] = message.subject
        email.set_content(message.body)
        context = ssl.create_default_context()
        with smtplib.SMTP(self.host, self.port, timeout=30) as server:
            server.starttls(context=context)
            server.login(self.username, self.password)
            server.send_message(email)


def build_message(opportunity: Opportunity, subject: str, body: str) -> OutreachMessage:
    recipient = opportunity.business.email
    if not recipient:
        raise ValueError("lead has no public email address")
    if opportunity.status in {PipelineStatus.ARCHIVED, PipelineStatus.CUSTOMER}:
        raise ValueError("lead is not eligible for outreach")
    return OutreachMessage(recipient=recipient, subject=subject, body=body)


def can_send(last_sent_at: datetime | None, cooldown_hours: int = 24) -> bool:
    if cooldown_hours < 0:
        raise ValueError("cooldown_hours must be non-negative")
    if last_sent_at is None:
        return True
    if last_sent_at.tzinfo is None:
        last_sent_at = last_sent_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= last_sent_at + timedelta(hours=cooldown_hours)


def send_targeted_outreach(
    opportunity: Opportunity,
    provider: OutreachProvider,
    subject: str,
    body: str,
    *,
    last_sent_at: datetime | None = None,
    cooldown_hours: int = 24,
) -> OutreachMessage:
    message = build_message(opportunity, subject, body)
    if not can_send(last_sent_at, cooldown_hours):
        raise RuntimeError("outreach cooldown is still active")
    provider.send(message)
    return message
