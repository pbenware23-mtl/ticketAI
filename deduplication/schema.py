"""
Deduplication schema from README §3.

Methods: Semantic similarity, Metadata matching, Incident correlation.
Actions: Exact duplicate → Auto-merge, Likely duplicate → Agent review, Known incident → Link + notify.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DuplicateMatchType(str, Enum):
    """How the duplicate was detected."""

    EXACT = "exact"  # Auto-merge
    LIKELY = "likely"  # Agent review
    KNOWN_INCIDENT = "known_incident"  # Link + notify


class DeduplicationAction(str, Enum):
    """Recommended action from README."""

    AUTO_MERGE = "auto_merge"  # Exact duplicate
    AGENT_REVIEW = "agent_review"  # Likely duplicate
    LINK_NOTIFY = "link_notify"  # Known incident
    NONE = "none"  # No duplicate found


class DuplicateMatch(BaseModel):
    """A single duplicate candidate with match type and score."""

    candidate_ticket_id: str
    match_type: DuplicateMatchType
    similarity_score: float | None = None  # For semantic match (0–1)
    reason: str = ""  # e.g. "Same account, same error, same hour"


class DeduplicationResult(BaseModel):
    """Result of deduplication check: action and any matches."""

    ticket_id: str
    action: DeduplicationAction = DeduplicationAction.NONE
    matches: list[DuplicateMatch] = Field(default_factory=list)
    linked_incident_id: str | None = None  # When action is LINK_NOTIFY

    @property
    def is_duplicate(self) -> bool:
        return self.action != DeduplicationAction.NONE


class ProcessedTicketView(BaseModel):
    """
    Minimal view of a previously processed ticket for comparison.

    Used as candidate for metadata/semantic matching. Optional embedding
    for semantic similarity (if absent, computed from cleaned_text when embedding_fn provided).
    """

    ticket_id: str
    account_id: str | None = None
    error_message: str | None = None
    received_at: datetime | None = None
    cleaned_text: str = ""
    embedding: list[float] | None = None  # Optional precomputed embedding
