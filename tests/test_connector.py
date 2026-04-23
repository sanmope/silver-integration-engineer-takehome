
import pytest
from connector import ThreatVendorConnector
from uuid import UUID


def test_successful_login(httpx_mock):

    httpx_mock.add_response(
        method="POST",
        url="https://api.threatvendor.example.com/oauth/token",
        json={
            "access_token": "test-token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )
    connector = ThreatVendorConnector(
        client_id="test_client",
        client_secret="test_secret",
    )
    connector.authenticate()
    assert connector._access_token == "test-token-123"


def test_fetch_basic(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url="https://api.threatvendor.example.com/oauth/token",
        json={
            "access_token": "test-token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )
    connector = ThreatVendorConnector(
        client_id="test_client",
        client_secret="test_secret",
    )

    httpx_mock.add_response(
        method="GET",
        json={
            "data": [{
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "type": "ip",
                        "value": "185.220.101.34",
                        "severity": "critical",
                        "confidence": 95,
                        "tags": ["tor-exit", "botnet"],
                        "first_seen": "2026-01-15T08:30:00Z",
                        "updated_at": "2026-02-10T14:22:00Z"
                    }],  # Indicators list
            "pagination": {
                "page": 1,
                "limit": 100,
                "total": 1,
                "total_pages": 1,
                "has_more": False,
            }
        },
    )
    
    iterators = connector.fetch_indicators()

    assert list(iterators)[0].id == UUID('550e8400-e29b-41d4-a716-446655440000')


def test_rate_limiting_with_retry(httpx_mock):

    httpx_mock.add_response(
        method="POST",
        url="https://api.threatvendor.example.com/oauth/token",
        json={
            "access_token": "test-token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )
    #First run with a Retry-After 
    httpx_mock.add_response(
        method="GET",
        status_code=429,
        headers={"Retry-After": "1"},
    )

    # Second round of response with the data. 
    httpx_mock.add_response(
    method="GET",
    json={
        "data": [{
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "type": "ip",
                    "value": "185.220.101.34",
                    "severity": "critical",
                    "confidence": 95,
                    "tags": ["tor-exit", "botnet"],
                    "first_seen": "2026-01-15T08:30:00Z",
                    "updated_at": "2026-02-10T14:22:00Z"
                }],  # Indicators list
        "pagination": {
            "page": 1,
            "limit": 100,
            "total": 1,
            "total_pages": 1,
            "has_more": False,
        }
    },
    )

    connector = ThreatVendorConnector(
        client_id="test_client",
        client_secret="test_secret",
    )

    iterators = connector.fetch_indicators()

    assert list(iterators)[0].id == UUID('550e8400-e29b-41d4-a716-446655440000')

def test_5xx_does_not_return_indicators(httpx_mock):

    httpx_mock.add_response(
        method="POST",
        url="https://api.threatvendor.example.com/oauth/token",
        json={
            "access_token": "test-token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )
    #First round
    httpx_mock.add_response(
        method="GET",
        status_code=540,
        headers={"Retry-After": "1"},
    )

    # Second round of response with the data. 
    httpx_mock.add_response(
        method="GET",
        status_code=540,
        headers={"Retry-After": "1"},
    )
    # Third round of response with the data. 
    httpx_mock.add_response(
        method="GET",
        status_code=540,
        headers={"Retry-After": "1"},
    )


    connector = ThreatVendorConnector(
        client_id="test_client",
        client_secret="test_secret",
    )

    iterators = connector.fetch_indicators()

    assert list(iterators) == []