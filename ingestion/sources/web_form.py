"""
Web form entry point: parse form submissions (e.g. contact form, support form).

Supports JSON body or form-encoded POST with fields like: message, subject,
email, name, company, etc.
"""

from typing import Any

from ingestion.schema import TicketSource
from ingestion.sources.base import BaseSourceAdapter


class WebFormAdapter(BaseSourceAdapter):
    """Normalize web form submissions into ingestion kwargs."""

    def parse(self, payload: Any) -> dict[str, Any]:
        """
        Expect payload (dict) with:
        - message / description / body / content: main text
        - subject / title: optional
        - email, name, company: optional customer fields
        - account_id, customer_id: optional
        """
        if isinstance(payload, dict):
            return self._parse_dict(payload)
        raise ValueError("Web form payload must be a dict")

    def _parse_dict(self, d: dict[str, Any]) -> dict[str, Any]:
        raw_text = (
            d.get("message")
            or d.get("description")
            or d.get("body")
            or d.get("content")
            or d.get("details")
            or ""
        )
        subject = d.get("subject") or d.get("title") or ""
        source_id = d.get("submission_id") or d.get("id")

        return {
            "source": TicketSource.WEB_FORM,
            "raw_text": raw_text,
            "subject": subject,
            "source_id": source_id,
            "email": d.get("email"),
            "name": d.get("name"),
            "company": d.get("company"),
            "customer_id": d.get("customer_id"),
            "account_id": d.get("account_id"),
            "channel_metadata": {
                "form_name": d.get("form_name"),
                "form_id": d.get("form_id"),
                "referrer": d.get("referrer"),
            },
        }
