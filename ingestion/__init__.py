"""
Ticket triage ingestion module.

Entry point sources: Email, Web forms, Chat/in-app, CRM imports, Slack/Teams.
All sources normalize to a single ticket schema for downstream classification and routing.
"""

from ingestion.schema import NormalizedTicket, TicketSource
from ingestion.core import IngestionService

__all__ = ["NormalizedTicket", "TicketSource", "IngestionService"]
