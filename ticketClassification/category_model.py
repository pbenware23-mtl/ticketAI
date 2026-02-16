"""
Category model: LLM or rule-based classifier using README taxonomy.

Returns CategoryResult (category + confidence). Low confidence → human review.
"""

import json
import re
from typing import Callable

from ticketClassification.schema import Category, CategoryResult


# Rule-based keyword mapping (category -> list of lowercase keywords/phrases)
CATEGORY_KEYWORDS: dict[Category, list[str]] = {
    Category.BILLING_PAYMENTS: [
        "bill", "invoice", "payment", "charge", "refund", "subscription",
        "pricing", "plan", "renewal", "credit card", "billing", "overcharge",
    ],
    Category.ACCOUNT_ACCESS: [
        "login", "log in", "password", "reset password", "locked out",
        "cannot access", "access denied", "2fa", "mfa", "authenticate",
        "account locked", "forgot password",
    ],
    Category.TECHNICAL_BUG: [
        "error", "crash", "broken", "not working", "bug", "defect",
        "failed", "failure", "exception", "stack trace", "500", "404",
        "doesn't work", "won't load", "freeze", "timeout",
    ],
    Category.FEATURE_REQUEST: [
        "would be nice", "feature request", "can you add", "suggest",
        "enhancement", "improvement", "wish", "could we have",
        "please add", "support for", "ability to",
    ],
    Category.INTEGRATION_ISSUE: [
        "api", "webhook", "integration", "connector", "sync", "third party",
        "oauth", "sso", "rest ", "endpoint", "connection failed",
    ],
    Category.SECURITY_ABUSE: [
        "security", "breach", "hack", "abuse", "compliance", "gdpr",
        "data leak", "unauthorized", "suspicious", "phishing",
    ],
    Category.GENERAL_INQUIRY: [
        "how do i", "how to", "documentation", "guide", "question",
        "what is", "where can i", "can you explain",
    ],
}


def _rule_based_classify(text: str) -> CategoryResult:
    """Classify using keyword matches; confidence from match strength."""
    if not text or not text.strip():
        return CategoryResult(category=Category.OTHER, confidence=0.0)

    lower = text.lower()
    words = set(re.findall(r"\w+", lower))
    scores: dict[Category, float] = {}

    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = 0.0
        for kw in keywords:
            if kw in lower:
                score += 1.0
            # single-word match
            if " " not in kw and kw in words:
                score += 0.5
        if score > 0:
            scores[cat] = score

    if not scores:
        return CategoryResult(category=Category.OTHER, confidence=0.3)

    best = max(scores, key=scores.get)
    raw_conf = min(0.5 + scores[best] * 0.15, 0.95)
    return CategoryResult(category=best, confidence=round(raw_conf, 2))


def _parse_category_json(raw: str) -> CategoryResult | None:
    """Parse LLM JSON response into CategoryResult."""
    raw = raw.strip()
    # Strip markdown code block if present
    if raw.startswith("```"):
        raw = re.sub(r"^```\w*\n?", "", raw)
        raw = re.sub(r"\n?```\s*$", "", raw)
    try:
        data = json.loads(raw)
        cat_str = (data.get("category") or "").strip().lower().replace(" ", "_")
        # Map common variants to enum
        if cat_str in ("billing", "payments"):
            cat_str = "billing_payments"
        elif cat_str in ("account_access", "account access"):
            cat_str = "account_access"
        elif cat_str in ("technical_bug", "technical bug", "bug"):
            cat_str = "technical_bug"
        elif cat_str in ("feature_request", "feature request"):
            cat_str = "feature_request"
        elif cat_str in ("integration_issue", "integration"):
            cat_str = "integration_issue"
        elif cat_str in ("security_abuse", "security", "abuse"):
            cat_str = "security_abuse"
        elif cat_str in ("general_inquiry", "general inquiry"):
            cat_str = "general_inquiry"
        category = Category(cat_str) if cat_str in [c.value for c in Category] else Category.OTHER
        confidence = float(data.get("confidence", 0.8))
        confidence = max(0.0, min(1.0, confidence))
        return CategoryResult(category=category, confidence=confidence)
    except (json.JSONDecodeError, ValueError, KeyError):
        return None


class CategoryModel:
    """
    Category classifier: optional LLM with rule-based fallback.

    If llm_fn is provided, it is called with the prompt and should return
    the model's text response. If None or LLM fails, rule-based is used.
    """

    def __init__(
        self,
        llm_fn: Callable[[str], str] | None = None,
        confidence_threshold: float = 0.8,
    ):
        self._llm = llm_fn
        self.confidence_threshold = confidence_threshold

    def classify(self, ticket_text: str) -> CategoryResult:
        """Classify ticket text; use LLM if available else rule-based."""
        text = (ticket_text or "").strip()
        if self._llm:
            from ticketClassification.prompts import CATEGORY_PROMPT

            prompt = CATEGORY_PROMPT.format(ticket_text=text[:4000])
            try:
                response = self._llm(prompt)
                result = _parse_category_json(response)
                if result is not None:
                    return result
            except Exception:
                pass
        return _rule_based_classify(text)
