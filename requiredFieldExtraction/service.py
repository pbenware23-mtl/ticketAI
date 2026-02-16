"""
Extraction service: run field extraction on a NormalizedTicket.

Merges ticket customer metadata (name, company, account_id, plan_tier) into
extracted fields per README data enrichment. Returns ExtractionResult.
"""

from requiredFieldExtraction.schema import ExtractedFields, ExtractionResult
from requiredFieldExtraction.extractor import FieldExtractor


class ExtractionService:
    """
    Required field extraction (README §2).

    Consumes NormalizedTicket; runs LLM or rule-based extraction, then merges
    ticket.customer (customer name, company, account_id, plan_tier) into
    ExtractedFields so enrichment from CRM/source is preserved.
    """

    def __init__(self, extractor: FieldExtractor | None = None):
        self._extractor = extractor or FieldExtractor()

    def extract(self, ticket: "NormalizedTicket") -> ExtractionResult:  # type: ignore[name-defined]
        """
        Extract required fields from ticket text and merge customer metadata.

        ticket: from ingestion (ticket_id, cleaned_text, subject, customer).
        """
        text = ticket.cleaned_text or ""
        if ticket.subject:
            text = f"{ticket.subject}\n\n{text}".strip()

        fields = self._extractor.extract(text)

        # Merge customer metadata (README: data enrichment via CRM lookup, plan tier)
        customer = getattr(ticket, "customer", None)
        if customer is not None:
            if not fields.customer_name and getattr(customer, "name", None):
                fields.customer_name = customer.name
            if not fields.company and getattr(customer, "company", None):
                fields.company = customer.company
            if not fields.account_id and getattr(customer, "account_id", None):
                fields.account_id = customer.account_id
            # Plan tier is enrichment-only; could add to schema if we extend ExtractedFields
            # for now customer.plan_tier is available on ticket for routing

        # Attachments: merge any from ticket.attachments if not already in mentioned
        ticket_attachments = getattr(ticket, "attachments", None) or []
        if ticket_attachments:
            existing = set(fields.attachments_mentioned or [])
            for a in ticket_attachments:
                if a and a not in existing:
                    existing.add(a)
            fields.attachments_mentioned = list(existing)[:20]

        return ExtractionResult(ticket_id=ticket.ticket_id, fields=fields)


try:
    from ingestion.schema import NormalizedTicket
except ImportError:
    NormalizedTicket = None  # type: ignore[misc, assignment]
