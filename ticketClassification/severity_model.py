"""
Severity detection: rule-based signals + optional LLM (README).

Signals: system outage, payment failure, security breach, VIP, revenue impact, SLA risk.
Output: P1–P4 with reason.
"""

import json
import re
from typing import Callable

from ticketClassification.schema import Severity, SeverityResult


# P1 signals (outage / critical)
P1_PATTERNS = [
    r"\b(outage|down|production down|system down|service down)\b",
    r"\b(cannot access production|prod (is )?down)\b",
    r"\b(critical|emergency|urgent)\s+(security|breach)\b",
    r"\b(everyone|all users)\s+(affected|cannot)\b",
]

# P2 signals (major degradation)
P2_PATTERNS = [
    r"\b(major\s+)?(degradation|outage)\b",
    r"\b(payment\s+)?(failure|failed|broken)\s+(for\s+)?(all|everyone)\b",
    r"\b(revenue\s+impact|revenue\s+at\s+risk)\b",
    r"\b(core\s+feature\s+broken|critical\s+feature)\b",
    r"\b(sla\s+breach|sla\s+at\s+risk)\b",
]

# P3 signals (standard)
P3_PATTERNS = [
    r"\b(error|bug|issue|not working)\b",
    r"\b(help|support)\s+(with|needed)\b",
]

# P4: low / request (feature request, how-to, minor)
P4_PATTERNS = [
    r"\b(feature\s+request|enhancement|improvement)\b",
    r"\b(how\s+to|how\s+do\s+i)\b",
    r"\b(would\s+be\s+nice|suggestion)\b",
]


def _rule_based_severity(text: str) -> SeverityResult:
    """Assign severity from keyword/signal rules; default P3."""
    if not text or not text.strip():
        return SeverityResult(severity=Severity.P4, reason="Empty ticket")

    lower = text.lower()

    for pattern in P1_PATTERNS:
        if re.search(pattern, lower, re.I):
            return SeverityResult(
                severity=Severity.P1,
                reason="Detected critical/outage or system-down language",
            )

    for pattern in P2_PATTERNS:
        if re.search(pattern, lower, re.I):
            return SeverityResult(
                severity=Severity.P2,
                reason="Detected major degradation or high-impact signal",
            )

    for pattern in P4_PATTERNS:
        if re.search(pattern, lower, re.I):
            return SeverityResult(
                severity=Severity.P4,
                reason="Detected low-priority or request-type language",
            )

    return SeverityResult(
        severity=Severity.P3,
        reason="Standard issue; no P1/P2/P4 signals detected",
    )


def _parse_severity_json(raw: str) -> SeverityResult | None:
    """Parse LLM JSON into SeverityResult."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```\w*\n?", "", raw)
        raw = re.sub(r"\n?```\s*$", "", raw)
    try:
        data = json.loads(raw)
        sev = (data.get("severity") or "P3").strip().upper()
        if sev not in ("P1", "P2", "P3", "P4"):
            sev = "P3"
        reason = (data.get("reason") or "").strip() or "LLM-assigned"
        return SeverityResult(severity=Severity(sev), reason=reason)
    except (json.JSONDecodeError, ValueError, KeyError):
        return None


class SeverityModel:
    """
    Severity detector: optional LLM with rule-based fallback.

    Rule-based uses README signals (outage, payment failure, security, etc.)
    to assign P1–P4. LLM can override with a reason.
    """

    def __init__(self, llm_fn: Callable[[str], str] | None = None):
        self._llm = llm_fn

    def classify(self, ticket_text: str) -> SeverityResult:
        """Assign severity (P1–P4) and reason."""
        text = (ticket_text or "").strip()
        if self._llm:
            from ticketClassification.prompts import SEVERITY_PROMPT

            prompt = SEVERITY_PROMPT.format(ticket_text=text[:4000])
            try:
                response = self._llm(prompt)
                result = _parse_severity_json(response)
                if result is not None:
                    return result
            except Exception:
                pass
        return _rule_based_severity(text)
