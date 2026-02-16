"""
Classification service: run category + severity on a NormalizedTicket.

Uses confidence threshold from README: below threshold → needs_human_review.
"""

from ticketClassification.schema import (
    CategoryResult,
    SeverityResult,
    TicketClassificationResult,
)
from ticketClassification.category_model import CategoryModel
from ticketClassification.severity_model import SeverityModel


class ClassificationService:
    """
    Orchestrates category and severity models on ingested tickets.

    Consumes NormalizedTicket (ingestion schema); returns TicketClassificationResult
    with category, severity, and needs_human_review when confidence < threshold.
    """

    def __init__(
        self,
        category_model: CategoryModel | None = None,
        severity_model: SeverityModel | None = None,
        confidence_threshold: float = 0.8,
    ):
        self._category = category_model or CategoryModel(
            confidence_threshold=confidence_threshold
        )
        self._severity = severity_model or SeverityModel()
        self.confidence_threshold = confidence_threshold

    def classify(self, ticket: "NormalizedTicket") -> TicketClassificationResult:
        """
        Classify a normalized ticket: category then severity.

        ticket: from ingestion (has ticket_id, cleaned_text, subject, etc.).
        """
        # Use cleaned_text for classification; optionally prepend subject
        text = ticket.cleaned_text or ""
        if ticket.subject:
            text = f"{ticket.subject}\n\n{text}".strip()

        category_result: CategoryResult = self._category.classify(text)
        severity_result: SeverityResult = self._severity.classify(text)

        needs_review = category_result.confidence < self.confidence_threshold

        return TicketClassificationResult(
            ticket_id=ticket.ticket_id,
            category=category_result,
            severity=severity_result,
            needs_human_review=needs_review,
        )


# Type hint for NormalizedTicket (avoid circular import if ingestion not installed)
try:
    from ingestion.schema import NormalizedTicket
except ImportError:
    NormalizedTicket = None  # type: ignore[misc, assignment]
