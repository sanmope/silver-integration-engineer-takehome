from fastapi import FastAPI
from models import HealthStatus 
from credentials.local import LocalCredentialStore
from connector import ThreatVendorConnector
from jobs.sync_status import SyncStatus
from jobs.task import sync_vendor_indicators

from pydantic import BaseModel
from datetime import datetime
from config import config

app = FastAPI()

class HealthStatusResponse(BaseModel):
    integration: HealthStatus

class ConnectorHealth(BaseModel):
    connector_auth: str
    last_sync_status: str | None = None
    credential_expiry: datetime | None = None
    
class SyncStatusResponse(BaseModel):
    integration_id: str
    last_sync: datetime | None = None
    last_status: str 
    error_count: int


@app.get("/status/{integration_id}", response_model=HealthStatusResponse, status_code=200)
def getHealthAllStatus(integration_id: str) -> HealthStatusResponse:

    sync_status = SyncStatus(config.sync_status).load(integration_id)

    health_status = HealthStatus(
        status =  sync_status['status']  if sync_status and 'status' in sync_status else 'Unknown',
        last_sync = sync_status['last_sync'] if sync_status and 'last_sync' in sync_status else None,
        last_status = sync_status['last_status'] if sync_status and 'last_status' in sync_status else 'Unknown',
    )
    
    return HealthStatusResponse(
        integration = health_status
    )

@app.post("/sync/{integration_id}", response_model=SyncStatusResponse, status_code=200)
def getsyncStatus(integration_id: str) -> SyncStatusResponse:
    
    syncResult = sync_vendor_indicators.apply(args=[integration_id]).get()
    return SyncStatusResponse(
        integration_id = integration_id,
        last_sync = syncResult.completed_at.isoformat(),
        last_status="success" if syncResult.success else "failed",
        error_count=len(syncResult.errors)
    )
    



    


@app.get("/health", response_model=ConnectorHealth)
def getStatus(integration_id: str | None = None) -> ConnectorHealth:
    print(f"base_url: {config.base_url}")

    syncStatus = SyncStatus(config.sync_status)
    if not integration_id:
        integration_id = config.integration_ids[0]
    
    store = LocalCredentialStore(
        path = config.credentials_path,
        fernet_key = config.fernet_key.encode()
    )

    creds = store.get(integration_id)
    if creds is None:
        raise ValueError(f"No credentials found for {integration_id}")
    
    #Get last sync from status
    status = syncStatus.load(integration_id)
    last_sync_status = status["last_status"] if status and "last_status" in status else None

    #Iniziaize Conector
    with ThreatVendorConnector(creds.client_id, creds.client_secret, base_url=config.base_url) as connector:
        try:
            connector.authenticate()
            connector_auth = "ok"
        except Exception as e:
            print(f"Auth error: {e}")
            connector_auth = "error"
        credential_expiry = connector._token_expiry

        return ConnectorHealth(
            connector_auth = connector_auth,
            last_sync_status = last_sync_status,
            credential_expiry = credential_expiry,
        )        

