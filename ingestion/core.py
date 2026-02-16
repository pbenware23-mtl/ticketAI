"""
Core ingestion service: normalize, assign ticket ID, persist raw + cleaned text.

Consumes payloads from any source adapter and produces NormalizedTicket,
then enqueues or stores for the next pipeline stage (classification, etc.).
"""

import uuid
from datetime import datetime

from ingestion.schema import CustomerMetadata, NormalizedTicket, TicketSource


def assign_ticket_id() -> str:
    """Generate a unique ticket ID (e.g. for dedupe and linking)."""
    return f"TKT-{uuid.uuid4().hex[:12].upper()}"


def clean_text(raw: str) -> str:
    """
    Normalize raw content for downstream ML (strip HTML, collapse whitespace, etc.).
    Extend with HTML stripping, translation, or PII masking as needed.
    """
    if not raw:
        return ""
    text = raw.strip()
    # Placeholder: add HTML strip, markdown normalization, etc.
    while "  " in text:
        text = text.replace("  ", " ")
    return text


class IngestionService:
    """
    Central ingestion: build NormalizedTicket from source payload and hand off.

    Hand off can be: in-memory list (dev), queue (SQS/Kafka/Pub/Sub), or DB.
    """

    def __init__(self, on_ingested: callable = None):
        """
        Args:
            on_ingested: Optional callback(ticket: NormalizedTicket) for queue/DB.
                         If None, tickets are only returned (e.g. for sync API).
        """
        self._on_ingested = on_ingested

    def ingest(
        self,
        source: TicketSource,
        raw_text: str,
        *,
        subject: str = "",
        source_id: str | None = None,
        customer_id: str | None = None,
        company: str | None = None,
        email: str | None = None,
        name: str | None = None,
        account_id: str | None = None,
        plan_tier: str | None = None,
        attachments: list[str] | None = None,
        channel_metadata: dict | None = None,
        received_at: datetime | None = None,
        extra_customer: dict | None = None,
    ) -> NormalizedTicket:
        """Normalize a single ticket from any source and optionally hand off."""
        ticket_id = assign_ticket_id()
        cleaned = clean_text(raw_text)
        customer = CustomerMetadata(
            customer_id=customer_id,
            company=company,
            email=email,
            name=name,
            account_id=account_id,
            plan_tier=plan_tier,
            extra=extra_customer or {},
        )
        ticket = NormalizedTicket(
            ticket_id=ticket_id,
            source=source,
            raw_text=raw_text,
            cleaned_text=cleaned,
            subject=subject or "",
            customer=customer,
            received_at=received_at or datetime.utcnow(),
            source_id=source_id,
            attachments=attachments or [],
            channel_metadata=channel_metadata or {},
        )
        if self._on_ingested:
            self._on_ingested(ticket)
        return ticket
