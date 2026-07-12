"""Retry/backoff behaviour of okama_macro/sources/fred.get_series (#33).

A transient upstream 5xx (FRED/proxy hiccup) must not fail the whole nightly run:
get_series retries a few times on a 5xx before giving up. Client errors (4xx) are
NOT retried. ``time.sleep`` is mocked so the tests are fast.
"""

import pytest
import requests

from okama_macro import _http
from okama_macro.sources import fred

_GOOD_PAYLOAD = {"count": 1, "observations": [{"date": "2020-01-01", "value": "1.5"}]}


class _Resp:
    """Minimal stand-in for a requests.Response."""

    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f"{self.status_code} Server Error")
            err.response = self  # real 5xx errors carry the response
            raise err

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def _fast_env(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "k")
    monkeypatch.setattr(_http.time, "sleep", lambda *a, **k: None)


def _sequence_get(responses, calls):
    def _get(url, **kwargs):
        calls.append(1)
        return responses[len(calls) - 1]
    return _get


def test_retries_transient_5xx_then_succeeds(monkeypatch):
    calls: list = []
    monkeypatch.setattr(
        _http.requests, "get",
        _sequence_get([_Resp(502), _Resp(200, _GOOD_PAYLOAD)], calls),
    )

    df = fred.get_series("DFF")

    assert len(calls) == 2                 # retried once, then succeeded
    assert df.iloc[0, 0] == pytest.approx(1.5)


def test_persistent_5xx_raises_after_max_attempts(monkeypatch):
    calls: list = []
    monkeypatch.setattr(
        _http.requests, "get",
        lambda url, **kwargs: calls.append(1) or _Resp(503),
    )

    with pytest.raises(RuntimeError, match="DFF"):
        fred.get_series("DFF")

    assert len(calls) == fred._MAX_ATTEMPTS


def test_client_error_4xx_is_not_retried(monkeypatch):
    calls: list = []
    monkeypatch.setattr(
        _http.requests, "get",
        lambda url, **kwargs: calls.append(1) or _Resp(404),
    )

    with pytest.raises(RuntimeError, match="DFF"):
        fred.get_series("DFF")

    assert len(calls) == 1                 # 4xx fails fast, no retry
