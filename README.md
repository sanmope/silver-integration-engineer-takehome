# Augur Security — Vendor Integration Connector

A production-pattern connector that pulls threat indicators from a third-party security vendor, syncs them on a schedule, stores them securely, and exports them in industry-standard formats (EDL, CSV, STIX 2.1). Built to demonstrate real-world failure handling: token expiry mid-sync, rate limiting, transient server errors, and incremental sync.

---

## Setup

```bash
git clone https://github.com/sanmope/silver-integration-engineer-takehome
cd silver-integration-engineer-takehome
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Environment variables

| Variable | Description | Default |
|---|---|---|
| `BASE_URL` | ThreatVendor API base URL | `https://api.threatvendor.example.com` |
| `FERNET_KEY` | Fernet encryption key for local credential store | — |
| `CREDENTIALS_PATH` | Path to encrypted credentials file | `credentials.enc` |
| `BROKER_URL` | Celery broker (Redis) | `redis://localhost:6379/0` |
| `BACKEND_URL` | Celery result backend (Redis) | `redis://localhost:6379/1` |
| `INTEGRATION_IDS` | Comma-separated list of integration IDs | `integration_123` |
| `SYNC_INTERVAL_SECONDS` | Background sync interval | `900` |

---

## Demo

```bash
# Start all services (Redis, Celery worker, Celery beat, mock vendor API)
docker-compose up

# In a separate terminal — store credentials and trigger a sync
python demo.py
```

The demo auto-generates and saves a `FERNET_KEY` to `.env` if one does not exist.


### Live Demo
- Mock Vendor API: https://silver-integration-engineer-takehome-production.up.railway.app/docs
- API: https://<tu-url-api>.up.railway.app/docs

---

## Running Tests

```bash
pytest -v
pytest --cov=src --cov-report=term-missing
```

---

## API (Bonus)

```bash
PYTHONPATH=src uvicorn src.api.main:app --port 8001 --reload
```

| Endpoint | Description |
|---|---|
| `GET /health` | Connector auth validity, last sync status, credential expiry |
| `GET /status/{integration_id}` | Sync status for a specific integration |
| `POST /sync/{integration_id}` | Trigger a manual sync |

Swagger UI available at `http://localhost:8001/docs`.

---

## Design Decisions

**Connector**
- Generator in `fetch_indicators` — O(1) memory per page, regardless of dataset size
- `_ensure_authenticated` with 60s buffer — prevents 401 mid-sync when token expires between auth check and API call
- 429 uses `Retry-After` header exactly — no fixed delays
- 5xx uses exponential backoff (`3 * 2^retries`); breaks out of pagination loop after `max_retries` rather than crashing
- `force_429` flag in mock server — makes retry logic fully testable without a real rate limit

**Credential Store**
- `LocalCredentialStore` and `AWSSecretsStore` implement the same `CredentialStore` ABC — swapping local for AWS requires only config changes
- All writes use `.tmp` + rename — file is never corrupted if process dies mid-write
- Fernet encryption at rest; on-disk format is `integration_id → encrypted_bytes (base64)`

**Sync Status**
- Atomic JSON file with `.tmp` + rename
- `last_sync` stored as ISO 8601 string — human-readable, no datetime serialization issues
- New vs updated heuristic: `first_seen >= last_sync` → new, `updated_at >= last_sync` → updated

**Background Jobs**
- Beat schedule built dynamically from `config.integration_ids` — adding an integration only requires config change
- Retry with `countdown=2 ** retries`; after `max_retries=3` logs CRITICAL and returns (dead letter handling)
- Incremental sync: reads `last_sync` from status file, passes to `fetch_indicators(updated_since=last_sync)`

**Exporters**
- Filtering centralized in `BaseExporter.filter()` — concrete exporters never duplicate filter logic
- `export()` receives an open `IO` object — caller owns file lifecycle, composable with S3 multipart uploads
- `EdlExporter` hardcodes `indicator_types=[IP, DOMAIN, URL]` — hashes have no meaning in a firewall blocklist
- STIX uses `stix2` library for schema validation and correct pattern syntax; unknown types are logged and skipped

---

## What I'd Improve With More Time

- **Specific exceptions** — replace generic `Exception` in `authenticate()` with a dedicated `AuthenticationError`
- **`list_all()` on `CredentialStore`** — discover integrations from the store rather than requiring them in config
- **Credential store factory** — a `get_credential_store()` factory driven by a `CREDENTIAL_BACKEND=local|aws` env var, so the API and tasks never hardcode `LocalCredentialStore`
- **`integration_ids` from credential store** — currently sourced from config; in prod should be discovered dynamically via `store.list_all()`
- **S3 export** — `BaseExporter` already accepts any `IO` object; wiring to `boto3.client('s3').upload_fileobj` requires no exporter changes
- **Structured logging with correlation IDs** — trace a complete sync across worker logs
- **Dead letter queue** — publish to SNS or a dedicated Celery queue instead of just logging CRITICAL
- **`last_sync` timezone enforcement** — validate and coerce to UTC at the task boundary rather than relying on convention
