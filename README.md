# Augur Security — Senior Integration Engineer Take-Home

## Overview

Build a **Vendor Integration Connector** that demonstrates your ability to consume third-party security APIs, handle authentication, manage background sync jobs, and export threat data in industry-standard formats.

**Time estimate:** 4-5 hours

**Deliverable:** GitHub repository with working code and documentation

---

## The Scenario

Augur needs to integrate with a new security vendor. Your job is to build a connector that:

1. Authenticates using OAuth2 client credentials
2. Pulls threat indicators with pagination and rate limiting
3. Syncs data on a schedule with proper error handling
4. Exports data in multiple formats (EDL, STIX, CSV)

We provide a mock vendor API specification for you to integrate against.

---

## Part 1: Mock Vendor API

We've defined a mock "ThreatVendor" API. You can either:

- **Option A:** Build the mock API yourself (adds ~30 min, shows full-stack thinking)
- **Option B:** Mock the responses in your connector tests (faster)

See `mock-api-spec.md` for the full API specification.

---

## Part 2: Connector Implementation (40%)

Build a Python connector class with the following capabilities:

```python
class ThreatVendorConnector:
    def __init__(self, client_id: str, client_secret: str, base_url: str):
        ...
    
    def authenticate(self) -> None:
        """Get OAuth token, handle expiry and refresh."""
        
    def fetch_indicators(self, updated_since: datetime | None = None) -> Iterator[Indicator]:
        """Paginate through all indicators, yielding normalized objects."""
        
    def sync(self, last_sync: datetime | None = None) -> SyncResult:
        """Full sync operation with metrics (fetched, new, updated, errors)."""
```

**Requirements:**

- OAuth2 token management (fetch, cache, auto-refresh before expiry)
- Pagination handling (follow `has_more` until exhausted)
- Rate limiting (respect 429, use Retry-After header, exponential backoff)
- Retry logic (transient failures with configurable max retries)
- Timeout handling
- Proper logging (debug for requests, info for sync progress, error for failures)

**Deliverables:**

- `connector.py` — Connector class
- `models.py` — Pydantic models for Indicator, SyncResult, etc.
- Unit tests mocking the HTTP layer

---

## Part 3: Credential Management (15%)

Build a simple credential store abstraction:

```python
class CredentialStore(ABC):
    @abstractmethod
    def get(self, integration_id: str) -> Credentials | None: ...
    
    @abstractmethod
    def store(self, integration_id: str, credentials: Credentials) -> None: ...
    
    @abstractmethod
    def delete(self, integration_id: str) -> None: ...

class LocalCredentialStore(CredentialStore):
    """File-based store for local dev (encrypted at rest)."""

class AWSSecretsStore(CredentialStore):
    """AWS Secrets Manager implementation (can be stubbed)."""
```

**Requirements:**

- Abstract interface for credential storage
- Local implementation using encrypted file (Fernet or similar)
- AWS Secrets Manager implementation (can stub the boto3 calls)
- Credentials model with `client_id`, `client_secret`, `access_token`, `token_expiry`

---

## Part 4: Background Job System (25%)

Implement a sync job that runs on a schedule:

```python
# Using Celery, RQ, or APScheduler

@task
def sync_vendor_indicators(integration_id: str) -> SyncResult:
    """
    1. Load credentials from store
    2. Initialize connector
    3. Run sync (incremental from last_sync timestamp)
    4. Store results and update last_sync
    5. Handle errors and retry logic
    """
```

**Requirements:**

- Configurable schedule (e.g., every 15 minutes)
- Incremental sync (only fetch indicators updated since last successful sync)
- Error handling with retry (max 3 attempts, exponential backoff)
- Dead letter handling (after max retries, log and alert)
- Sync status tracking (last_sync, last_status, error_count)

**Deliverables:**

- `tasks.py` — Celery/RQ task
- `sync_status.py` — Status tracking (can be simple JSON file or SQLite)
- Show how you'd monitor failed jobs

---

## Part 5: Feed Exports (20%)

Export synced indicators in three formats:

### 1. EDL (External Dynamic List)

Plain text, one indicator per line:

```
185.220.101.34
192.168.1.100
malware-c2.evil.com
```

### 2. CSV

```csv
type,value,severity,tags,updated_at
ip,185.220.101.34,critical,"tor-exit,botnet",2026-02-10T14:22:00Z
domain,malware-c2.evil.com,high,c2,2026-02-08T00:00:00Z
```

### 3. STIX 2.1 Bundle

```json
{
  "type": "bundle",
  "id": "bundle--uuid",
  "objects": [
    {
      "type": "indicator",
      "id": "indicator--uuid",
      "pattern": "[ipv4-addr:value = '185.220.101.34']",
      "pattern_type": "stix",
      "valid_from": "2026-02-10T14:22:00Z",
      "labels": ["tor-exit", "botnet"]
    }
  ]
}
```

**Requirements:**

- Filter by type (ip, domain, hash) and severity
- Efficient streaming for large datasets (don't load all into memory)
- S3 upload capability (can stub boto3, show the interface)

**Deliverables:**

- `exporters/edl.py`, `exporters/csv_exporter.py`, `exporters/stix.py`
- Base exporter class with common filtering logic
- Example of S3 upload (stubbed is fine)

---

## Evaluation Criteria

| Category | Weight | What We're Looking For |
|----------|--------|------------------------|
| **Connector Quality** | 40% | Auth handling, pagination, rate limiting, retries, error handling |
| **Job System** | 25% | Scheduling, incremental sync, failure handling, status tracking |
| **Feed Exports** | 20% | Correct formats, filtering, streaming for large data |
| **Credential Management** | 15% | Clean abstraction, encryption, AWS interface |

---

## Bonus (Optional, pick one)

1. **Flask → FastAPI migration:** Show how you'd expose the sync status and trigger manual syncs via a FastAPI endpoint

2. **Sigma rule deployment:** Given a Sigma rule YAML, show how you'd convert it to a Splunk SPL query or CrowdStrike Custom IOA format

3. **Health checks:** Build a `/health` endpoint that checks connector auth validity, last sync status, and credential expiry

---

## Tech Requirements

- Python 3.10+
- `httpx` or `requests` for HTTP
- `pydantic` for data models
- Celery, RQ, or APScheduler for jobs
- `cryptography` (Fernet) for local credential encryption
- `pytest` for tests

---

## What We're Looking For

- **Production patterns:** This is how we actually build connectors. Show us you understand the failure modes.
- **Error handling:** What happens when the vendor API is down? When creds expire mid-sync? When rate limited?
- **Incremental sync:** Don't re-fetch everything every time.
- **Clean abstractions:** Credential store interface, exporter base class, connector pattern.
- **Tests:** Mock the HTTP layer, test the retry logic, test the export formats.

---

## What We're NOT Looking For

- Actual vendor API access (mock everything)
- Perfect STIX compliance (close enough is fine)
- Production deployment configs
- UI of any kind

---

## Submission

1. GitHub repo with code
2. README with:
   - Setup instructions
   - How to run tests
   - Design decisions
   - What you'd improve with more time
3. Email the link to [RECRUITER EMAIL]

---

## Questions?

Make reasonable assumptions and document them. Real vendor APIs are messier than this mock. Show us how you'd handle the mess.
