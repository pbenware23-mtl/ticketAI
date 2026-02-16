"""
HTTP routes for each ingestion entry point.

- POST /ingest/web-form   → Web forms
- POST /ingest/email      → Email (webhook from SendGrid, Mailgun, etc.)
- POST /ingest/chat       → Chat / in-app support
- POST /ingest/crm        → CRM imports (Zendesk, Freshdesk, etc.)
- POST /ingest/slack      → Slack events
- POST /ingest/teams      → Microsoft Teams
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ingestion.schema import NormalizedTicket
from ingestion.sources.email import EmailAdapter
from ingestion.sources.web_form import WebFormAdapter
from ingestion.sources.chat import ChatAdapter
from ingestion.sources.crm import CRMImportAdapter
from ingestion.sources.slack_teams import SlackTeamsAdapter


def _ticket_response(ticket: NormalizedTicket) -> dict:
    """Serialize normalized ticket for API response."""
    return {
        "ticket_id": ticket.ticket_id,
        "source": ticket.source.value,
        "subject": ticket.subject,
        "cleaned_text": ticket.cleaned_text[:200] + "..." if len(ticket.cleaned_text) > 200 else ticket.cleaned_text,
        "received_at": ticket.received_at.isoformat(),
    }


def build_router(
    email_adapter: EmailAdapter,
    web_form_adapter: WebFormAdapter,
    chat_adapter: ChatAdapter,
    crm_adapter: CRMImportAdapter,
    slack_teams_adapter: SlackTeamsAdapter,
) -> APIRouter:
    router = APIRouter(prefix="/ingest", tags=["ingestion"])

    @router.post("/web-form", response_model=dict)
    async def ingest_web_form(request: Request):
        """Web form submission (JSON body with message, subject, email, etc.)."""
        body = await request.json()
        ticket = web_form_adapter.ingest(body)
        return {"ok": True, "ticket": _ticket_response(ticket)}

    @router.post("/email", response_model=dict)
    async def ingest_email(request: Request):
        """Email webhook (e.g. SendGrid, Mailgun, SES inbound)."""
        body = await request.json()
        try:
            ticket = email_adapter.ingest(body)
            return {"ok": True, "ticket": _ticket_response(ticket)}
        except ValueError as e:
            return JSONResponse(
                status_code=422,
                content={"ok": False, "error": str(e)},
            )

    @router.post("/chat", response_model=dict)
    async def ingest_chat(request: Request):
        """Chat / in-app support (Intercom, Zendesk Chat, etc.)."""
        body = await request.json()
        try:
            ticket = chat_adapter.ingest(body)
            return {"ok": True, "ticket": _ticket_response(ticket)}
        except ValueError as e:
            return JSONResponse(
                status_code=422,
                content={"ok": False, "error": str(e)},
            )

    @router.post("/crm", response_model=dict)
    async def ingest_crm(request: Request):
        """CRM import (Zendesk, Freshdesk, ServiceNow, etc.)."""
        body = await request.json()
        try:
            ticket = crm_adapter.ingest(body)
            return {"ok": True, "ticket": _ticket_response(ticket)}
        except ValueError as e:
            return JSONResponse(
                status_code=422,
                content={"ok": False, "error": str(e)},
            )

    @router.post("/slack", response_model=dict)
    async def ingest_slack(request: Request):
        """Slack event or message payload."""
        body = await request.json()
        try:
            # Force Slack source by ensuring platform or event shape
            if isinstance(body, dict) and "platform" not in body:
                body = {**body, "platform": "slack"}
            ticket = slack_teams_adapter.ingest(body)
            return {"ok": True, "ticket": _ticket_response(ticket)}
        except ValueError as e:
            return JSONResponse(
                status_code=422,
                content={"ok": False, "error": str(e)},
            )

    @router.post("/teams", response_model=dict)
    async def ingest_teams(request: Request):
        """Microsoft Teams activity or webhook payload."""
        body = await request.json()
        try:
            if isinstance(body, dict) and "platform" not in body:
                body = {**body, "platform": "teams"}
            ticket = slack_teams_adapter.ingest(body)
            return {"ok": True, "ticket": _ticket_response(ticket)}
        except ValueError as e:
            return JSONResponse(
                status_code=422,
                content={"ok": False, "error": str(e)},
            )

    return router
