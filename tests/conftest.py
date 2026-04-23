
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from models import Indicator, IndicatorType, Severity

@pytest.fixture
def sample_indicators():
    now = datetime.now(timezone.utc)
    return [
        Indicator(
            id=uuid4(),
            type=IndicatorType.IP,
            value="1.2.3.4",
            severity=Severity.CRITICAL,
            confidence=90,
            first_seen=now,
            updated_at=now,
        ),
        Indicator(
            id=uuid4(),
            type=IndicatorType.DOMAIN,
            value="malware.com",
            severity=Severity.HIGH,
            confidence=80,
            first_seen=now,
            updated_at=now,
        ),
        Indicator(
            id=uuid4(),
            type=IndicatorType.IP,
            value="5.6.7.8",
            severity=Severity.MEDIUM,
            confidence=70,
            first_seen=now,
            updated_at=now,
        ),
        Indicator(
            id=uuid4(),
            type=IndicatorType.HASH,
            value="d41d8cd98f00b204e9800998ecf8427e",
            severity=Severity.MEDIUM,
            confidence=70,
            first_seen=now,
            updated_at=now,
        ),
    ]