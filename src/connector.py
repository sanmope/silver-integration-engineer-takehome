from datetime import datetime, timezone, timedelta
from time import sleep
import httpx
from typing import Iterator
from models import Indicator, SyncResult

import logging

logger = logging.getLogger(__name__)


class ThreatVendorConnector():

    def __init__(
            self,
            client_id: str,
            client_secret: str,
            base_url: str = "https://api.threatvendor.example.com",
            timeout: float = 30.0,
            max_retries: int = 3,
            
        ):

        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self._access_token: str | None = None
        self._token_expiry: datetime | None = None

        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def authenticate(self) -> None:
        response = self._client.post(
            f"{self.base_url}/oauth/token",
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
        )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception("Invalid Credentials: Http error 401")
            
        data = response.json()
        self._access_token = data["access_token"]
        self._token_expiry = datetime.now(tz=timezone.utc) + timedelta(seconds=data["expires_in"])


    def _ensure_authenticated(self) -> None:
        if not self._token_expiry or self._token_expiry <=  datetime.now(tz=timezone.utc) + timedelta(seconds=60):
            self.authenticate()

    
    def fetch_indicators(
        self,
        updated_since: datetime | None = None,
        indicator_type: str | None = None,
        severity: str | None = None,
    ) -> Iterator[Indicator]:

        self._ensure_authenticated()

        has_more = True
        page = 1
        backoff = 1
        retries = 0

        while has_more:
            self._ensure_authenticated()
            logger.debug("Fetching page %d", page)
            response = self._client.get(
                f"{self.base_url}/api/v1/indicators",
                headers={"Authorization": f"Bearer {self._access_token}"},
                params={
                    "page": page,
                    "limit": 500,
                    "updated_since": updated_since.isoformat() if updated_since else None,
                    "severity": severity,
                    "force_429": False,
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers["Retry-After"])
                    logger.warning("Rate limited, waiting %d seconds", retry_after)
                    sleep(retry_after)
                    continue
                
                if 500 <= e.response.status_code <= 599:
                    logger.error("Server error %d on page %d, retry %d/%d", 
                        e.response.status_code, page, retries, self.max_retries)
                    retries += 1
                    if retries >= self.max_retries:
                        logger.error("Max retries reached for page %d", page)
                        break
                    sleep(3*backoff)
                    backoff *=2
                    continue


            dataResponse = response.json()
            has_more = dataResponse["pagination"]["has_more"]
            page += 1
            data = dataResponse["data"]

            for indicator in [Indicator(**item) for item in data]:
                yield indicator
            
            backoff = 1
            retries = 0


    def sync(self, last_sync: datetime | None = None) -> SyncResult:
        started_at = datetime.now(tz=timezone.utc)
        indicators = self.fetch_indicators(last_sync)

        indicators_new = 0 
        indicators_updated = 0
        fetched = 0
        try:

            #Track metrics, if last_sync is None it means first run\
            #if first_seen is greater or equal to last_sync it means is a new indicator\
            #if updated_at is greater or equal to last_sync it means is an updated indicator.
            for indicator in indicators:
                fetched += 1
                if last_sync is None:
                    indicators_new += 1
                elif indicator.first_seen >= last_sync:
                    indicators_new += 1
                elif indicator.updated_at >= last_sync:
                    indicators_updated += 1
            
            return SyncResult(
                success = True,
                started_at = started_at,
                completed_at = datetime.now(tz=timezone.utc),
                indicators_fetched = fetched,
                indicators_new = indicators_new,
                indicators_updated = indicators_updated,
                errors = []
            )           
        
        except Exception as e:
            logger.error("Sync failed: %s", e)
            return SyncResult(
                success = False,
                started_at = started_at,
                completed_at = datetime.now(tz=timezone.utc),
                indicators_fetched = fetched,
                indicators_new = indicators_new,
                indicators_updated = indicators_updated,
                errors = [str(e)],
            )





