from fastapi import FastAPI, Form, HTTPException, Depends
from fastapi.security import  HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import uuid 
from models import Indicator



SAMPLE_DATA = [
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "ip",
    "value": "185.220.101.34",
    "severity": "critical",
    "confidence": 95,
    "tags": ["tor-exit", "botnet"],
    "first_seen": "2026-01-15T08:30:00Z",
    "updated_at": "2026-02-10T14:22:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "type": "domain",
    "value": "malware-c2.evil.com",
    "severity": "high",
    "confidence": 88,
    "tags": ["c2", "malware"],
    "first_seen": "2026-02-01T12:00:00Z",
    "updated_at": "2026-02-08T00:00:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "type": "hash",
    "value": "44d88612fea8a8f36de82e1234567890abcdef12",
    "severity": "critical",
    "confidence": 100,
    "tags": ["ransomware", "lockbit"],
    "first_seen": "2026-02-05T16:45:00Z",
    "updated_at": "2026-02-09T10:00:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "type": "ip",
    "value": "192.168.100.50",
    "severity": "medium",
    "confidence": 72,
    "tags": ["scanner"],
    "first_seen": "2026-01-20T09:00:00Z",
    "updated_at": "2026-02-07T11:30:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440004",
    "type": "url",
    "value": "https://phishing-site.example.com/login",
    "severity": "high",
    "confidence": 91,
    "tags": ["phishing", "credential-theft"],
    "first_seen": "2026-02-03T14:20:00Z",
    "updated_at": "2026-02-10T08:15:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440005",
    "type": "domain",
    "value": "suspicious-download.net",
    "severity": "low",
    "confidence": 55,
    "tags": ["suspicious"],
    "first_seen": "2026-01-28T22:10:00Z",
    "updated_at": "2026-02-06T17:45:00Z"
  }
]


app = FastAPI()

#Design decision:  dict instead of DB for this purpose, no conf needed, if in prod, DB
active_tokens: dict[str, datetime] = {}

class ResponseToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int 


@app.post("/oauth/token", response_model=ResponseToken, status_code=200)
def create_token(
    client_id: str = Form(...),
    client_secret: str = Form(...),
    grant_type: str = Form(...),
) -> ResponseToken:

    #Validate Credentials
    if client_id != "test_client" or client_secret != "test_secret":
        raise HTTPException(status_code=401, detail={"error": "invalid_client"})

    #Create token
    token = str(uuid.uuid4())
    active_tokens[token] = datetime.now(tz=timezone.utc) + timedelta(seconds=3600)
    

    return ResponseToken(
        access_token = token,
        token_type = "Bearer",
        expires_in = 3600
    )


#delegate format validation of Header to FastApi
security = HTTPBearer()

class Pagination(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    has_more: bool
    
class ResponseIndicators(BaseModel):
    data: list[Indicator]
    pagination: Pagination



@app.get("/api/v1/indicators", response_model=ResponseIndicators, status_code=200)
def get_indicators(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    page: int = 1,
    limit: int = 100,
    updated_since: datetime | None = None,
    type: str | None = None,
    severity: str | None = None,
    force_429: bool = False,

) -> ResponseIndicators:

    token = credentials.credentials
    if token not in active_tokens or active_tokens[token] < datetime.now(tz=timezone.utc):
        raise HTTPException(status_code=401, detail={"error": "Not valid credentials"})

    #For the purpose of the challenge, the condition is emulated, generate real\
    #condition could lead to complex errors
    if force_429:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "error_description": "Rate limit of 100 requests per minute exceeded",
                "retry_after": 60,
            },
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(datetime.now(tz=timezone.utc).timestamp()) + 60),
            },
        )

    #In production, filtering should be applied before object\
    #instantiation to avoid allocating objects that will be discarded.
    indicators = [Indicator(**item) for item in SAMPLE_DATA]

    #More friendly to chop instead of returning error
    limit = min(limit, 500)

    if type:
        indicators = [i for i in indicators if i.type == type]
    if severity:
        indicators = [i for i in indicators if i.severity == severity]
    if updated_since:
        indicators = [i for i in indicators if i.updated_at > updated_since]
    

    total=len(indicators)
    start = (page - 1)*limit
    end = limit*page
    page_data = indicators[start:end]
    total_pages = (len(indicators) + limit - 1) // limit
    has_more = end < len(indicators)

    #Pagination after filtering data, returning only selected
    pagination = Pagination(
        page=page,
        limit=limit,
        total=total,
        total_pages= total_pages,
        has_more = has_more,
    )
    
    return ResponseIndicators(
        data=page_data,
        pagination=pagination,
    )

