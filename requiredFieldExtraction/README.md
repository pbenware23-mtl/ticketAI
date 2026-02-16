# Required Field Extraction Module

Structured extraction from support tickets (README §2). Normalizes messy tickets into required fields for downstream deduplication, response generation, and routing.

## Fields (README)

**Common fields**
- Customer name, Company, Account ID  
- Product / module  
- Environment (prod/staging/development)  
- Error message  
- Timestamp (mentioned in ticket)  
- Steps to reproduce  
- Attachments mentioned  

**LLM extraction example (README)**  
- Product, Issue type, Error message, Environment, Urgency indicators  

**Data enrichment**  
- Customer name, company, account_id (and plan tier) are merged from the ticket’s customer metadata (ingestion/CRM) when not extracted from text.

## Usage

```python
from ingestion.schema import NormalizedTicket
from requiredFieldExtraction import ExtractionService, ExtractionResult

svc = ExtractionService()
# ticket: NormalizedTicket from ingestion
result: ExtractionResult = svc.extract(ticket)

print(result.fields.product, result.fields.environment, result.fields.error_message)
print(result.fields.urgency, result.fields.steps_to_reproduce)
```

## LLM integration (optional)

Use an LLM for better extraction by passing a `FieldExtractor` with `llm_fn`:

```python
from requiredFieldExtraction import FieldExtractor, ExtractionService

def my_llm(prompt: str) -> str:
    # e.g. OpenAI, Anthropic
    return response_text

extractor = FieldExtractor(llm_fn=my_llm)
svc = ExtractionService(extractor=extractor)
result = svc.extract(ticket)
```

Without an LLM, rule-based extraction is used (environment, urgency, error patterns, steps, attachments).

## Pipeline

Ingestion → Classification → **Required field extraction** → Deduplication → Response → Routing.
