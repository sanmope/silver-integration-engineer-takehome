from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class IndicatorType(str, Enum):
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    HASH = "hash"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Indicator(BaseModel):
    model_config = {"frozen": True}

    id: UUID
    type: IndicatorType
    value: str
    severity: Severity
    confidence: int
    tags: list[str] = []
    first_seen: datetime
    updated_at: datetime
    metadata: dict[str, Any] | None = None



class SyncResult(BaseModel):
    success: bool
    started_at: datetime
    completed_at: datetime
    indicators_fetched: int
    indicators_new: int
    indicators_updated: int
    errors: list[str] = []

class Credentials(BaseModel):
    client_id: str
    client_secret: str
    access_token: str | None = None
    token_expiry: datetime | None = None

class HealthStatus(BaseModel):
    status: str
    last_sync: datetime | None = None
    last_status: str
