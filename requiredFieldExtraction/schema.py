"""
Extraction schema from README: common fields + LLM fields.

Common fields: Customer name, Company, Account ID, Product/module, Environment,
Error message, Timestamp, Steps to reproduce, Attachments mentioned.
LLM example: product, issue_type, error_message, environment, urgency.
"""

from pydantic import BaseModel, Field


class ExtractedFields(BaseModel):
    """
    Required fields extracted from a ticket (README §2).

    - customer_name, company, account_id: from text and/or merged from ticket customer metadata
    - product: Product / module (e.g. "API Gateway")
    - issue_type: Short label (e.g. "Authentication failure")
    - environment: prod / staging / development / unknown
    - error_message: Raw error or code (e.g. "401 invalid token")
    - urgency: High / Medium / Low (urgency indicators)
    - timestamp: Mentioned time/date in ticket if any
    - steps_to_reproduce: Description of how to reproduce
    - attachments_mentioned: Any attachment references in the body
    """

    customer_name: str | None = None
    company: str | None = None
    account_id: str | None = None
    product: str | None = None
    issue_type: str | None = None
    environment: str | None = None
    error_message: str | None = None
    urgency: str | None = None
    timestamp: str | None = None
    steps_to_reproduce: str | None = None
    attachments_mentioned: list[str] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """Extraction output: ticket_id + extracted fields."""

    ticket_id: str
    fields: ExtractedFields
