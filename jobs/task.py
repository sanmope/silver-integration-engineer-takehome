from models import Credentials
from conector import ThreatVendorConnector
from local import LocalCredentialStore
from config import config
from celery_app import app
from sync_status import SyncStatus 
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=3)
def sync_vendor_indicators(self,integration_id: str):
    sync_status = SyncStatus(config.sync_status)
    try:
        store = LocalCredentialStore(
            path = config.credentials_path,
            fernet_key = config.fernet_key.encode()
        )

        creds = store.get(integration_id)
        if creds is None:
            raise ValueError(f"No credentials found for {integration_id}")
        
        #Get last sync from status
        status = sync_status.load(integration_id)
        last_sync = datetime.fromisoformat(status["last_sync"]) if status and "last_sync" in status else None

        #Iniziaize Conector
        with ThreatVendorConnector(creds.client_id, creds.client_secret) as connector:
            sync_result =  connector.sync(last_sync)
            sync_status.update(
                integration_id,
                last_sync = sync_result.completed_at.isoformat(),
                last_status="success" if sync_result.success else "failed",
                error_count=len(sync_result.errors)
            )
            return sync_result

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            # dead letter handling
            logger.critical("Task permanently failed: %s", integration_id)
            sync_status.update(integration_id, last_status="failed")
            return  # no re-raise
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

