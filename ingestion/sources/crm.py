"""
CRM import entry point: parse tickets imported from Zendesk, Freshdesk,
ServiceNow, Salesforce, HubSpot, etc.

Supports bulk or single-ticket import payloads with CRM-specific field mapping.
"""

from typing import Any

from ingestion.schema import TicketSource
from ingestion.sources.base import BaseSourceAdapter


class CRMImportAdapter(BaseSourceAdapter):
    """Normalize CRM ticket records into ingestion kwargs."""

    def parse(self, payload: Any) -> dict[str, Any]:
        """
        Expect payload (dict) with common CRM-style fields:
        - description / body / subject + description: content
        - subject / title: subject
        - id / ticket_id: source_id
        - requester / contact: { email, name } or requester_id
        - account_id, company, custom_fields: optional
        - created_at / created: received_at
        - crm_source: "zendesk" | "freshdesk" | "servicenow" | "salesforce" | "hubspot"
        """
        if isinstance(payload, dict):
            return self._parse_dict(payload)
        raise ValueError("CRM import payload must be a dict")

    def _parse_dict(self, d: dict[str, Any]) -> dict[str, Any]:
        raw_text = (
            d.get("description")
            or d.get("body")
            or (f"{d.get('subject', '')}\n\n{d.get('description', '')}".strip())
            or d.get("content")
            or ""
        )
        subject = d.get("subject") or d.get("title") or ""
        source_id = str(d.get("id") or d.get("ticket_id") or "")

        requester = d.get("requester") or d.get("contact") or d.get("user") or {}
        if isinstance(requester, dict):
            email = requester.get("email") or d.get("requester_email")
            name = requester.get("name") or d.get("requester_name")
        else:
            email = d.get("requester_email")
            name = d.get("requester_name")

        received_at = None
        for key in ("created_at", "created", "created_date", "date"):
            if d.get(key):
                try:
                    from dateutil import parser as date_parser
                    received_at = date_parser.parse(d[key])
                    break
                except Exception:
                    pass

        return {
            "source": TicketSource.CRM_IMPORT,
            "raw_text": raw_text,
            "subject": subject,
            "source_id": source_id or None,
            "email": email,
            "name": name,
            "company": d.get("company") or (requester.get("company") if isinstance(requester, dict) else None),
            "customer_id": str(d.get("requester_id") or requester.get("id") or "") or None,
            "account_id": d.get("account_id") or d.get("organization_id"),
            "plan_tier": d.get("plan_tier") or d.get("plan"),
            "received_at": received_at,
            "channel_metadata": {
                "crm_source": d.get("crm_source") or d.get("source"),
                "priority": d.get("priority"),
                "status": d.get("status"),
                "custom_fields": d.get("custom_fields") or {},
            },
        }
