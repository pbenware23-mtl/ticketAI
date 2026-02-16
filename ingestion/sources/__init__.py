"""
Source adapters: convert external payloads into the shape expected by IngestionService.

Each module corresponds to an entry point: Email, Web forms, Chat, CRM, Slack/Teams.
"""

from ingestion.sources.base import BaseSourceAdapter
from ingestion.sources.email import EmailAdapter
from ingestion.sources.web_form import WebFormAdapter
from ingestion.sources.chat import ChatAdapter
from ingestion.sources.crm import CRMImportAdapter
from ingestion.sources.slack_teams import SlackTeamsAdapter

__all__ = [
    "BaseSourceAdapter",
    "EmailAdapter",
    "WebFormAdapter",
    "ChatAdapter",
    "CRMImportAdapter",
    "SlackTeamsAdapter",
]
