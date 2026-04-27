import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from models import Credentials, SyncResult
from jobs.tasks import sync_vendor_indicators


@pytest.fixture
def mock_credentials():
    return Credentials(
        client_id="test_client",
        client_secret="test_secret",
    )


@pytest.fixture
def mock_sync_result():
    now = datetime.now(timezone.utc)
    return SyncResult(
        success=True,
        started_at=now,
        completed_at=now,
        indicators_fetched=3,
        indicators_new=2,
        indicators_updated=1,
        errors=[],
    )


def test_sync_success(mock_credentials, mock_sync_result):
    with patch("jobs.tasks.LocalCredentialStore") as MockStore, \
         patch("jobs.tasks.ThreatVendorConnector") as MockConnector, \
         patch("jobs.tasks.SyncStatus") as MockStatus:

        MockStore.return_value.get.return_value = mock_credentials
        MockStatus.return_value.load.return_value = None

        mock_connector_instance = MagicMock()
        mock_connector_instance.__enter__ = MagicMock(return_value=mock_connector_instance)
        mock_connector_instance.__exit__ = MagicMock(return_value=False)
        mock_connector_instance.sync.return_value = mock_sync_result
        MockConnector.return_value = mock_connector_instance

        result = sync_vendor_indicators.apply(args=["integration_123"]).get()

        assert result.success is True
        assert result.indicators_fetched == 3
        MockStatus.return_value.update.assert_called_once()


def test_sync_no_credentials():
    with patch("jobs.tasks.LocalCredentialStore") as MockStore, \
         patch("jobs.tasks.SyncStatus"):

        MockStore.return_value.get.return_value = None

        result = sync_vendor_indicators.apply(args=["integration_missing"])
        assert result.result is None


def test_sync_retry_on_failure(mock_credentials):
    with patch("jobs.tasks.LocalCredentialStore") as MockStore, \
         patch("jobs.tasks.ThreatVendorConnector") as MockConnector, \
         patch("jobs.tasks.SyncStatus") as MockStatus:

        MockStore.return_value.get.return_value = mock_credentials
        MockStatus.return_value.load.return_value = None

        mock_connector_instance = MagicMock()
        mock_connector_instance.__enter__ = MagicMock(return_value=mock_connector_instance)
        mock_connector_instance.__exit__ = MagicMock(return_value=False)
        mock_connector_instance.sync.side_effect = Exception("Connection error")
        MockConnector.return_value = mock_connector_instance

        result = sync_vendor_indicators.apply(args=["integration_123"])
        assert result.result is None