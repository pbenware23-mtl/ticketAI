"""
Deduplication methods from README §3.

1. Semantic similarity: embeddings + cosine similarity threshold (e.g. >0.92)
2. Metadata matching: same account, same error string, same timeframe
3. Incident correlation: link to active outage
"""

import math
import re
from datetime import datetime, timedelta
from typing import Callable

from deduplication.schema import (
    DuplicateMatch,
    DuplicateMatchType,
    ProcessedTicketView,
)


def _normalize_error_message(msg: str | None) -> str:
    """Normalize error string for comparison (strip, lower, collapse whitespace)."""
    if not msg:
        return ""
    return " ".join(re.split(r"\s+", msg.strip().lower()))


def _same_timeframe(
    received_at: datetime | None,
    candidate_at: datetime | None,
    window_hours: float = 1.0,
) -> bool:
    """True if both timestamps are within window_hours (or same day if window large)."""
    if received_at is None or candidate_at is None:
        return False
    delta = abs((received_at - candidate_at).total_seconds())
    return delta <= window_hours * 3600


def metadata_match(
    current_account_id: str | None,
    current_error: str | None,
    current_received_at: datetime | None,
    candidate: ProcessedTicketView,
    *,
    same_account_required: bool = True,
    same_error_required: bool = True,
    time_window_hours: float = 1.0,
) -> DuplicateMatch | None:
    """
    README: Metadata matching — same account, same error string, same timeframe.

    Returns a DuplicateMatch (EXACT) if all required criteria match; else None.
    """
    if same_account_required:
        if not current_account_id or not candidate.account_id:
            return None
        if current_account_id.strip() != candidate.account_id.strip():
            return None
    if same_error_required:
        n1 = _normalize_error_message(current_error)
        n2 = _normalize_error_message(candidate.error_message)
        if not n1 or not n2:
            return None
        if n1 != n2:
            return None
    if not _same_timeframe(
        current_received_at, candidate.received_at, time_window_hours
    ):
        return None

    reason = "Same account, same error string, same timeframe"
    if not same_error_required:
        reason = "Same account, same timeframe"
    return DuplicateMatch(
        candidate_ticket_id=candidate.ticket_id,
        match_type=DuplicateMatchType.EXACT,
        similarity_score=1.0,
        reason=reason,
    )


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors. Returns value in [-1, 1]."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def semantic_match(
    current_embedding: list[float] | None,
    current_text: str,
    candidate: ProcessedTicketView,
    embedding_fn: Callable[[str], list[float]] | None,
    *,
    exact_threshold: float = 0.92,
    likely_threshold: float = 0.85,
) -> DuplicateMatch | None:
    """
    README: Semantic similarity — embeddings + cosine similarity threshold (e.g. >0.92).

    exact_threshold: >= this → EXACT (auto-merge).
    likely_threshold: >= this and < exact_threshold → LIKELY (agent review).
    """
    cand_emb = candidate.embedding
    if cand_emb is None and embedding_fn and candidate.cleaned_text:
        cand_emb = embedding_fn(candidate.cleaned_text)
    if current_embedding is None and embedding_fn and current_text:
        current_embedding = embedding_fn(current_text)

    if not current_embedding or not cand_emb:
        return None
    if len(current_embedding) != len(cand_emb):
        return None

    score = cosine_similarity(current_embedding, cand_emb)
    if score >= exact_threshold:
        return DuplicateMatch(
            candidate_ticket_id=candidate.ticket_id,
            match_type=DuplicateMatchType.EXACT,
            similarity_score=round(score, 4),
            reason=f"Semantic similarity {score:.2f} >= {exact_threshold}",
        )
    if score >= likely_threshold:
        return DuplicateMatch(
            candidate_ticket_id=candidate.ticket_id,
            match_type=DuplicateMatchType.LIKELY,
            similarity_score=round(score, 4),
            reason=f"Semantic similarity {score:.2f} in [{likely_threshold}, {exact_threshold})",
        )
    return None


def incident_match(
    ticket_id: str,
    account_id: str | None,
    product: str | None,
    get_active_incident_ids: Callable[[], list[str]] | None,
    link_to_incident: Callable[[str, str | None, str | None], str | None] | None,
) -> tuple[DuplicateMatch | None, str | None]:
    """
    README: Incident correlation — link to active outage.

    Returns (DuplicateMatch with KNOWN_INCIDENT, incident_id) if ticket links to an active incident.
    Use either get_active_incident_ids (return list of active IDs) or link_to_incident(ticket_id, account_id, product) -> incident_id | None.
    """
    incident_id: str | None = None
    if link_to_incident is not None:
        incident_id = link_to_incident(ticket_id, account_id, product)
    elif get_active_incident_ids is not None:
        active = get_active_incident_ids()
        if active:
            incident_id = active[0]  # Link to first active; could be smarter

    if not incident_id:
        return None, None

    return (
        DuplicateMatch(
            candidate_ticket_id=incident_id,
            match_type=DuplicateMatchType.KNOWN_INCIDENT,
            reason="Linked to active incident",
        ),
        incident_id,
    )