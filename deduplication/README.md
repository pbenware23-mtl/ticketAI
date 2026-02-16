# Deduplication Module

Before response/routing, detect duplicates (README §3).

## Methods

1. **Semantic similarity** — Embeddings + vector DB; cosine similarity threshold (e.g. >0.92).
2. **Metadata matching** — Same account, same error string, same timeframe.
3. **Incident correlation** — Link to active outage.

## Actions (README)

| Case            | Action        |
|-----------------|---------------|
| Exact duplicate | Auto-merge    |
| Likely duplicate| Agent review  |
| Known incident  | Link + notify |

## Usage

```python
from deduplication import (
    DeduplicationService,
    DeduplicationResult,
    ProcessedTicketView,
)

svc = DeduplicationService(
    semantic_exact_threshold=0.92,
    semantic_likely_threshold=0.85,
    metadata_time_window_hours=1.0,
)

# Candidates: previously processed tickets (e.g. from same account or vector store)
candidates = [
    ProcessedTicketView(
        ticket_id="TKT-OLD",
        account_id="acct-1",
        error_message="401 invalid token",
        received_at=...,
        cleaned_text="Getting 401 when calling API",
    ),
]

result = svc.check(
    ticket_id="TKT-NEW",
    account_id="acct-1",
    error_message="401 invalid token",
    received_at=...,
    cleaned_text="Same 401 invalid token on login",
    current_embedding=None,
    candidates=candidates,
)
# result.action: auto_merge | agent_review | link_notify | none
# result.matches, result.is_duplicate
```

With **ticket + extraction result** (pipeline convenience):

```python
from deduplication import DeduplicationService
# ticket: NormalizedTicket, extraction_result: ExtractionResult
result = svc.check_ticket(ticket, extraction_result, candidates)
```

## Optional: semantic similarity

Pass an embedding function to use cosine similarity (exact ≥0.92, likely ≥0.85):

```python
def my_embedding_fn(text: str) -> list[float]:
    # e.g. OpenAI embedding, sentence-transformers
    return [...]

svc = DeduplicationService(embedding_fn=my_embedding_fn)
# Candidates can have precomputed .embedding or leave empty to compute from cleaned_text
```

## Optional: incident correlation

Pass one of:

- `get_active_incident_ids: () -> list[str]` — returns active incident IDs to link to.
- `link_to_incident: (ticket_id, account_id, product) -> str | None` — returns incident ID if this ticket should link.

When a link is found, `action` is `link_notify` and `linked_incident_id` is set.

## Pipeline

Ingestion → Classification → Field extraction → **Deduplication** → Response → Routing.
