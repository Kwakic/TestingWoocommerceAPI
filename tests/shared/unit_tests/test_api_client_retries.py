"""Unit tests for APIClient retry safety and server-provided retry delays."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests

from EcommerceAPI.src.clients.api_client import APIClient
from EcommerceAPI.src.core.request_context import RequestContext


def _make_client() -> APIClient:
    auth_strategy = Mock()
    auth_strategy.apply.side_effect = lambda request_kwargs: request_kwargs

    client = APIClient(
        base_url="https://example.test/wp-json/wc/v3",
        retries=3,
        backoff=1,
        auth_strategy=auth_strategy,
    )
    client.http_client = Mock()
    return client


def _context(method: str) -> RequestContext:
    return RequestContext(
        method=method,
        url="https://example.test/wp-json/wc/v3/customers",
        headers={"Content-Type": "application/json"},
        json={"email": "customer@example.test"},
    )


def test_post_response_is_not_retried(monkeypatch):
    client = _make_client()
    response = SimpleNamespace(status_code=503, headers={})
    client.http_client.request.return_value = response
    sleep = Mock()
    monkeypatch.setattr("EcommerceAPI.src.clients.api_client.time.sleep", sleep)

    result = client._request_with_backoff(_context("POST"))

    assert result is response
    client.http_client.request.assert_called_once()
    sleep.assert_not_called()


def test_post_network_error_is_not_retried(monkeypatch):
    client = _make_client()
    error = requests.ConnectionError("connection dropped")
    client.http_client.request.side_effect = error
    sleep = Mock()
    monkeypatch.setattr("EcommerceAPI.src.clients.api_client.time.sleep", sleep)

    with pytest.raises(requests.ConnectionError, match="connection dropped"):
        client._request_with_backoff(_context("POST"))

    client.http_client.request.assert_called_once()
    sleep.assert_not_called()


def test_get_retries_429_after_retry_after_delay(monkeypatch):
    client = _make_client()
    rate_limited = SimpleNamespace(
        status_code=429,
        headers={"Retry-After": "5"},
    )
    success = SimpleNamespace(status_code=200, headers={})
    client.http_client.request.side_effect = [rate_limited, success]
    sleep = Mock()
    monkeypatch.setattr("EcommerceAPI.src.clients.api_client.time.sleep", sleep)
    monkeypatch.setattr("EcommerceAPI.src.clients.api_client.uniform", lambda *_: 0.0)

    result = client._request_with_backoff(_context("GET"))

    assert result is success
    assert client.http_client.request.call_count == 2
    sleep.assert_called_once_with(5.0)
