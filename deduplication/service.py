"""
Deduplication service: run metadata, semantic, and incident checks (README §3).

Decides action: Auto-merge (exact), Agent review (likely), Link + notify (known incident).
"""

from datetime import datetime
from typing import Any, Callable

from deduplication.schema import (
    DeduplicationAction,
    DeduplicationResult,
    DuplicateMatch,
    DuplicateMatchType,
    ProcessedTicketView,
)
from deduplication.matchers import (
    metadata_match,
    semantic_match,
    incident_match,
)


class DeduplicationService:
    """
    Before response/routing, detect duplicates (README §3).

    - Metadata matching: same account, same error string, same timeframe
    - Semantic similarity: embeddings + cosine threshold (e.g. >0.92) → exact/likely
    - Incident correlation: link to active outage → link_notify
    """

    def __init__(
        self,
        *,
        embedding_fn: Callable[[str], list[float]] | None = None,
        semantic_exact_threshold: float = 0.92,
        semantic_likely_threshold: float = 0.85,
        metadata_time_window_hours: float = 1.0,
        get_active_incident_ids: Callable[[], list[str]] | None = None,
        link_to_incident: Callable[
            [str, str | None, str | None], str | None
        ] | None = None,
    ):
        self._embedding_fn = embedding_fn
        self._semantic_exact = semantic_exact_threshold
        self._semantic_likely = semantic_likely_threshold
        self._metadata_window = metadata_time_window_hours
        self._get_active_incidents = get_active_incident_ids
        self._link_to_incident = link_to_incident

    def check(
        self,
        ticket_id: str,
        account_id: str | None,
        error_message: str | None,
        received_at: datetime | None,
        cleaned_text: str,
        current_embedding: list[float] | None,
        candidates: list[ProcessedTicketView],
        *,
        product: str | None = None,
    ) -> DeduplicationResult:
        """
        Run deduplication: metadata → semantic → incident. Return action and matches.

        candidates: Previously processed tickets to compare against (e.g. from same account or vector store).
        """
        matches: list[DuplicateMatch] = []
        linked_incident_id: str | None = None

        # 1. Metadata matching
        for cand in candidates:
            if cand.ticket_id == ticket_id:
                continue
            m = metadata_match(
                account_id,
                error_message,
                received_at,
                cand,
                time_window_hours=self._metadata_window,
            )
            if m and not _already_matched(m.candidate_ticket_id, matches):
                matches.append(m)

        # 2. Semantic similarity (if we have embedding or embedding_fn)
        if candidates and (current_embedding or self._embedding_fn):
            for cand in candidates:
                if cand.ticket_id == ticket_id:
                    continue
                m = semantic_match(
                    current_embedding,
                    cleaned_text,
                    cand,
                    self._embedding_fn,
                    exact_threshold=self._semantic_exact,
                    likely_threshold=self._semantic_likely,
                )
                if m and not _already_matched(m.candidate_ticket_id, matches):
                    matches.append(m)

        # 3. Incident correlation
        inc_match, inc_id = incident_match(
            ticket_id,
            account_id,
            product,
            self._get_active_incidents,
            self._link_to_incident,
        )
        if inc_match:
            matches.append(inc_match)
            linked_incident_id = inc_id

        # Decide action (README: exact → auto_merge, likely → agent_review, known_incident → link_notify)
        action = DeduplicationAction.NONE
        if any(m.match_type == DuplicateMatchType.KNOWN_INCIDENT for m in matches):
            action = DeduplicationAction.LINK_NOTIFY
        elif any(m.match_type == DuplicateMatchType.EXACT for m in matches):
            action = DeduplicationAction.AUTO_MERGE
        elif any(m.match_type == DuplicateMatchType.LIKELY for m in matches):
            action = DeduplicationAction.AGENT_REVIEW

        return DeduplicationResult(
            ticket_id=ticket_id,
            action=action,
            matches=matches,
            linked_incident_id=linked_incident_id,
        )

    def check_ticket(
        self,
        ticket: Any,
        extraction_result: Any,
        candidates: list[ProcessedTicketView],
        *,
        current_embedding: list[float] | None = None,
    ) -> DeduplicationResult:
        """
        Convenience: run check using NormalizedTicket + ExtractionResult.

        ticket: from ingestion (ticket_id, cleaned_text, received_at, customer).
        extraction_result: from requiredFieldExtraction (fields.account_id, fields.error_message, etc.).
        """
        account_id = getattr(ticket, "customer", None) and getattr(
            ticket.customer, "account_id", None
        )
        if not account_id and extraction_result and hasattr(extraction_result, "fields"):
            account_id = getattr(extraction_result.fields, "account_id", None)
        error_message = None
        product = None
        if extraction_result and hasattr(extraction_result, "fields"):
            error_message = getattr(extraction_result.fields, "error_message", None)
            product = getattr(extraction_result.fields, "product", None)
        received_at = getattr(ticket, "received_at", None)
        cleaned_text = getattr(ticket, "cleaned_text", "") or ""
        ticket_id = getattr(ticket, "ticket_id", "")
        return self.check(
            ticket_id=ticket_id,
            account_id=account_id,
            error_message=error_message,
            received_at=received_at,
            cleaned_text=cleaned_text,
            current_embedding=current_embedding,
            candidates=candidates,
            product=product,
        )


def _already_matched(candidate_id: str, matches: list[DuplicateMatch]) -> bool:
    return any(m.candidate_ticket_id == candidate_id for m in matches)
