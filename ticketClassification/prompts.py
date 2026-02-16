"""
Prompt templates for LLM-based category and severity (from README).
"""

CATEGORY_PROMPT = """Classify the support ticket into exactly one category.

Categories:
- billing_payments: Billing, payments, invoices, refunds, subscription, pricing
- account_access: Login, password, 2FA, account locked, access denied
- technical_bug: Errors, crashes, broken feature, defect, not working
- feature_request: New feature, enhancement, improvement idea
- integration_issue: API, webhook, third-party, connector, sync issues
- security_abuse: Security concern, abuse, compliance, data breach
- general_inquiry: How-to, question, documentation, general support
- other: Anything that does not fit above

Ticket:
{ticket_text}

Return valid JSON only, no markdown:
{{ "category": "<one of the category values above>", "confidence": <number between 0 and 1> }}"""


SEVERITY_PROMPT = """Assign a severity level to this support ticket.

Severity scale:
- P1: Outage / critical — production down, system unavailable, critical security — Immediate
- P2: Major degradation — major feature broken, significant impact — <4h
- P3: Standard issue — normal bug or request — <24h
- P4: Low / request — minor, enhancement, backlog — Backlog

Consider: system outage, payment failure, security breach, VIP/revenue impact, SLA risk.

Ticket:
{ticket_text}

Return valid JSON only, no markdown:
{{ "severity": "P1" or "P2" or "P3" or "P4", "reason": "<short reason>" }}"""
