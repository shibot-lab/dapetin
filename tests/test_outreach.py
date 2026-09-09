from datetime import datetime, timedelta, timezone

import pytest

from dapetin.domain.models import Business, Opportunity, OpportunityScore, PipelineStatus
from dapetin.outreach import OutreachMessage, OutreachProvider, build_message, can_send, send_targeted_outreach


class FakeProvider(OutreachProvider):
    def __init__(self):
        self.sent = []

    def send(self, message: OutreachMessage) -> None:
        self.sent.append(message)


def make_opportunity(email="hello@example.com", status=PipelineStatus.QUALIFIED):
    return Opportunity(
        business=Business(name="Prima Karya", email=email, source_id="prima-karya"),
        score=OpportunityScore(80, ["Has public website"]),
        status=status,
    )


def test_build_message_requires_email():
    with pytest.raises(ValueError):
        build_message(make_opportunity(email=None), "Hello", "Hi")


def test_archived_and_customer_leads_are_not_eligible():
    for status in (PipelineStatus.ARCHIVED, PipelineStatus.CUSTOMER):
        with pytest.raises(ValueError):
            build_message(make_opportunity(status=status), "Hello", "Hi")


def test_cooldown_blocks_repeat_outreach():
    recent = datetime.now(timezone.utc) - timedelta(hours=1)
    assert can_send(recent, cooldown_hours=24) is False
    assert can_send(recent, cooldown_hours=0) is True


def test_targeted_outreach_sends_one_message():
    provider = FakeProvider()
    message = send_targeted_outreach(
        make_opportunity(), provider, "Partnership", "Hello Prima Karya"
    )
    assert provider.sent == [message]
    assert message.recipient == "hello@example.com"
