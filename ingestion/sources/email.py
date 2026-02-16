"""
Email entry point: parse incoming email payloads (e.g. from webhook or IMAP poll).

Supports:
- Webhook payloads (SendGrid, Mailgun, AWS SES, etc.)
- Parsed IMAP message dict
- Minimal body/subject/from structure
"""

from typing import Any

from ingestion.schema import TicketSource
from ingestion.sources.base import BaseSourceAdapter


class EmailAdapter(BaseSourceAdapter):
    """Normalize email payloads into ingestion kwargs."""

    def parse(self, payload: Any) -> dict[str, Any]:
        """
        Expect payload like:
        - subject: str
        - body or text or html: str (prefer plain text for cleaned_text)
        - from / sender: str or {"email", "name"}
        - message_id: str (optional, for source_id)
        - attachments: list of {"filename", "url"} or URLs
        - received_at: ISO datetime string (optional)
        """
        if isinstance(payload, dict):
            return self._parse_dict(payload)
        raise ValueError("Email payload must be a dict")

    def _parse_dict(self, d: dict[str, Any]) -> dict[str, Any]:
        subject = d.get("subject") or d.get("Subject") or ""
        body = (
            d.get("body")
            or d.get("text")
            or d.get("plain_text")
            or d.get("html")
            or d.get("body_html")
            or ""
        )
        if isinstance(body, bytes):
            body = body.decode("utf-8", errors="replace")

        sender = d.get("from") or d.get("sender") or {}
        if isinstance(sender, str):
            email = sender
            name = None
        else:
            email = sender.get("email") or sender.get("address")
            name = sender.get("name")

        source_id = d.get("message_id") or d.get("Message-Id") or d.get("id")
        attachments = d.get("attachments") or []
        if attachments and isinstance(attachments[0], dict):
            attachments = [
                a.get("url") or a.get("content_id") or a.get("filename", "")
                for a in attachments
            ]

        received_at = None
        if d.get("received_at") or d.get("date"):
            try:
                from dateutil import parser as date_parser

                received_at = date_parser.parse(
                    d.get("received_at") or d.get("date")
                )
            except Exception:
                pass

        return {
            "source": TicketSource.EMAIL,
            "raw_text": body,
            "subject": subject,
            "source_id": source_id,
            "email": email,
            "name": name,
            "attachments": attachments,
            "channel_metadata": {
                "to": d.get("to"),
                "cc": d.get("cc"),
                "reply_to": d.get("reply_to"),
            },
            "received_at": received_at,
        }
