"""
Classification schema: category taxonomy and severity scale from README.

Category taxonomy: Billing/Payments, Account Access, Technical Bug, Feature Request,
Integration Issue, Security/Abuse, General Inquiry (+ Other fallback).
Severity: P1 (outage/critical) … P4 (low/backlog).
"""

from enum import Enum

from pydantic import BaseModel, Field


class Category(str, Enum):
    """Category taxonomy from README."""

    BILLING_PAYMENTS = "billing_payments"
    ACCOUNT_ACCESS = "account_access"
    TECHNICAL_BUG = "technical_bug"
    FEATURE_REQUEST = "feature_request"
    INTEGRATION_ISSUE = "integration_issue"
    SECURITY_ABUSE = "security_abuse"
    GENERAL_INQUIRY = "general_inquiry"
    OTHER = "other"


class Severity(str, Enum):
    """Priority scale from README. P1 = immediate, P4 = backlog."""

    P1 = "P1"  # Outage / critical — Immediate
    P2 = "P2"  # Major degradation — <4h
    P3 = "P3"  # Standard issue — <24h
    P4 = "P4"  # Low / request — Backlog


# Human-readable meanings for severity (SLA)
SEVERITY_MEANING: dict[Severity, str] = {
    Severity.P1: "Outage / critical — Immediate",
    Severity.P2: "Major degradation — <4h",
    Severity.P3: "Standard issue — <24h",
    Severity.P4: "Low / request — Backlog",
}


class CategoryResult(BaseModel):
    """Category model output: category + confidence (0–1)."""

    category: Category
    confidence: float = Field(ge=0.0, le=1.0)


class SeverityResult(BaseModel):
    """Severity detection output: P1–P4 + reason."""

    severity: Severity
    reason: str = ""


class TicketClassificationResult(BaseModel):
    """
    Full classification for a ticket: category, severity, and human-review flag.

    needs_human_review: True when category confidence is below threshold
    (per README: fallback to human review).
    """

    ticket_id: str
    category: CategoryResult
    severity: SeverityResult
    needs_human_review: bool = False
