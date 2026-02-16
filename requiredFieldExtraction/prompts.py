"""
LLM extraction prompt from README §2.

Extract: Product, Issue type, Error message, Environment, Urgency indicators.
Return JSON only.
"""

EXTRACTION_PROMPT = """Extract the following fields from the support ticket.

Fields:
- product: Product or module name (e.g. API Gateway, Dashboard, Mobile app)
- issue_type: Brief issue type (e.g. Authentication failure, Timeout, Bug)
- error_message: Exact error message or code if mentioned (e.g. 401 invalid token)
- environment: One of Production, Staging, Development, or empty if unknown
- urgency: One of High, Medium, Low based on wording in the ticket
- timestamp: Any date/time mentioned in the ticket (e.g. "since 2pm", "2024-01-15")
- steps_to_reproduce: Summary of steps to reproduce the issue, if described
- attachments_mentioned: List of any files or attachments the customer says they attached or will attach

Ticket:
{ticket_text}

Return valid JSON only, no markdown. Use null for missing fields. For attachments_mentioned use a list of strings.
Example:
{{ "product": "API Gateway", "issue_type": "Authentication failure", "error_message": "401 invalid token", "environment": "Production", "urgency": "High", "timestamp": null, "steps_to_reproduce": null, "attachments_mentioned": [] }}"""
