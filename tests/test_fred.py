"""Tests for the FRED data source client (okama_macro/sources/fred.py)."""

import datetime

import pandas as pd
import pytest
import requests

from okama_macro import _http
from okama_macro.sources import fred


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


def _payload(observations: list[dict], count: int | None = None) -> dict:
    return {
        "count": len(observations) if count is None else count,
        "observations": observations,
    }


OBSERVATIONS = [
    {"date": "2026-06-01", "value": "4.33"},
    {"date": "2026-06-02", "value": "."},  # FRED marks missing values with "."
    {"date": "2026-06-03", "value": "4.08"},
]


def test_api_path_parses_observations(monkeypatch):
    captured = {}

    def fake_get(url, params=None, **kwargs):
        captured["url"] = url
        captured["params"] = params
        return FakeResponse(_payload(OBSERVATIONS))

    monkeypatch.setenv("FRED_API_KEY", "test-key")
    monkeypatch.setattr(_http.requests, "get", fake_get)

    df = fred.get_series("DFF", first_date=datetime.datetime(2026, 6, 1))

    assert captured["url"] == fred.FRED_API_URL
    assert captured["params"]["series_id"] == "DFF"
    assert captured["params"]["api_key"] == "test-key"
    assert captured["params"]["observation_start"] == "2026-06-01"
    assert list(df.columns) == ["DFF"]
    assert len(df) == 2  # the "." (missing) observation is dropped
    assert df.index[0] == pd.Timestamp("2026-06-01")
    assert df["DFF"].iloc[-1] == pytest.approx(4.08)


def test_api_path_passes_last_date(monkeypatch):
    captured = {}

    def fake_get(url, params=None, **kwargs):
        captured["params"] = params
        return FakeResponse(_payload(OBSERVATIONS))

    monkeypatch.setenv("FRED_API_KEY", "test-key")
    monkeypatch.setattr(_http.requests, "get", fake_get)

    fred.get_series(
        "DFF",
        first_date=datetime.datetime(2026, 6, 1),
        last_date=datetime.datetime(2026, 6, 3),
    )

    assert captured["params"]["observation_end"] == "2026-06-03"


def test_api_path_raises_on_truncation(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "test-key")

    def fake_get(url, params=None, **kwargs):
        return FakeResponse(_payload(OBSERVATIONS, count=100001))

    monkeypatch.setattr(_http.requests, "get", fake_get)

    with pytest.raises(RuntimeError, match="pagination"):
        fred.get_series("DFF")


def test_api_error_does_not_leak_key(monkeypatch):
    def fake_get(url, params=None, **kwargs):
        raise requests.ConnectionError(f"{url}?api_key={params['api_key']} failed")

    monkeypatch.setenv("FRED_API_KEY", "sekret-key-value")
    monkeypatch.setattr(_http.requests, "get", fake_get)

    with pytest.raises(RuntimeError) as excinfo:
        fred.get_series("DFF")

    assert "sekret-key-value" not in str(excinfo.value)
    assert "***" in str(excinfo.value)


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="FRED_API_KEY"):
        fred.get_series("DFF")
