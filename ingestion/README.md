# Ticket Triage Ingestion Module

Entry point layer for the AI support ticket workflow. All sources normalize into a single **NormalizedTicket** schema for downstream classification, extraction, and routing.

## Entry point sources

| Source        | HTTP endpoint        | Use case                                      |
|---------------|----------------------|-----------------------------------------------|
| **Email**     | `POST /ingest/email`  | SendGrid, Mailgun, SES inbound webhooks       |
| **Web forms** | `POST /ingest/web-form` | Contact/support form submissions (JSON)   |
| **Chat**      | `POST /ingest/chat`  | Intercom, Zendesk Chat, in-app support        |
| **CRM import**| `POST /ingest/crm`   | Zendesk, Freshdesk, ServiceNow, Salesforce    |
| **Slack**     | `POST /ingest/slack` | Slack events / support channel messages       |
| **Teams**     | `POST /ingest/teams` | Microsoft Teams activities / webhooks        |

## Quick start

```bash
# From repo root
pip install -r requirements.txt
uvicorn ingestion.api.app:app --reload --host 0.0.0.0 --port 8000
```

- Health: `GET http://localhost:8000/health`
- Web form example:  
  `curl -X POST http://localhost:8000/ingest/web-form -H "Content-Type: application/json" -d '{"message":"Cannot log in","subject":"Login issue","email":"user@example.com"}'`

## Schema

- **NormalizedTicket**: `ticket_id`, `source`, `raw_text`, `cleaned_text`, `subject`, `customer` (metadata), `received_at`, `source_id`, `attachments`, `channel_metadata`.
- **TicketSource**: `email` | `web_form` | `chat` | `crm_import` | `slack` | `teams`.

## Using adapters in code

```python
from ingestion.core import IngestionService
from ingestion.sources import WebFormAdapter, EmailAdapter

def on_ingested(ticket):
    # Send to queue (SQS, Kafka, etc.) or DB
    print(ticket.ticket_id, ticket.source, ticket.cleaned_text[:80])

ingestion = IngestionService(on_ingested=on_ingested)
web = WebFormAdapter(ingestion)
email = EmailAdapter(ingestion)

ticket = web.ingest({"message": "Bug in checkout", "email": "a@b.com"})
# ticket is NormalizedTicket; on_ingested(ticket) was already called
```

## Next pipeline stage

Ingestion assigns a ticket ID, timestamp, and customer metadata, and stores raw + cleaned text. Connect `on_ingested` to your queue (Kafka, SQS, Pub/Sub) or workflow engine (Temporal, Airflow) for classification and routing.
