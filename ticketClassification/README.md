# Ticket Classification Module

Category and severity classification using the README taxonomy. Consumes **NormalizedTicket** from the ingestion layer and returns **TicketClassificationResult** (category + confidence, severity P1–P4 + reason, and human-review flag).

## Category model (README)

- **Taxonomy**: Billing/Payments, Account Access, Technical Bug, Feature Request, Integration Issue, Security/Abuse, General Inquiry, Other
- **Output**: `CategoryResult(category, confidence 0–1)`
- **Confidence threshold**: Below threshold → `needs_human_review: true` (fallback to human review)

## Severity detection (README)

- **Signals**: System outage, payment failure, security breach, VIP/revenue impact, SLA breach risk
- **Levels**:
  - **P1** — Outage / critical (Immediate)
  - **P2** — Major degradation (<4h)
  - **P3** — Standard issue (<24h)
  - **P4** — Low / request (Backlog)
- **Output**: `SeverityResult(severity, reason)`

## Usage

```python
from ingestion.schema import NormalizedTicket  # from ingestion module
from ticketClassification import ClassificationService, TicketClassificationResult

svc = ClassificationService(confidence_threshold=0.8)
# ticket: NormalizedTicket from ingestion
result: TicketClassificationResult = svc.classify(ticket)

print(result.category.category, result.category.confidence)
print(result.severity.severity, result.severity.reason)
print("Needs human review:", result.needs_human_review)
```

## LLM integration (optional)

Both category and severity support an optional LLM for better accuracy. Pass a callable that takes the prompt string and returns the model response:

```python
from ticketClassification import CategoryModel, SeverityModel, ClassificationService

def my_llm(prompt: str) -> str:
    # e.g. OpenAI, Anthropic, etc.
    return response_text

category_model = CategoryModel(llm_fn=my_llm, confidence_threshold=0.8)
severity_model = SeverityModel(llm_fn=my_llm)
svc = ClassificationService(category_model=category_model, severity_model=severity_model)
```

Without an LLM, rule-based keyword/signal logic is used (category keywords and severity patterns from the README).

## Pipeline

Ingestion → **Classification** → (next: field extraction, deduplication, response, routing).
