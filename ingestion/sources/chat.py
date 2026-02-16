"""
Chat / in-app support entry point: parse messages from Intercom, Zendesk Chat,
Drift, custom in-app widget, etc.

Supports conversation-style payloads with message body, user info, and thread context.
"""

from typing import Any

from ingestion.schema import TicketSource
from ingestion.sources.base import BaseSourceAdapter


class ChatAdapter(BaseSourceAdapter):
    """Normalize chat or in-app support messages into ingestion kwargs."""

    def parse(self, payload: Any) -> dict[str, Any]:
        """
        Expect payload (dict) with:
        - message / body / text: main content
        - user: { id, email, name } or flat user_id, email, name
        - conversation_id / thread_id: for grouping
        - message_id / id: source_id
        - channel: e.g. "intercom", "zendesk_chat"
        """
        if isinstance(payload, dict):
            return self._parse_dict(payload)
        raise ValueError("Chat payload must be a dict")

    def _parse_dict(self, d: dict[str, Any]) -> dict[str, Any]:
        raw_text = (
            d.get("message")
            or d.get("body")
            or d.get("text")
            or d.get("content")
            or ""
        )
        source_id = d.get("message_id") or d.get("id")
        user = d.get("user") or {}
        if isinstance(user, dict):
            email = user.get("email") or d.get("email")
            name = user.get("name") or d.get("user_name")
            customer_id = user.get("id") or d.get("user_id")
        else:
            email = d.get("email")
            name = d.get("user_name")
            customer_id = d.get("user_id")

        return {
            "source": TicketSource.CHAT,
            "raw_text": raw_text,
            "subject": "",  # Chat often has no subject; use first line or leave empty
            "source_id": source_id,
            "email": email,
            "name": name,
            "customer_id": str(customer_id) if customer_id else None,
            "company": d.get("company") or (user.get("company") if isinstance(user, dict) else None),
            "channel_metadata": {
                "conversation_id": d.get("conversation_id") or d.get("thread_id"),
                "channel": d.get("channel"),
                "platform": d.get("platform"),
            },
        }
