"""
Deduplication layer (README §3).

Before response/routing, detect duplicates via:
- Semantic similarity (embeddings + cosine threshold e.g. >0.92)
- Metadata matching (same account, same error string, same timeframe)
- Incident correlation (link to active outage)

Actions: Exact duplicate → Auto-merge; Likely duplicate → Agent review; Known incident → Link + notify.
"""

from deduplication.schema import (
    DuplicateMatchType,
    DeduplicationAction,
    DuplicateMatch,
    DeduplicationResult,
    ProcessedTicketView,
)
from deduplication.service import DeduplicationService

__all__ = [
    "DuplicateMatchType",
    "DeduplicationAction",
    "DuplicateMatch",
    "DeduplicationResult",
    "ProcessedTicketView",
    "DeduplicationService",
]
