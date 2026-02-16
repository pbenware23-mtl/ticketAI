"""
FastAPI application: wires ingestion service, source adapters, and routes.

Optional: pass on_ingested callback to push to queue (SQS, Kafka, etc.);
otherwise tickets are returned in the API response and can be stored in-memory for dev.
"""

from typing import Callable

from fastapi import FastAPI

from ingestion.core import IngestionService
from ingestion.schema import NormalizedTicket
from ingestion.sources.email import EmailAdapter
from ingestion.sources.web_form import WebFormAdapter
from ingestion.sources.chat import ChatAdapter
from ingestion.sources.crm import CRMImportAdapter
from ingestion.sources.slack_teams import SlackTeamsAdapter
from ingestion.api.routes import build_router


def create_app(
    on_ingested: Callable[[NormalizedTicket], None] | None = None,
) -> FastAPI:
    """
    Create the ingestion API app.

    Args:
        on_ingested: Optional callback for each ingested ticket (e.g. enqueue to SQS/Kafka).
    """
    ingestion = IngestionService(on_ingested=on_ingested)
    email = EmailAdapter(ingestion)
    web_form = WebFormAdapter(ingestion)
    chat = ChatAdapter(ingestion)
    crm = CRMImportAdapter(ingestion)
    slack_teams = SlackTeamsAdapter(ingestion)

    app = FastAPI(
        title="Ticket Triage Ingestion",
        description="Entry points: Email, Web forms, Chat, CRM imports, Slack/Teams",
        version="0.1.0",
    )
    app.include_router(
        build_router(email, web_form, chat, crm, slack_teams),
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


# Default app instance (in-memory; no queue)
app = create_app()
