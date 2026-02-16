"""
Ticket classification module: category + severity from README taxonomy.

Consumes NormalizedTicket (from ingestion), outputs category (with confidence)
and severity (P1–P4 with reason). Supports confidence threshold → human review.
"""

from ticketClassification.schema import (
    Category,
    Severity,
    CategoryResult,
    SeverityResult,
    TicketClassificationResult,
)
from ticketClassification.service import ClassificationService

__all__ = [
    "Category",
    "Severity",
    "CategoryResult",
    "SeverityResult",
    "TicketClassificationResult",
    "ClassificationService",
]
