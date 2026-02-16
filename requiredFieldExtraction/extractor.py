"""
Field extractor: LLM with rule-based fallback (README §2).

Parses ticket text for product, issue_type, error_message, environment, urgency,
timestamp, steps_to_reproduce, attachments_mentioned.
"""

import json
import re
from typing import Callable

from requiredFieldExtraction.schema import ExtractedFields


# Environment patterns (prod/staging/dev)
ENV_PATTERNS = [
    (r"\b(production|prod)\b", "Production"),
    (r"\b(staging|stage)\b", "Staging"),
    (r"\b(dev|development|local)\b", "Development"),
    (r"\b(test|qa)\s+(env|environment)\b", "Staging"),
]

# Urgency indicators
URGENCY_HIGH = [
    r"\b(urgent|critical|asap|immediately|emergency|blocking|down)\b",
    r"\b(cannot|can't|unable to)\s+(access|login|use)\b",
]
URGENCY_LOW = [
    r"\b(when you can|no rush|low priority|nice to have)\b",
]

# Error-like patterns (codes, exception words)
ERROR_PATTERNS = [
    r"\b(\d{3}\s+[\w\s]+(?:\s+error)?)\b",  # 401 Unauthorized, 500 error
    r"\b(Error:\s*[^\n.]+)",
    r"\b(Exception(?:\s+in)?[^\n.]+)",
    r"\b([A-Z][a-z]+(?:Error|Exception)\s*:?\s*[^\n.]*)",
    r"\b(failed\s+(?:with|to)\s+[^\n.]+)",
]

# Steps to reproduce
STEPS_PATTERNS = [
    r"steps?\s*(to\s+reproduce|:)\s*([^\n]+(?:\n(?!\s*\d+\.)[^\n]+)*)",
    r"reproduce[d]?\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\n|\Z)",
    r"how\s+to\s+reproduce\s*:?\s*([^\n]+(?:\n[^\n]+)*)",
]

# Attachments mentioned
ATTACHMENT_PATTERNS = [
    r"\b(attached|attachment|see\s+attached)\s*(?:file)?\s*:?\s*([^\n.,]+)",
    r"\b(attached\s+[^\n.]+)",
    r"\b(uploaded|enclosed)\s+[^\n.]*",
    r"(\w+\.(?:pdf|log|csv|png|txt|xlsx?))\b",
]


def _rule_based_extract(text: str) -> ExtractedFields:
    """Extract fields using regex and heuristics when LLM is not used."""
    if not text:
        return ExtractedFields()

    lower = text.strip().lower()
    fields = ExtractedFields()

    # Environment
    for pattern, env in ENV_PATTERNS:
        if re.search(pattern, text, re.I):
            fields.environment = env
            break

    # Urgency
    for pattern in URGENCY_HIGH:
        if re.search(pattern, text, re.I):
            fields.urgency = "High"
            break
    if not fields.urgency:
        for pattern in URGENCY_LOW:
            if re.search(pattern, text, re.I):
                fields.urgency = "Low"
                break
    if not fields.urgency:
        fields.urgency = "Medium"

    # Error message (first match)
    for pattern in ERROR_PATTERNS:
        m = re.search(pattern, text, re.I | re.M)
        if m:
            fields.error_message = m.group(1).strip()[:500]
            break

    # Timestamp (simple patterns)
    ts_m = re.search(
        r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|(?:at|since|on)\s+[\w\d:]+)\b",
        text,
        re.I,
    )
    if ts_m:
        fields.timestamp = ts_m.group(1).strip()

    # Steps to reproduce
    for pattern in STEPS_PATTERNS:
        m = re.search(pattern, text, re.I | re.S)
        if m:
            steps = (m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1)).strip()
            fields.steps_to_reproduce = steps[:1000]
            break

    # Attachments mentioned
    mentioned = []
    for pattern in ATTACHMENT_PATTERNS:
        for m in re.finditer(pattern, text, re.I):
            g = m.group(1).strip() if m.lastindex >= 1 else m.group(0).strip()
            if g and g not in mentioned:
                mentioned.append(g[:200])
    if mentioned:
        fields.attachments_mentioned = mentioned[:10]

    return fields


def _parse_extraction_json(raw: str) -> ExtractedFields | None:
    """Parse LLM JSON into ExtractedFields."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```\w*\n?", "", raw)
        raw = re.sub(r"\n?```\s*$", "", raw)
    try:
        data = json.loads(raw)
        return ExtractedFields(
            product=_str(data.get("product")),
            issue_type=_str(data.get("issue_type")),
            error_message=_str(data.get("error_message")),
            environment=_str(data.get("environment")),
            urgency=_str(data.get("urgency")),
            timestamp=_str(data.get("timestamp")),
            steps_to_reproduce=_str(data.get("steps_to_reproduce")),
            attachments_mentioned=_str_list(data.get("attachments_mentioned")),
        )
    except (json.JSONDecodeError, ValueError, KeyError):
        return None


def _str(v: object) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _str_list(v: object) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()][:20]
    return []


class FieldExtractor:
    """
    Extract required fields from ticket text; optional LLM with rule-based fallback.
    """

    def __init__(self, llm_fn: Callable[[str], str] | None = None):
        self._llm = llm_fn

    def extract(self, ticket_text: str) -> ExtractedFields:
        """Extract fields from ticket body; use LLM if available else rules."""
        text = (ticket_text or "").strip()
        if self._llm:
            from requiredFieldExtraction.prompts import EXTRACTION_PROMPT

            prompt = EXTRACTION_PROMPT.format(ticket_text=text[:6000])
            try:
                response = self._llm(prompt)
                result = _parse_extraction_json(response)
                if result is not None:
                    return result
            except Exception:
                pass
        return _rule_based_extract(text)
