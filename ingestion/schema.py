"""
Normalized ticket schema for the ingestion layer.

All entry point sources (Email, Web forms, Chat, CRM, Slack/Teams) produce
tickets in this format for downstream classification, extraction, and routing.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TicketSource(str, Enum):
    EMAIL = "email"
    WEB_FORM = "web_form"
    CHAT = "chat"
    CRM_IMPORT = "crm_import"
    SLACK = "slack"
    TEAMS = "teams"


class CustomerMetadata(BaseModel):
    """Optional customer/account context from the source."""

    customer_id: str | None = None
    company: str | None = None
    email: str | None = None
    name: str | None = None
    account_id: str | None = None
    plan_tier: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class NormalizedTicket(BaseModel):
    """
    Single canonical ticket representation after ingestion.

    - ticket_id: Assigned by ingestion (e.g. UUID); stable for dedupe/linking.
    - source: Which channel the ticket came from.
    - raw_text: Original message body for auditing and reprocessing.
    - cleaned_text: Normalized text for classification/extraction (strip HTML, etc.).
    - subject: Title/summary when available (email subject, form title, thread title).
    - customer: Optional metadata from source or CRM.
    - received_at: When the ticket was received by our system.
    - source_id: External ID from the source system (e.g. email message-id, Slack ts).
    - attachments: References to any attachments (URLs or storage keys).
    - channel_metadata: Source-specific fields (thread_id, channel, etc.).
    """

    ticket_id: str
    source: TicketSource
    raw_text: str
    cleaned_text: str
    subject: str = ""
    customer: CustomerMetadata = Field(default_factory=CustomerMetadata)
    received_at: datetime = Field(default_factory=datetime.utcnow)
    source_id: str | None = None
    attachments: list[str] = Field(default_factory=list)
    channel_metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": False}
